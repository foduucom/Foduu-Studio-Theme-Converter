import json
from tqdm import tqdm
from pathlib import Path
from .logger import logger
import re
from .progress import WebSocketManager,push_log

ws_manager = WebSocketManager()
def wrap_try_catch(script: str):


    script = re.sub(
        r"const shortcodeSidebar = params\??\.shortcodeSidebar;",
        """const shortcodeSidebar = params.shortcodeSidebar;

    try {""",
        script
    )


    script = script.replace(
            "</script>",
            """} catch (error) {
    console.log(error instanceof Error ? error.message :JSON.stringify(error, null, 2));
    }
    </script>"""
        )

    return script

def create_shortcode(data,filename):
    param_json = json.dumps(data["param"],
                            indent=4,
                            ensure_ascii=False)
    
    script = wrap_try_catch(data['queryScript']) 

    code = script.replace("params.shortcodeSidebar",
                               f"""
    {{name: '{filename}_{(data['name'])}',
    param: {param_json},
    }}
    """)

    final_shortcode = f"""{code}

    <!-- TEMPLATE START -->

    {data['template']}
    """
    return final_shortcode

def get_unique_filepath(output_dir: Path, name: str) -> Path:
    base_path = output_dir / f"{name}.mustache"

    if not base_path.exists():
        return base_path

    i = 1
    while True:
        new_path = output_dir / f"{name}_{i}.mustache"
        if not new_path.exists():
            return new_path
        i += 1


def save_mustache_files(json_file: str,output_dir:Path):
    json_path = Path(json_file)
    
    if not Path(json_path).exists():
        logger.warning(f"Skipping mustache generation, file missing: {json_path}")
        return
 
    output_dir.mkdir(parents=True, exist_ok=True)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Loading components from: {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        components = json.load(f)

    logger.info(f"\nExporting {len(components)} components...\n")
    push_log(f"Saving {len(components)} components of {json_path.parent.name} file") 
    for comp in tqdm(components, desc="Saving templates", unit="file"):
        if comp is None:
            logger.error("Found None component in JSON, skipping...")
            continue

        if "name" not in comp:
            logger.error(f"Component missing 'name': {comp}")
            continue
        
        name = comp["name"]
        file_path = output_dir / f"{json_path.parent.name}_{name}.mustache"

        # file_path = get_unique_filepath(output_dir, name)
        if file_path.exists():
            continue
        else:
            cleaned = create_shortcode(comp,json_path.parent.name)
            with open(file_path, "w", encoding="utf-8") as out:
                out.write(cleaned)

    logger.info("\nAll templates exported successfully.\n")

    return output_dir

if __name__ == "__main__":
    save_mustache_files("GenerateShortCode/index/shortcodes.json")
