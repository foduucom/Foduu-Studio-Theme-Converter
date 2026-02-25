from bs4 import BeautifulSoup, NavigableString
from pathlib import Path
import os
import json
from bs4 import Comment
from bs4 import Tag


ASSET_FOLDERS = {
    ".css": "assets/css/",
    ".js": "assets/js/",
    ".png": "assets/images/",
    ".jpg": "assets/images/",
    ".jpeg": "assets/images/",
    ".svg": "assets/images/",
    ".webp": "assets/images/",
    ".woff": "assets/fonts/",
    ".woff2": "assets/fonts/",
    ".ttf": "assets/fonts/",
}


def rewrite_html_assets(soup):

    for tag in soup.find_all(["link", "script", "img"]):

        attr = "href" if tag.name == "link" else "src"

        if not tag.get(attr):
            continue

        url = tag[attr].strip()

        
        if url.startswith(("http", "//", "{{")):
            continue

        
        url_path = Path(url)

        if url_path.parts and url_path.parts[0].lower() == "assets":
            tag[attr] = "{{ baseUrl }}/" + url

            continue


        filename = url_path.name
        parent_folder = url_path.parent.name.lower()
        ext = url_path.suffix.lower()

        
        
        
        if parent_folder in ["", ".", "assets"]:

            if ext == ".css":
                tag[attr] = "{{ baseUrl }}/assets/css/" + filename

            elif ext == ".js":
                tag[attr] = "{{ baseUrl }}/assets/js/" + filename

            else:
                tag[attr] = "{{ baseUrl }}/assets/images/" + filename

        
        
        
        else:
            tag[attr] = f"{{{{ baseUrl }}}}/assets/{parent_folder}/{filename}"



def find_main_wrapper(body):
    candidates = body.find_all(["main", "section", "div"], recursive=True)

    candidates = [
        c for c in candidates
        if not c.find("mustache-partial")
    ]

    if not candidates:
        return body

    return max(
        candidates,
        key=lambda tag: len(tag.find_all(True))
    )

def replace_with_content_preserve_partials(wrapper):
    partials = wrapper.find_all("mustache-partial")

    wrapper.clear()

    for p in partials:
        if "header" in p.get_text():
            wrapper.append(p)

    wrapper.append(NavigableString("{{{ content }}}"))

    for p in partials:
        if "footer" in p.get_text():
            wrapper.append(p)

    return wrapper


def remove_all_comments(soup):
    for c in soup.find_all(string=lambda text: isinstance(text, Comment)):
        c.extract()


def remove_empty_divs(soup):
    if not soup.body:
        return

    removed = 0

    while True:
        empty_found = False

        
        divs = soup.body.find_all("div")

        for div in divs:
            if not isinstance(div, Tag):
                continue

            
            if div.attrs:
                continue

            
            has_text = div.get_text(strip=True)
            has_children = div.find(True)

            if not has_text and not has_children:
                div.decompose()
                removed += 1
                empty_found = True

        if not empty_found:
            break

    print("Removed empty divs:", removed)

def build_layout(html_file, output_dir, partial_configs_path,
                 shortcode_configs_path, output_name):
    
    print("building default layout... at:", output_dir)
    html = Path(html_file).read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    output_file = Path(output_dir) / "layouts" / output_name

    os.makedirs(output_file.parent, exist_ok=True)
    with open(partial_configs_path, "r", encoding="utf-8") as f:
        partials = json.load(f)

    with open(shortcode_configs_path, "r", encoding="utf-8") as f:
        shortcodes = json.load(f)



    rewrite_html_assets(soup)
    remove_all_comments(soup)

    print(len(partials), "partials found")
    for config in partials:
        selector = config["selector"]
        name = config["name"]

        element = soup.select_one(selector)
        if not element:
            continue
        
        index_name = f"index_{name}"   

        element.replace_with(
            NavigableString(f"{{{{>{index_name}}}}}")
        )

        print("Partial replaced:", name)

    body = soup.body
    if not body:
        raise ValueError("No <body> tag found")


    removed = 0

    for sc in shortcodes:
        selector = sc["selector"]

        element = soup.select_one(selector)
        if element:
            element.decompose()   
            removed += 1

    print("Removed shortcode HTML blocks:", removed)
    

    remove_empty_divs(soup)

    footer_node = body.find("footer")
    if not footer_node:
        for node in body.descendants:
            if isinstance(node, NavigableString) and "{{>index_footer" in node:
                footer_node = node 
                break


    if footer_node:
        footer_node.insert_before(NavigableString("\n{{{ content }}}\n"))
    else:
        body.append(NavigableString("\n{{{ content }}}\n"))



    output_file.write_text(
        soup.decode(formatter=None),
        encoding="utf-8"
    )

    print("Created:", output_file)
