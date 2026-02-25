from langchain_nvidia_ai_endpoints import ChatNVIDIA
from .track_expense import update_expense_log
from dotenv import load_dotenv
import os
import json
from langchain.messages import SystemMessage, HumanMessage
from langchain_nvidia_ai_endpoints import ChatNVIDIA
import os
from bs4 import BeautifulSoup


load_dotenv()
model_name = os.getenv("MODEL_NAME")

model = ChatNVIDIA(model=model_name,
    max_completion_tokens=31384,
)


def update_navigation_with_ai(original_data, ai_response_string):
    try:
        
        new_navigation = json.loads(ai_response_string)
        
        
        if not isinstance(new_navigation, list):
            raise ValueError("AI response must be a JSON array")
            
        
        updated_data = original_data.copy()
        updated_data["navigation"] = new_navigation
        
        return updated_data
        
    except json.JSONDecodeError as e:
        print(f"Failed to parse AI response: {e}")
        return original_data
    

def generate_navigation(soup):


    with open("prompt/config_prompt.md","r") as f:
        prompt = f.read()
    
    body = soup.find("body")

    
    for script in body.find_all("script"):
        script.decompose()
    messages = [
        SystemMessage(prompt),
        HumanMessage(f"""
    Here is the HTML code:

    ```html
    {body}
    ```
    """)
    ]
    response = model.invoke(messages)
    update_expense_log("config",response.usage_metadata)
    return response.content

def create_config(config_path,html_path):

    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    with open("sample_config.json","r", encoding="utf-8") as f:
        data = json.load(f)

    response = generate_navigation(soup)
    update_data = update_navigation_with_ai(data,response)

    
    with open(config_path,'w') as f:
        json.dump(update_data, f, indent=2, ensure_ascii=False)
    return update_data

if __name__ == "__main__":
    html_path = "ExtractedThemes/gearo_furniture_store_ecommerce/gearo-package/gearo/index.html"
    config_path = "FinalShortcodes/gearo_furniture_store_ecommerce/theme/config.json"
    data = create_config(config_path, html_path)
    print(data)