import json
from typing import Any, Dict, List
from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        if not self.active_connections:
            return

        data = json.dumps(message, ensure_ascii=False)

        disconnected = []

        for ws in self.active_connections:
            try:
                await ws.send_text(data)
            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            self.disconnect(ws)