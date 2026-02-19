from .convert_shortcode import (generate_shortcodes,
                                generate_shortcodes_batch)
from .analyze_html import seperate_html
from .create_mustache import save_mustache_files
from .logger import logger
from .separate_div import extract_components
from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor
from .create_default import build_layout 
import threading
import time
from .track_expense import calculate_total_expense
from .progress import WebSocketManager, push_log

from .helper import (give_full_theme_data,
                     create_output_structure,
                     create_readme,
                     copy_assets,
                     take_homepage_screenshot,
                     save_unique_partials,
                     copy_404_page,
                     zip_output_folder)


ws_manager = WebSocketManager()

def for_now(folder_path):
    # create index.mustache
    index_path = folder_path / "index.mustache"
    index_path.write_text("", encoding="utf-8")

    # create partials/header.mustache
    header_path = folder_path / "partials" / "header.mustache"
    header_path.write_text("", encoding="utf-8")

    # create partials/footer.mustache
    footer_path = folder_path / "partials" / "footer.mustache"
    footer_path.write_text("", encoding="utf-8")


def give_shortcodes(input_path,analyzed_html_path,output_dir,theme_name):
    # Skip anything inside documentation/doc folders
    if any("doc" in p.name.lower() for p in input_path.parents):
        logger.info(f"Skipping HTML inside doc folder: {input_path}")
        return None

    if any("doc" in p.name.lower() for p in analyzed_html_path.parents):
        logger.info(f"Skipping config inside doc folder: {analyzed_html_path}")
        return None

    thread_name = threading.current_thread().name
    thread_id = threading.get_ident()
    push_log(f"Converting: {input_path.name} file")
    logger.info(f"[{thread_name} | ID={thread_id}] Processing: {analyzed_html_path}")

    partials_dir = output_dir / "partials"
    shortcodes_dir = output_dir / "shortcodes"

    partials_dir.mkdir(exist_ok=True)
    shortcodes_dir.mkdir(parents=True, exist_ok=True)

    partials_path,shortcodes_path = extract_components(
            html_file=input_path,
            config_file=analyzed_html_path,
            theme_name=theme_name
        )
    
    # push_log(f"Generating Shortcodes for: {input_path.name} file")
    # generated_shortcode_path = generate_shortcodes(shortcodes_path,theme_name)
    generated_shortcode_path = generate_shortcodes_batch(shortcodes_path,theme_name)

    with open(partials_path, "r", encoding="utf-8") as f:
        partials = json.load(f)
    
    save_unique_partials(partials, partials_dir, input_path.stem)
    save_mustache_files(generated_shortcode_path,shortcodes_dir)
    return output_dir

def run_shortcode_generation(input_path, converted_theme_path, OUTPUT_DIR_NAME):
    futures = []

    with ThreadPoolExecutor(max_workers=4) as executor:
        for path, html_path, unzip_path in seperate_html(input_path):
            futures.append(
                executor.submit(
                    give_shortcodes,
                    html_path,
                    path,
                    converted_theme_path,
                    OUTPUT_DIR_NAME
                )
            )

    for f in futures:
        f.result()

    return unzip_path

import asyncio
async def main(input_path,theme_data):
    theme_data = give_full_theme_data(theme_data)
    start_time = time.time()
    OUTPUT_DIR_NAME = Path(input_path).stem
    OUTPUT_DIR = Path("FinalShortcodes") / OUTPUT_DIR_NAME #/ version
    logger.info(OUTPUT_DIR)
    converted_theme_path = create_output_structure(OUTPUT_DIR)

    create_readme(theme_data,OUTPUT_DIR)
    unzip_path=None
    logger.info("Analyzing HTML files One by one... ")
    unzip_path = await asyncio.to_thread(
        run_shortcode_generation,
        input_path,
        converted_theme_path,
        OUTPUT_DIR_NAME
    )
    if unzip_path and unzip_path.exists():
        html_path = await take_homepage_screenshot(unzip_path, OUTPUT_DIR)
        
        is_assets_exits = copy_assets(html_path.parent, converted_theme_path)
    else:
        await take_homepage_screenshot("", OUTPUT_DIR,html_path=input_path)

    if is_assets_exits:
        logger.info("Assets copied... ")
    else:
        logger.info("Assets not copied. Copying static files manually...")
    
    temp_folder_name = html_path.name.split(".")[0]
    partial_path = f"temp/AnalyzedComponentsJson/{OUTPUT_DIR_NAME}/{temp_folder_name}/partials.json"
    shortcode_path = f"temp/AnalyzedComponentsJson/{OUTPUT_DIR_NAME}/{temp_folder_name}/shortcodes.json"
    # for default.mustache
    build_layout(html_path,converted_theme_path,partial_path,shortcode_path,"default.mustache")
    copy_404_page(converted_theme_path,OUTPUT_DIR_NAME)

    # just for now 
    push_log("Zipping final output...")

    for_now(converted_theme_path)
    final_zip = zip_output_folder(OUTPUT_DIR)

    calculate_total_expense()

    # folder_to_delete = ["GenerateShortCode","SeparatedComponentsJson",
    #                    "AnalyzedComponentsJson",
    #                     "bad_outputs","temp"]
    # for folder in folder_to_delete:
    #     folder_path = Path(folder)

    #     if folder_path.exists() and folder_path.is_dir():
    #         logger.info(f"Deleting folder: {folder_path}")
    #         shutil.rmtree(folder_path, ignore_errors=True)
    # # file to delete

    # file_to_delete = ["expense.json","processed_blocks.json"]

    # for file in file_to_delete:
    #     file_path = Path(file)

    #     if file_path.exists() and file_path.is_file():
    #         logger.info(f"Deleting file: {file_path}")
    #         os.remove(file_path)
            
    elapsed = time.time() - start_time
    minutes = elapsed / 60
    push_log("Conversion complete!")

    logger.info(f"Time taken in generating: {minutes:.2f} minutes")
    return final_zip

if __name__ == "__main__":
    main("THEMES/extech-it-solutions-services.zip")

    logger.info("Finished template-converter...")