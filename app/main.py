from fastapi import FastAPI, UploadFile, File,Form 
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import WebSocket
from pathlib import Path
import shutil,uuid, json
from src.main import main
from src.progress import WebSocketManager, log_queue
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(log_sender())
    yield

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

ws_manager = WebSocketManager()

async def log_sender():
    while True:
        msg = await asyncio.to_thread(log_queue.get)
        await ws_manager.send_log(msg)


@app.get("/",response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate(
    file: UploadFile = File(...),
    theme_name: str = Form(None),
    theme_version: str = "1.0.0",
    theme_category: str = Form(None),
    theme_subcategory: str = Form(None),
    theme_author: str = Form(None),
    theme_author_email: str = Form(None),
    website_type: str = Form(None),
    demo_url: str = Form(None),
  ):
    

    if not file.filename.endswith(".zip"):
        return {"message": "Invalid file format"}
    
    zip_path = Path(f"/tmp/{file.filename}")
    zip_path.parent.mkdir(exist_ok=True)
    with open(zip_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    theme_data = {
    "THEME_NAME": theme_name,
    "VERSION": theme_version,
    "CATEGORY":theme_category,
    "SUBCATEGORY": theme_subcategory,
    "WEBSITE_TYPE": website_type,
    "AUTHOR": theme_author,
    "AUTHOR_EMAIL": theme_author_email,
    "DEMO_URL": demo_url
    }
    output_zip = await main(zip_path, theme_data)
    output_filename = Path(output_zip).name
    return FileResponse(output_zip,
                        media_type="application/zip",
                        filename=output_filename)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)

    try:
        while True:
            await asyncio.sleep(1)
    except:
        pass
    finally:
        await ws_manager.disconnect()