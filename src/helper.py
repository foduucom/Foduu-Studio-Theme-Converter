from pathlib import Path
import shutil
import json
from bs4 import  NavigableString
from playwright.async_api import async_playwright
from .logger import logger
from PIL import Image
import hashlib
import os



from .for_readme import generate_metadata
import re

HOME_PRIORITY = {"index.html", "home.html", "main.html"}


def is_doc_path(path: Path) -> bool:
    return any("doc" in p.name.lower() for p in path.parents)


def find_homepage(unzip_path: Path):
    html_files = []

    for f in unzip_path.rglob("*.html"):
        if any("doc" in parent.name.lower() for parent in f.parents):
            continue
        html_files.append(f)

    if not html_files:
        return None

    for file in html_files:
        if file.name.lower() in HOME_PRIORITY:
            return file

    return max(html_files, key=lambda f: f.stat().st_size)


async def take_homepage_screenshot(unzip_path: Path, output_dir: Path,html_path=None):

    if html_path:
        homepage = Path(html_path)

        if not homepage.exists():
            logger.info(f"Provided HTML file does not exist:{homepage}")
            return

    else:
        homepage = find_homepage(unzip_path)

        if not homepage:
            logger.info("No homepage HTML found.")
            return

    png_path = output_dir / "screenshot.png"
    webp_path = output_dir / "screenshot.webp"

    logger.info(f"Homepage detected:{homepage}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto(homepage.resolve().as_uri())

        await page.wait_for_timeout(3000)

        await page.screenshot(path=str(png_path))

        await browser.close()

    img = Image.open(png_path)
    img.save(webp_path, "webp", quality=85,optimize=True)
    
    png_path.unlink()

    logger.info(f"Screenshot saved: {webp_path}")
    return homepage


def save_unique_partials(partials, partials_dir, source_folder_name):
    registry_file = Path("temp/partials_registry.json")
    os.makedirs("temp", exist_ok=True)

    registry = {}

    
    if registry_file.exists():
        content = registry_file.read_text(encoding="utf-8").strip()
        if content:
            try:
                registry = json.loads(content)
            except json.JSONDecodeError:
                registry = {}

    saved, skipped = 0, 0

    for partial in partials:
        name = partial["name"]   
        html = partial["html"].strip()

        html_hash = hashlib.md5(html.encode("utf-8")).hexdigest()

        if source_folder_name != "index":
            
            if html_hash in registry.values():
                print("Skipping duplicate:", name)
                skipped += 1
                continue

        
        filename = f"{source_folder_name}_{name}.mustache"
        partial_file = partials_dir / filename

        partial_file.write_text(html, encoding="utf-8")

        
        registry[filename] = html_hash

        print("Saved:", filename)
        saved += 1

    registry_file.write_text(
        json.dumps(registry, indent=2),
        encoding="utf-8"
    )

    print(f"Saved: {saved}, Skipped: {skipped}")
from pathlib import Path
import shutil

def copy_assets(theme_path: Path, output_dir: Path):

    assets_out = output_dir / "assets"
    assets_out.mkdir(parents=True, exist_ok=True)

    asset_exts = {
        ".css", ".js",
        ".png", ".jpg", ".jpeg", ".svg", ".webp", ".gif",
        ".woff", ".woff2", ".ttf", ".eot"
    }

    all_assets_path = []

    # ---------------------------------
    # 1️⃣ Copy top-level asset folders
    # ---------------------------------
    for item in theme_path.iterdir():

        if not item.is_dir():
            continue

        if "doc" in item.name.lower():
            continue

        has_assets = any(
            f.suffix.lower() in asset_exts
            for f in item.rglob("*")
            if f.is_file()
        )

        if not has_assets:
            continue

        dest_folder = assets_out / item.name

        shutil.copytree(
            item,
            dest_folder,
            dirs_exist_ok=True
        )

        all_assets_path.append(dest_folder)

    # ---------------------------------
    # 2️⃣ Copy loose root-level files
    # ---------------------------------
    for file in theme_path.iterdir():

        if not file.is_file():
            continue

        ext = file.suffix.lower()

        if ext not in asset_exts:
            continue

        if ext == ".css":
            dest_dir = assets_out / "css"
        elif ext == ".js":
            dest_dir = assets_out / "js"
        else:
            dest_dir = assets_out / "images"

        dest_dir.mkdir(parents=True, exist_ok=True)

        dest = dest_dir / file.name
        shutil.copy2(file, dest)

        all_assets_path.append(dest)

    return True, all_assets_path


def copy_template(sample_path, target_path):
    sample_text = Path(sample_path).read_text(encoding="utf-8")
    Path(target_path).write_text(sample_text, encoding="utf-8")

def create_output_structure(output_dir: Path):
    logger.info("Creating output directory structure...")

   
    
    (output_dir / "documentation").mkdir(parents=True, exist_ok=True)
    (output_dir / "dummy_data").mkdir(parents=True, exist_ok=True)

    
    theme_dir = output_dir / "theme"
    (theme_dir / "assets").mkdir(parents=True, exist_ok=True)
    (theme_dir / "partials").mkdir(parents=True, exist_ok=True)
    (theme_dir / "shortcodes").mkdir(parents=True, exist_ok=True)
    (theme_dir / "layouts").mkdir(parents=True, exist_ok=True)

    

    page_file = theme_dir / "page.mustache"
    sample_page_file = "sample_page.mustache"


    copy_template(sample_page_file, page_file)
    
    return theme_dir

def process_unzip_folder(unzip_path: Path, output_dir: Path):
    create_output_structure(output_dir)

    take_homepage_screenshot(unzip_path, output_dir)

    copy_assets(unzip_path, output_dir)

    logger.info("Done: Screenshot + Assets copied.")


def zip_output_folder(output_dir: Path):
    zip_name = str(output_dir)  
    shutil.make_archive(zip_name, "zip", output_dir)
    logger.info(f"Final ZIP created: {zip_name}.zip")

    return f"{zip_name}.zip"

def copy_404_page(dest_folder,theme_name):
    
    shortcode_json_file = Path(f"temp/AnalyzedComponentsJson/{theme_name}/404/shortcodes.json")
    partial_json_file = Path(f"temp/AnalyzedComponentsJson/{theme_name}/404/partials.json")
    
    if not shortcode_json_file.exists() or not partial_json_file.exists():
        logger.warning("JSON files not found.")
        return
    
    shortcode_data = json.loads(shortcode_json_file.read_text(encoding="utf-8"))
    partial_data = json.loads(partial_json_file.read_text(encoding="utf-8"))

    
    dest_file = Path(dest_folder) / "404.mustache"
    dest_file.parent.mkdir(parents=True, exist_ok=True)

    
    header = """
    {{!-- @layout default --}}

    """

    
    html_blocks = []
    for item in partial_data[:-1]:
        name = item["name"]

        partial_block = NavigableString(f"{{{{>{name}}}}}")

        html_blocks.append(partial_block)

    for item in shortcode_data:
        html = item.get("html")
        if html:
            html_blocks.append(html)

    html_blocks.append(NavigableString(f"{{{{>{partial_data[-1]['name']}}}}}"))
    
    dest_file.write_text(
        header + "\n\n".join(html_blocks),
        encoding="utf-8"
    )

    print(" 404.mustache created:", dest_file)

def create_readme(data:dict,output_dir:Path):

    template_path = Path("sample_README.md")
    output_path = output_dir / "README.md"

    content = template_path.read_text(encoding="utf-8")

    for key, value in data.items():
        content = content.replace(f"{{{{{key}}}}}", str(value))

    output_path.write_text(content, encoding="utf-8")
    print("README.md generated successfully.")

    return output_path


def slugify(name: str) -> str:
    name = name.lower().strip()
    name = re.sub(r"\s+", "-", name)
    name = re.sub(r"[^a-z0-9\-]", "", name)
    return name


def give_full_theme_data(theme_data):
    dtag = generate_metadata(theme_data["THEME_NAME"])

    
    if not dtag:
        dtag = {
            "description": "",
            "tags": []
        }

    
    if not theme_data.get("VERSION"):
        theme_data["VERSION"] = "1.0.0"

    
    theme_data["DESCRIPTION"] = dtag.get("description", "")

    
    tags = dtag.get("tags", [])

    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    theme_data["TAGS"] = ",".join(tags)

    
    theme_data["THEME_SLUG"] = slugify(theme_data["THEME_NAME"]) + "-theme"

    return theme_data


def process_html_path(soup):

    for tag in soup.find_all(["link", "script", "img"]):

        if tag.name == "link":
            attrs = ["href"]
        elif tag.name == "img":
            attrs = ["src", "data-src", "data-original", "data-lazy"]
        else:
            attrs = ["src"]
             
        for attr in attrs:
            if not tag.get(attr):
                continue

            url = tag[attr].strip()

            
            if url.startswith(("http", "//", "{{", "assets/")):
                continue
        
            if url.startswith("/assets/"):
                url = url[1:]
                
            url_path = Path(url)
            ext = url_path.suffix.lower()

            
            if len(url_path.parts) > 1:
                tag[attr] = "assets/" + url.lstrip("/")

            
            else:
                filename = url_path.name

                if ext == ".css":
                    tag[attr] = f"assets/css/{filename}"
                elif ext == ".js":
                    tag[attr] = f"assets/js/{filename}"
                else:
                    tag[attr] = f"assets/images/{filename}"

    return soup

