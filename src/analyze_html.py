import os
import zipfile
import re
from pathlib import Path
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.messages import SystemMessage, HumanMessage
from .logger import logger
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from .track_expense import update_expense_log
import shutil
from .progress import push_log

load_dotenv()

OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER")
EXTRACT_FOLDER = os.getenv("EXTRACT_FOLDER")

use = os.getenv("USE")
model_name = os.getenv("MODEL_NAME")
if use == "GEMINI":
    model = init_chat_model(
        model_name,
        max_tokens=31384,
    )
else:
    model = ChatNVIDIA(model=model_name,
                        temperature=0.5,
                        max_completion_tokens=31384,
    )   
with open("prompt/seperation.md", "r", encoding="utf-8") as f:
    prompt = f.read()


def extract_zip(zip_path, extract_to):
    logger.info(f"Extracting ZIP: {zip_path}")
    push_log(f"Extracting ZIP: {zip_path}")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)

    macosx_folder = Path(extract_to) / "__MACOSX"
    if macosx_folder.exists():
        shutil.rmtree(macosx_folder)
        logger.info("Removed __MACOSX folder")

    logger.info("Extraction complete.\n")



def clean_html(html_path):
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    body = soup.find("body")
    if not body:
        return None

    for script in body.find_all("script"):
        script.decompose()

    return body.prettify()

def html_to_json(html_code,html_path=None,retries=3):
    messages = [
        SystemMessage(prompt),
        HumanMessage(f"""
    Here is the HTML code:

    ```html
    {html_code}
    ```
    """)
    ]
    for attempt in range(1, retries + 1):
        try:
            response = model.invoke(messages)

            usage = getattr(response, "usage_metadata", None)
            if usage:
                logger.info(f"Token Usage in analyzing HTML: {usage}")
                update_expense_log(str(html_path), usage)

            if response is None or not response.content:
                raise ValueError("Empty response from model")

            clean = re.sub(r"```json|```", "", response.content).strip()
            return clean

        except Exception as e:
            logger.error(f"Attempt {attempt}/{retries} failed: {e}")
            time.sleep(1)

    response = model.invoke(messages) 
    clean = re.sub(r"```json|```", "", response.content).strip()
    return clean


def process_html_file(html_path, project_name=None, extract_folder=None):
    """Process a single HTML file → JSON output"""

    output_dir = Path(OUTPUT_FOLDER) / project_name
    output_dir.mkdir(parents=True, exist_ok=True)

    if extract_folder:
        rel_path = html_path.relative_to(extract_folder)
        safe_name = str(rel_path).replace("/", "_").replace("\\", "_")
        filename = safe_name.replace(".html", ".json")
    else:
        filename = html_path.stem + ".json"

    output_path = output_dir / filename

    if output_path.exists():
        logger.info(f"Skipping (already exists): {output_path}")
        return output_path

    html_code = clean_html(html_path)

    if not html_code:
        logger.warning(f"No <body> found in {html_path}, skipping...")
        return None

    push_log(f"Analyzing HTML {html_path.stem}...")
    json_output = html_to_json(html_code, html_path)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json_output)

    logger.info(f"Saved: {output_path}")
    return output_path


def process_zip_file(zip_path):
    """Extract ZIP and process all HTML files"""

    extract_folder = Path(EXTRACT_FOLDER) / zip_path.stem
    extract_zip(zip_path, extract_folder)

    seen = set()
    logger.info("Processing HTML files...")
    for root, _, files in os.walk(extract_folder):

        if "__MACOSX" in root:
            continue

        for file in files:
            if file.endswith(".html"):
                if file != "index.html":
                    continue
                
                full_path = Path(root) / file

                rel_path = full_path.relative_to(extract_folder)

                if rel_path in seen:
                    logger.warning(f"Duplicate file found: {rel_path}")
                    continue
                
                if "404.html" in str(rel_path):
                    logger.warning(f"Skipping 404.html file: {rel_path}")
                    continue

                seen.add(rel_path)

                output_path = process_html_file(
                    full_path,
                    project_name=zip_path.stem,
                    extract_folder=extract_folder
                )

                if output_path:
                    yield output_path,full_path,extract_folder
          

def seperate_html(file_path):
    """
    User gives either:
    - ZIP file → extract + process all HTML
    - HTML file → process directly
    """
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    file_path = Path(file_path)

    if not file_path.exists():
        logger.warning("File not found.")
        return

    
    if file_path.suffix == ".zip":
        yield from process_zip_file(file_path)

    elif file_path.suffix == ".html":
        output_path = process_html_file(file_path,file_path.stem)
        yield output_path
    else:
        logger.warning("Unsupported file type. Only .zip or .html allowed.")
        return 

if __name__ == "__main__":
    seperate_html("index.html")