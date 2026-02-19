
progress_store = {}
result_store = {}
import queue

log_queue = queue.Queue()

def push_log(msg: str):
    log_queue.put(msg)

from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        self.ws_client: WebSocket | None = None


    async def connect(self,websocket: WebSocket):
        await websocket.accept()          # REQUIRED

        self.ws_client = websocket


    async def disconnect(self):
        self.ws_client = None


    async def send_log(self,message: str):
        if self.ws_client:
            await self.ws_client.send_text(message)
