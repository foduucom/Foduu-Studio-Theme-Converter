from pathlib import Path
import json
from threading import Lock
from .logger import logger
import os
expense_lock = Lock()



def update_expense_log(component_name: str, usage: dict):
    with expense_lock:
        expense_file = os.getenv("EXPENSE_FILE")
        os.makedirs("temp", exist_ok=True)
        expense_data = {}

        if expense_file.exists():
            try:
                content = expense_file.read_text(encoding="utf-8").strip()
                if content:
                    expense_data = json.loads(content)
            except json.JSONDecodeError:
                logger.warning("expense.json corrupted. Resetting...")
                expense_data = {}

        expense_data[component_name] = {
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }

        tmp_file = expense_file.with_suffix(".tmp")
        tmp_file.write_text(
            json.dumps(expense_data, indent=2),
            encoding="utf-8"
        )
        tmp_file.replace(expense_file)

        logger.info(f"Token expense updated: {component_name}")


def calculate_total_expense():
    expense_file = Path("temp/expense.json")

    if not expense_file.exists():
        logger.warning("expense.json not found.")
        return

    with open(expense_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_input = 0
    total_output = 0
    total_tokens = 0

    for file, usage in data.items():
        total_input += usage.get("input_tokens", 0)
        total_output += usage.get("output_tokens", 0)
        total_tokens += usage.get("total_tokens", 0)

    input_cost = ((total_input / 1000000) * 0.15) * 90.56
    output_cost = ((total_output / 1000000) * 1.50) * 90.56
    
    total_cost = input_cost + output_cost
    logger.info("====== TOKEN EXPENSE SUMMARY ======")
    logger.info(f"Total Input Tokens : {total_input}")
    logger.info(f"Total Output Tokens: {total_output}")
    logger.info(f"Total Tokens       : {total_tokens}")
    logger.info(f"Total Input Cost   : {input_cost:.2f}")
    logger.info(f"Total Output Cost  : {output_cost:.2f}")
    logger.info(f"Total Cost         : {total_cost:.2f}")
    logger.info("===================================")

    return {
        "input_tokens": total_input,
        "output_tokens": total_output,
        "total_tokens": total_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost
    }
