from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.core.logging import setup_logger
from app.ml.predictor import ASATGNNDemoPredictor
from app.store.memory_store import MemoryEventStore
from app.websocket.manager import WebSocketManager

logger = setup_logger()

app = FastAPI(
    title="ASAT GNN IDS Demo Backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 80)
    logger.info("Starting ASAT GNN IDS Demo Backend")
    logger.info("ARTIFACT_DIR=%s", settings.artifact_dir)
    logger.info("DEVICE=%s", settings.device)
    logger.info("ONLINE_K=%s", settings.online_k)
    logger.info("=" * 80)

    app.state.settings = settings
    app.state.store = MemoryEventStore(max_events=settings.max_events_in_memory)
    app.state.ws_manager = WebSocketManager()

    app.state.predictor = ASATGNNDemoPredictor(
        artifact_dir=settings.artifact_dir,
        device=settings.device,
        online_k=settings.online_k,
    )

    logger.info("Predictor loaded successfully.")


@app.get("/")
async def root():
    return {
        "service": "ASAT GNN IDS Demo Backend",
        "health": "/api/health",
        "events": "/api/events",
        "websocket": "/ws/events",
    }


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    manager: WebSocketManager = app.state.ws_manager

    await manager.connect(websocket)

    try:
        await websocket.send_json(
            {
                "type": "connected",
                "message": "Connected to ASAT GNN IDS backend.",
                "stats": app.state.store.stats(),
            }
        )

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)

    except Exception:
        manager.disconnect(websocket)