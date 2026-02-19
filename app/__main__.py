

from app.main import app


import uvicorn

uvicorn.run(app, host="localhost",
             port=8000, log_level="info")
