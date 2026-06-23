import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Settings:
    app_host: str
    app_port: int
    artifact_dir: str
    device: str
    online_k: int
    max_events_in_memory: int
    cors_origins: list[str]


def load_settings() -> Settings:
    load_dotenv()

    cors_raw = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080",
    )

    return Settings(
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        artifact_dir=os.getenv(
            "ARTIFACT_DIR",
            "./artifacts/hierarchical_asat_gnn_demo_minimal_artifacts",
        ),
        device=os.getenv("DEVICE", "cpu"),
        online_k=int(os.getenv("ONLINE_K", "8")),
        max_events_in_memory=int(os.getenv("MAX_EVENTS_IN_MEMORY", "5000")),
        cors_origins=[x.strip() for x in cors_raw.split(",") if x.strip()],
    )


settings = load_settings()