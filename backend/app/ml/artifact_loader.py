import json
import os
from typing import Any, Dict, List, Optional

import faiss
import joblib
import numpy as np


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class DemoArtifacts:
    def __init__(self, artifact_dir: str):
        self.artifact_dir = artifact_dir

        self.preprocess_dir = os.path.join(artifact_dir, "01_preprocess")
        self.encoder_dir = os.path.join(artifact_dir, "02_encoder")
        self.gnn_dir = os.path.join(artifact_dir, "03_gnn_model")
        self.graph_dir = os.path.join(artifact_dir, "04_graph_bank")
        self.metadata_dir = os.path.join(artifact_dir, "05_metadata")
        self.threshold_dir = os.path.join(artifact_dir, "06_thresholds_and_rescue")

        self.preprocess_config = load_json(
            os.path.join(self.preprocess_dir, "preprocess_config.json")
        )

        self.encoder_metadata = load_json(
            os.path.join(self.encoder_dir, "encoder_metadata.json")
        )

        self.gnn_config = load_json(
            os.path.join(self.gnn_dir, "gnn_model_config.json")
        )

        self.graph_bank_config = load_json(
            os.path.join(self.graph_dir, "graph_bank_config.json")
        )

        self.class_metadata = load_json(
            os.path.join(self.metadata_dir, "class_metadata.json")
        )

        self.threshold_config = load_json(
            os.path.join(self.threshold_dir, "threshold_and_rescue_config.json")
        )

        # self.class_names: List[str] = self.class_metadata["class_names"]
        # self.benign_id: int = int(self.class_metadata["benign_id"])
        # self.attack_class_ids: List[int] = [
        #     int(x) for x in self.class_metadata["attack_class_ids"]
        # ]

        self.attack_threshold: float = float(self.threshold_config["attack_threshold"])

        self.selected_features = self._load_selected_features()
        self.original_feature_columns = self._load_original_feature_columns()

        self.scaler = joblib.load(
            os.path.join(self.preprocess_dir, "feature_scaler_standardscaler.pkl")
        )

        self.label_encoder = joblib.load(
            os.path.join(self.preprocess_dir, "label_encoder.pkl")
        )

        # ============================================================
        # CRITICAL: use LabelEncoder order as the source of truth.
        # This prevents wrong dashboard labels when class_metadata.json
        # is saved in a different order from model class IDs.
        # ============================================================
        label_encoder_classes = [str(x) for x in list(self.label_encoder.classes_)]

        if len(label_encoder_classes) != int(self.class_metadata["num_classes"]):
            raise ValueError(
                "LabelEncoder class count does not match class_metadata num_classes: "
                f"{len(label_encoder_classes)} != {self.class_metadata['num_classes']}"
            )

        self.class_names = label_encoder_classes

        if "BenignTraffic" not in self.class_names:
            raise ValueError("BenignTraffic not found in LabelEncoder classes.")

        self.benign_id = int(self.class_names.index("BenignTraffic"))

        self.attack_class_ids = [
            i for i, name in enumerate(self.class_names)
            if i != self.benign_id
        ]

        print("=" * 80)
        print("Loaded class mapping from label_encoder.pkl")
        print("NUM_CLASSES =", len(self.class_names))
        print("BENIGN_ID =", self.benign_id)
        for i, name in enumerate(self.class_names):
            print(f"{i:02d} -> {name}")
        print("ATTACK_CLASS_IDS =", self.attack_class_ids)
        print("=" * 80)

        self.selected_idx: Optional[np.ndarray] = None
        selected_idx_path = os.path.join(
            self.preprocess_dir,
            "selected_idx_from_original_features.npy",
        )

        if os.path.exists(selected_idx_path):
            self.selected_idx = np.load(selected_idx_path).astype(np.int64)

        self.reference_embeddings = np.load(
            os.path.join(self.graph_dir, "reference_train_embeddings.npy")
        ).astype(np.float32)

        self.reference_labels = np.load(
            os.path.join(self.graph_dir, "reference_train_labels.npy")
        ).astype(np.int64)

        index_path = os.path.join(
            self.graph_dir,
            "reference_train_faiss_cosine.index",
        )

        if not os.path.exists(index_path):
            raise FileNotFoundError(f"FAISS index not found: {index_path}")

        self.faiss_index = faiss.read_index(index_path)

    def _load_selected_features(self) -> List[str]:
        path = os.path.join(self.preprocess_dir, "selected_features.json")
        return [str(x) for x in load_json(path)]

    def _load_original_feature_columns(self) -> List[str]:
        path = os.path.join(self.preprocess_dir, "original_feature_columns.json")
        if os.path.exists(path):
            return [str(x) for x in load_json(path)]
        return []

    def search_neighbors(self, z: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
        z = np.asarray(z, dtype=np.float32).copy()
        faiss.normalize_L2(z)
        scores, indices = self.faiss_index.search(z, int(k))
        return scores.astype(np.float32), indices.astype(np.int64)