from fastapi import APIRouter, Request
from app.schemas import AgentFlowPayload

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    settings = request.app.state.settings

    return {
        "status": "ok",
        "model_loaded": request.app.state.predictor is not None,
        "artifact_dir": settings.artifact_dir,
        "device": settings.device,
    }


@router.get("/events")
async def list_events(request: Request, limit: int = 200):
    return {
        "events": request.app.state.store.list_events(limit=limit),
        "stats": request.app.state.store.stats(),
    }


@router.get("/stats")
async def stats(request: Request):
    return request.app.state.store.stats()


@router.post("/agent/flows")
async def receive_agent_flows(payload: AgentFlowPayload, request: Request):
    predictor = request.app.state.predictor
    store = request.app.state.store
    manager = request.app.state.ws_manager

    flow_dicts = [f.model_dump() for f in payload.flows]

    predictions = predictor.predict_flows(flow_dicts)

    saved_events = []

    for pred in predictions:
        event = {
            **pred,
            "agent_id": payload.agent_id,
        }

        event = store.add_event(event)
        saved_events.append(event)

        await manager.broadcast(
            {
                "type": "prediction",
                "event": event,
                "stats": store.stats(),
            }
        )

    return {
        "status": "ok",
        "received_flows": len(payload.flows),
        "predicted_flows": len(saved_events),
        "stats": store.stats(),
    }