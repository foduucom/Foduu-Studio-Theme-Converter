import json
from bs4 import BeautifulSoup
from tqdm import tqdm
from pathlib import Path
from .logger import logger
from .progress import push_log

OUTPUT_DIR = "temp/AnalyzedComponentsJson"


def clean_html(soup):
    """Remove scripts/styles from HTML"""
    for tag in soup.find_all(["script", "style"]):
        tag.decompose()
    return soup


def extract_components(html_file: str, config_file: str,theme_name: str):
    """
    Extract HTML components based on selectors config.

    Args:
        html_file (str): Path to input HTML file
        config_file (str): Path to JSON config file
        outdir (str): Output folder

    Returns:
        dict: { "partials": [...], "shortcodes": [...] }
    """

    html_path = Path(html_file)
    config_path = Path(config_file)
    # outdir_path = Path(OUTPUT_DIR) / Path(html_file).stem
    outdir_path = Path(f"{OUTPUT_DIR}/{theme_name}/{Path(html_file).stem}")
    outdir_path.mkdir(parents=True, exist_ok=True)

    # ---- Validate files ----
    if not html_path.exists():
        logger.warning(f"HTML file not found: {html_path}")
        return None

    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}")
        return None

    # ---- Load config ----
    with open(config_path, "r", encoding="utf-8") as f:
        configs = json.load(f)

    # ---- Load HTML ----
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    soup = clean_html(soup)

    partials = []
    shortcodes = []
        
    logger.info(f"Total selectors in config: {len(configs)}")
    push_log(f"Extracting components from: {html_path.name} file")
    # ---- Extract Components ----
    for config in tqdm(configs, desc="Extracting components", unit="component"):

        selector = config["selector"]
        section_type = config.get("type", "shortcode")
        name = config.get("name", "component")

        element = soup.select_one(selector)

        if not element:
            tqdm.write(f"Not found: {selector}")
            continue

        component_data = {
            "name": name,
            "type": section_type,
            "selector": selector,
            "html": str(element)
        }

        if section_type == "partial":
            partials.append(component_data)
        else:
            shortcodes.append(component_data)

    
    partial_file = outdir_path / "partials.json"
    shortcode_file = outdir_path / "shortcodes.json"

    with open(partial_file, "w", encoding="utf-8") as f:
        json.dump(partials, f, indent=2, ensure_ascii=False)

    with open(shortcode_file, "w", encoding="utf-8") as f:
        json.dump(shortcodes, f, indent=2, ensure_ascii=False)

    logger.info("Extraction Complete")
    logger.info(f"Partials extracted: {len(partials)} → {partial_file}")
    logger.info(f"Shortcodes extracted: {len(shortcodes)} → {shortcode_file}")

    return  (partial_file, shortcode_file)
if __name__ == "__main__":
    extract_components(
        html_file="index.html",
        config_file="SeparatedComponentsJson/index.json")