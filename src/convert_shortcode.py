import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage
from .logger import logger
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from .track_expense import update_expense_log
from .save_shortcode import (
    is_already_processed,
    mark_as_processed,
    skeleton_hash
)
from src.schema import ShortcodeSchema

from langchain_community.callbacks import get_openai_callback

model_name = os.getenv("MODEL_NAME")
batch_size=5
model = ChatNVIDIA(model=model_name,
    max_completion_tokens=31384,
    temperature=0.4,
    top_p=0.95,

)
structured_model = model.with_structured_output(ShortcodeSchema)

def clean_llm_json(response_text: str):
    cleaned = re.sub(r"```json|```", "", response_text).strip()
    return json.loads(cleaned)

import time
from .progress import push_log

def invoke_with_retry(model, messages, key, retries=5):
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            with get_openai_callback() as cb:
                response = model.invoke(messages)

            logger.info(f"Input tokens: {cb.prompt_tokens}")
            logger.info(f"Output tokens: {cb.completion_tokens}")
            logger.info(f"Total tokens: {cb.total_tokens}")

            usage = {
                "input_tokens": cb.prompt_tokens,
                "output_tokens": cb.completion_tokens,
                "total_tokens": cb.total_tokens
            }

            logger.info(f"Token Usage: {usage}")
            update_expense_log(key, usage)


            if response is None:
                raise ValueError("LLM returned None")


            cleaned = response.model_dump()
            return cleaned

        except Exception as e:
            last_error = e
            logger.error(f"Attempt {attempt}/{retries} failed for {key}: {e}")


            try:
                Path("temp/bad_outputs").mkdir(exist_ok=True)
                Path(f"temp/bad_outputs/error_attempt_{attempt}.txt").write_text(
                    str(response) if "response" in locals() else str(e),
                    encoding="utf-8"
                )
            except:
                pass

            time.sleep(5)


    raise last_error


def batch_invoke_with_retry(model, messages, keys, retries=5,batch_name=""):
    results = [None] * len(messages)
    pending = list(range(len(messages)))

    for attempt in range(1, retries + 1):
        if not pending:
            break

        logger.info(f"Batch attempt {attempt}/{retries} → {len(pending)} left")

        try:
            pending_inputs = [messages[i] for i in pending]
            pending_keys = [keys[i] for i in pending]

            with get_openai_callback() as cb:
                responses = model.batch(pending_inputs)


            usage = {
                "input_tokens": cb.prompt_tokens,
                "output_tokens": cb.completion_tokens,
                "total_tokens": cb.total_tokens,
            }

            logger.info(f"Batch Token Usage: {usage}")


            update_expense_log(batch_name, usage)

            for idx, key, resp in zip(pending, pending_keys, responses):
                
                try:
                    if resp is None:
                        raise ValueError("LLM returned None")
                    
                    results[idx] = resp.model_dump()

                except Exception as e:
                    logger.error(
            f"Batch attempt {attempt}/{retries} failed for {key}: {e}")
                    Path("temp/bad_outputs").mkdir(exist_ok=True)
                    (
                    Path(f"temp/bad_outputs/{key}_attempt_{attempt}.txt")
                    .write_text(
                        str(resp),
                        encoding="utf-8"
                    ))
            pending = [i for i in range(len(messages)) if results[i] is None]
        except Exception as e:
            logger.error(f"Batch attempt {attempt}/{retries} failed: {e}")
            time.sleep(5+(attempt*2))   
        
    failed = [keys[i] for i,r in enumerate(results) if r is None]
    if failed :
        raise RuntimeError(f"Batch failed completely: {failed}")
    
    return results

def generate_shortcodes_batch(input_json_file: str,theme_name: str):
    with open("prompt/shortcode-creation.md", "r", encoding="utf-8") as f:
        shortcode_prompt = f.read()

    system_msg = SystemMessage(shortcode_prompt)

    input_path = Path(input_json_file)

    with open(input_path, "r", encoding="utf-8") as f:
        shortcodes = json.load(f)

    
    folder_name =  input_path.parent.name

    output_dir =  Path(f"{os.getenv('GENERATE_FOLDER')}/{theme_name}/{folder_name}")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "shortcodes.json"
    
    logger.info(f"Loaded shortcodes type: {type(shortcodes)}")


    final_output = []
    already_done = set()

    if output_file.exists():
        with open(output_file, "r", encoding="utf-8") as f:
            final_output = json.load(f)
        already_done = {c["name"] for c in final_output}
        logger.info(f"Resuming: {len(final_output)} already done")
    
    seen_html = set()
    batch = []
    batch_inputs = []
    batch_keys=[]

    push_log(f"Generating shortcodes for {input_path.parent.name}")
    logger.info("Starting batch shortcode generation...\n")
    batch_no = 1
    for component_dict in shortcodes:
        key = component_dict["name"]
        html = component_dict["html"]

        if key in already_done:
            continue

        exits,match,score = is_already_processed(html)
        if exits:
            logger.info(
            f"Skipping {key}[Already Processed:{match['name']}]: {score}"
            )
            continue

        hash_html = skeleton_hash(html)
        if hash_html in seen_html:
            logger.info(f"Skipping {key}[Duplicate]")
            continue

        seen_html.add(hash_html)


        message = [
            system_msg,
            HumanMessage(
                f"""
                Component Key: {key}

                Component Data:
                {json.dumps(component_dict, indent=2)}
                """
            )
        ]

        batch.append(component_dict)
        batch_inputs.append(message)
        batch_keys.append(key)
        
        if len(batch) == batch_size:
            batch_results = batch_invoke_with_retry(
                structured_model,
                batch_inputs,
                batch_keys,
                retries=5,
                batch_name=f"{folder_name}_batch_{batch_no}"
            )
            logger.info(f"Got response batch: {len(batch_results)}/{len(batch)}")

            for comp,cleaned in zip(batch,batch_results):
                key = comp["name"]
                html = comp["html"]

                final_output.append(cleaned)
                mark_as_processed(key,html,cleaned)
                already_done.add(key)
                with open(output_file,'w',encoding="utf-8") as f:
                    json.dump(final_output,f,indent=2,ensure_ascii=False)

                logger.info(f"Saved: {key}")

            batch = []
            batch_inputs = []
            batch_keys=[]
            batch_no += 1   
        
    if batch:
        logger.info(f"Processing leftovers: {len(batch)}")
        batch_results = batch_invoke_with_retry(
            structured_model,
            batch_inputs,
            batch_keys,
            retries=5,
            batch_name=f"{folder_name}_batch_{batch_no}"
        )

        for comp, cleaned in zip(batch, batch_results):

            key = comp["name"]
            html = comp["html"]

            final_output.append(cleaned)
            mark_as_processed(key,html,cleaned)
            already_done.add(key)
            with open(output_file, 'w', encoding="utf-8") as f:
                json.dump(final_output, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved: {key}")

    logger.info(f"\nAll done. Output saved at: {output_file}")
    return output_file









def generate_shortcodes(input_json_file: str,theme_name: str):

    with open("prompt/shortcode-creation.md", "r", encoding="utf-8") as f:
        shortcode_prompt = f.read()

    input_path = Path(input_json_file)
    logger.info(f"Input file: {input_path}")
    with open(input_path, "r", encoding="utf-8") as f:
        shortcodes = json.load(f)

    folder_name = input_path.parent.name

    output_dir = Path(f"temp/GenerateShortCode/{theme_name}") / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "shortcodes.json"
    
    logger.info(f"Loaded shortcodes type: {type(shortcodes)}")



    if output_file.exists():
        with open(output_file, "r", encoding="utf-8") as f:
            final_output = json.load(f)
        logger.info(f"Resuming from existing file: {len(final_output)} items loaded")
    else:
        final_output = []
    system_msg = SystemMessage(shortcode_prompt)
    if len(final_output) > 0:
        already_done = {item["name"] for item in final_output}
    else:
        already_done = set()


    logger.info("Generating shortcodes one by one...")
    for component_dict in shortcodes:
        key = component_dict["name"]
        html = component_dict["html"]
        
        if key in already_done:
            logger.info(f"Skipping already processed: {key}")
            continue
        exists, match, score = is_already_processed(html)

        if exists:
            logger.info(
                f"Skipping {key} (already processed: {match['name']}, similarity={score}%)"
            )
            continue
                    

        logger.info(f"Processing component: {key}")
        messages = [
            system_msg,
            HumanMessage(
                f"""
                Component Key: {key}

                Component Data:
                {json.dumps(component_dict, indent=2)}

               
                """
            )
        ]
        logger.info("Calling model.invoke...")

       
        cleaned = invoke_with_retry(structured_model, messages,key, retries=5)

        final_output.append(cleaned)    
        mark_as_processed(key, html,cleaned)

        with open(output_file, "w", encoding="utf-8") as f:
                json.dump(final_output, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Saved output for: {key}")

    logger.info(f"Output saved at: {output_file}")
    return output_file

if __name__ == "__main__":
    generate_shortcodes("AnalyzedComponentsJson/index/shortcodes.json")
