from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FlowInput(BaseModel):
    flow_key: Dict[str, Any] = Field(default_factory=dict)
    packet_count: int = 0
    window_start_ts: float = 0.0
    window_end_ts: float = 0.0
    features_order: List[str]
    features: List[float]
    features_dict: Optional[Dict[str, float]] = None


class AgentFlowPayload(BaseModel):
    agent_id: str
    sent_at: float
    num_flows: int
    flows: List[FlowInput]


class PredictionOutput(BaseModel):
    event_id: int
    agent_id: str
    received_at: float

    # Main dashboard fields
    attack_type: str
    source_ip: str
    source_port: int
    destination_ip: str
    destination_port: int
    protocol: str
    total_packets: int
    packets_per_second: float
    bytes_per_second: float

    # Model fields
    class_id: int
    class_name: str
    is_attack: bool
    confidence: float
    attack_probability: float
    subtype_confidence: Optional[float] = None

    # Raw flow metadata
    flow_key: Dict[str, Any]
    packet_count: int
    window_start_ts: float
    window_end_ts: float

    features_order: List[str]
    features: List[float]


class HealthOutput(BaseModel):
    status: str
    model_loaded: bool
    artifact_dir: str
    device: str