
from pathlib import Path
import json
import re
import hashlib
from bs4 import BeautifulSoup
from rapidfuzz.fuzz import ratio


DB_FILE = Path("temp/processed_blocks.json")

def html_skeleton(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()

    for tag in soup.find_all():
        if tag.string:
            tag.string.replace_with("")

    for tag in soup.find_all():
        for attr in ["id", "style", "data-id"]:
            if attr in tag.attrs:
                del tag.attrs[attr]

    skeleton = str(soup)
    skeleton = re.sub(r"\s+", " ", skeleton).strip()

    return skeleton


def skeleton_hash(html: str) -> str:
    skel = html_skeleton(html)
    return hashlib.sha256(skel.encode()).hexdigest()

def load_db():
    if not DB_FILE.exists():
        DB_FILE.write_text("[]", encoding="utf-8")

        return []

    try:
        content = DB_FILE.read_text(encoding="utf-8").strip()

        # Handle empty file case
        if not content:
            DB_FILE.write_text("[]", encoding="utf-8")
            return []

        return json.loads(content)

    except json.JSONDecodeError:
        # Reset corrupted DB
        DB_FILE.write_text("[]", encoding="utf-8")
        return []

def save_db(data):
    DB_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

def mark_as_processed(name: str, html: str,shortcode_data: dict):
    db = load_db()

    skel = html_skeleton(html)
    h = skeleton_hash(html)

    db.append({
        "name": name,
        "hash": h,
        "skeleton": skel,
        "shortcode": shortcode_data  
    })

    save_db(db)

from rapidfuzz.fuzz import ratio

def is_already_processed(new_html: str, threshold=95):
    db = load_db()

    new_skel = html_skeleton(new_html)
    new_hash = skeleton_hash(new_html)

    for item in db:
        if item["hash"] == new_hash:
            return True, item, 100

        score = ratio(new_skel, item["skeleton"])
        if score >= threshold:
            return True, item, score

    return False, None, None

