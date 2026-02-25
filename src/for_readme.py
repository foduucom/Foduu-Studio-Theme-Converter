from langchain.messages import SystemMessage, HumanMessage
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from .track_expense import update_expense_log
import os
from langchain_community.callbacks import get_openai_callback
from .schema import ReadmeMetadata
from .logger import logger
from .progress import push_log
load_dotenv()
model_name = os.getenv("MODEL_NAME")

model = ChatNVIDIA(model=model_name,
    max_completion_tokens=31384,
)
structured_model = model.with_structured_output(ReadmeMetadata)

with open("prompt/readme_metadata.md","r") as f:
    system_prompt = f.read()

def generate_metadata(theme_name:str):
    logger.info(f"Generating metadata for theme: {theme_name}")
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=theme_name),
    ]
    
    push_log(f"Generating metadata for theme: {theme_name}")

    with get_openai_callback() as cb:
        response = structured_model.invoke(messages)
    
    usage = {
                "input_tokens": cb.prompt_tokens,
                "output_tokens": cb.completion_tokens,
                "total_tokens": cb.total_tokens
            }


    update_expense_log("readme", usage)
    push_log(f"Generated metadata for theme: {theme_name}")
    if response :
        cleaned = response.model_dump()
        return cleaned


if __name__ == "__main__":
    print(generate_metadata("Extech IT Solutions Services"))
        