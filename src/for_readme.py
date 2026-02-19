from langchain.messages import SystemMessage, HumanMessage
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from .track_expense import update_expense_log
import os
from langchain_community.callbacks import get_openai_callback
from .schema import ReadmeMetadata

load_dotenv()
model_name = os.getenv("MODEL_NAME")

model = ChatNVIDIA(model=model_name,
    max_completion_tokens=31384,
)
structured_model = model.with_structured_output(ReadmeMetadata)

system_prompt = """
You will receive only a theme name.

Return JSON exactly like:

{
  "description": "...",
  "tags": ["tag1", "tag2", "tag3"]
}


Rules:
- Description must be max 50 words.
- Mention “Foduu Studio” naturally.
- Do NOT say Foduu Studio created/designed it.
- Do NOT mention “HTML theme” or “template”.
- Do NOT include the theme name.
- Tags must be 4–8 short lowercase keywords, comma-separated.
- Tags should match the niche and style (e.g., responsive, modern, contractor, portfolio).
- Output ONLY valid JSON, nothing else.
"""

def generate_metadata(theme_name:str):
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=theme_name),
    ]

    with get_openai_callback() as cb:
        response = structured_model.invoke(messages)
    
    usage = {
                "input_tokens": cb.prompt_tokens,
                "output_tokens": cb.completion_tokens,
                "total_tokens": cb.total_tokens
            }


    update_expense_log("readme", usage)
    print(response)
    if response :
        cleaned = response.model_dump()
        return cleaned


if __name__ == "__main__":
    print(generate_metadata("Extech IT Solutions Services"))
        