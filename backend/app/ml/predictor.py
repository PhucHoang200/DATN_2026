import os
import time
from typing import Any, Dict, List, Tuple

import numpy as np
import torch

from app.ml.artifact_loader import DemoArtifacts
from app.ml.graph.online_graph_builder import build_online_subgraph
from app.ml.models.encoder import EncoderClassifier
from app.ml.models.asat_gnn import HierarchicalASATAttentionGraphSAGE


EXPECTED_CLASS_NAMES_22 = [
    "BenignTraffic",
    "DDoS-ACK_Fragmentation",
    "DDoS-HTTP_Flood",
    "DDoS-ICMP_Flood",
    "DDoS-ICMP_Fragmentation",
    "DDoS-PSHACK_Flood",
    "DDoS-RSTFINFlood",
    "DDoS-SYN_Flood",
    "DDoS-SynonymousIP_Flood",
    "DDoS-TCP_Flood",
    "DDoS-UDP_Flood",
    "DDoS-UDP_Fragmentation",
    "DoS-HTTP_Flood",
    "DoS-SYN_Flood",
    "DoS-TCP_Flood",
    "DoS-UDP_Flood",
    "MITM-ArpSpoofing",
    "Mirai-greeth_flood",
    "Mirai-greip_flood",
    "Mirai-udpplain",
    "Recon-HostDiscovery",
    "VulnerabilityScan",
]


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def get_main_attack_group(class_name: str) -> str:
    class_name = str(class_name)

    if class_name == "BenignTraffic":
        return "Benign"

    if class_name.startswith("DDoS-"):
        return "DDoS"

    if class_name.startswith("DoS-"):
        return "DoS"

    if class_name.startswith("Recon-") or class_name == "VulnerabilityScan":
        return "Recon"

    if class_name in {"MITM-ArpSpoofing", "DNS_Spoofing"}:
        return "Spoofing"

    if class_name.startswith("Mirai-"):
        return "Mirai"

    if class_name in {
        "SqlInjection",
        "CommandInjection",
        "Backdoor_Malware",
        "Uploading_Attack",
        "XSS",
        "BrowserHijacking",
    }:
        return "Web-Based"

    if class_name == "DictionaryBruteForce":
        return "Brute Force"

    return "Unknown"


def get_flow_key(flow: Dict[str, Any]) -> Dict[str, Any]:
    return flow.get("flow_key", {}) or {}


def get_flow_protocol(flow: Dict[str, Any]) -> str:
    fk = get_flow_key(flow)

    proto = (
        fk.get("proto")
        or fk.get("protocol")
        or fk.get("ip_proto")
        or ""
    )

    proto = str(proto).upper().strip()

    if proto:
        return proto

    features_dict = flow.get("features_dict", {}) or {}

    try:
        if float(features_dict.get("TCP", 0.0)) >= 0.5:
            return "TCP"
        if float(features_dict.get("UDP", 0.0)) >= 0.5:
            return "UDP"
        if float(features_dict.get("ICMP", 0.0)) >= 0.5:
            return "ICMP"
    except Exception:
        pass

    return "UNKNOWN"


def get_ip_ports(flow: Dict[str, Any]) -> Tuple[str, str, int, int]:
    fk = get_flow_key(flow)

    src_ip = (
        fk.get("first_src_ip")
        or fk.get("src_ip")
        or fk.get("endpoint_a_ip")
        or "-"
    )

    dst_ip = (
        fk.get("first_dst_ip")
        or fk.get("dst_ip")
        or fk.get("endpoint_b_ip")
        or "-"
    )

    src_port = (
        fk.get("first_src_port")
        or fk.get("src_port")
        or fk.get("endpoint_a_port")
        or 0
    )

    dst_port = (
        fk.get("first_dst_port")
        or fk.get("dst_port")
        or fk.get("endpoint_b_port")
        or 0
    )

    try:
        src_port = int(src_port)
    except Exception:
        src_port = 0

    try:
        dst_port = int(dst_port)
    except Exception:
        dst_port = 0

    return str(src_ip), str(dst_ip), src_port, dst_port


def feature_value(flow: Dict[str, Any], name: str, default: float = 0.0) -> float:
    features_dict = flow.get("features_dict", {}) or {}

    try:
        return float(features_dict.get(name, default))
    except Exception:
        return float(default)


def compute_speed(flow: Dict[str, Any]) -> Tuple[float, float]:
    packet_count = int(flow.get("packet_count", 0) or 0)

    start_ts = float(flow.get("window_start_ts", 0.0) or 0.0)
    end_ts = float(flow.get("window_end_ts", 0.0) or 0.0)

    duration = max(end_ts - start_ts, 1e-6)
    total_bytes = feature_value(flow, "Tot sum", 0.0)

    packets_per_second = float(packet_count) / duration
    bytes_per_second = float(total_bytes) / duration

    return packets_per_second, bytes_per_second


def get_network_status(is_attack: bool, attack_probability: float) -> str:
    if not is_attack:
        return "NORMAL"

    if attack_probability >= 0.85:
        return "CRITICAL_ATTACK"

    if attack_probability >= 0.65:
        return "ATTACK"

    return "SUSPICIOUS"


def get_status_level(network_status: str) -> str:
    if network_status == "NORMAL":
        return "normal"

    if network_status == "SUSPICIOUS":
        return "warning"

    return "critical"


class ASATGNNDemoPredictor:
    def __init__(
        self,
        artifact_dir: str,
        device: str = "cpu",
        online_k: int = 8,
    ):
        self.artifact_dir = artifact_dir
        self.device = torch.device(device if device else "cpu")
        self.online_k = int(online_k)

        self.artifacts = DemoArtifacts(artifact_dir)
        self._validate_and_fix_class_mapping()

        self.encoder = self._load_encoder()
        self.gnn = self._load_gnn()

        self.encoder.eval()
        self.gnn.eval()

        print("=" * 80)
        print("ASAT GNN Demo Predictor loaded")
        print("Selected features =", len(self.artifacts.selected_features))
        print(self.artifacts.selected_features)
        print("Class names =", len(self.artifacts.class_names))

        for i, name in enumerate(self.artifacts.class_names):
            print(f"{i:02d} -> {name}")

        print("BENIGN_ID =", self.artifacts.benign_id)
        print("ATTACK_CLASS_IDS =", self.artifacts.attack_class_ids)
        print("Attack threshold =", self.artifacts.attack_threshold)
        print("=" * 80)

    def _validate_and_fix_class_mapping(self) -> None:
        current = [str(x) for x in list(self.artifacts.class_names)]

        if len(current) != 22:
            raise ValueError(
                f"Expected 22 classes for this demo model, got {len(current)}: {current}"
            )

        expected_set = set(EXPECTED_CLASS_NAMES_22)
        current_set = set(current)

        if current_set != expected_set:
            missing = sorted(expected_set - current_set)
            extra = sorted(current_set - expected_set)

            raise ValueError(
                "Class names in artifacts do not match the 22-class trained model. "
                f"Missing={missing}, Extra={extra}"
            )

        if current != EXPECTED_CLASS_NAMES_22:
            print(
                "WARNING: artifact class_names order differs from expected training order. "
                "Overriding class_names with expected 22-class order."
            )
            self.artifacts.class_names = list(EXPECTED_CLASS_NAMES_22)

        self.artifacts.benign_id = 0
        self.artifacts.attack_class_ids = list(range(1, 22))

    def _load_encoder(self):
        ckpt_path = os.path.join(
            self.artifacts.encoder_dir,
            "encoder_checkpoint.pt",
        )

        ckpt = torch.load(
            ckpt_path,
            map_location=self.device,
            weights_only=False,
        )

        input_dim = int(ckpt.get("input_dim") or len(self.artifacts.selected_features))
        latent_dim = int(ckpt.get("latent_dim") or self.artifacts.gnn_config["input_dim"])
        num_classes = int(self.artifacts.class_metadata["num_classes"])

        encoder_config = ckpt.get("encoder_config", {})
        dropout = float(encoder_config.get("encoder_dropout", 0.15))

        model = EncoderClassifier(
            input_dim=input_dim,
            latent_dim=latent_dim,
            num_classes=num_classes,
            dropout=dropout,
        ).to(self.device)

        state_dict = ckpt["state_dict"]

        try:
            model.load_state_dict(state_dict, strict=True)
        except Exception:
            model.load_state_dict(state_dict, strict=False)

        return model

    def _load_gnn(self):
        ckpt_path = os.path.join(
            self.artifacts.gnn_dir,
            "hierarchical_asat_gnn_demo_checkpoint.pt",
        )

        ckpt = torch.load(
            ckpt_path,
            map_location=self.device,
            weights_only=False,
        )

        cfg = ckpt["gnn_config"]

        model = HierarchicalASATAttentionGraphSAGE(
            input_dim=int(cfg["input_dim"]),
            hidden_dim=int(cfg["hidden_dim"]),
            num_attack_classes=int(cfg["num_attack_classes"]),
            num_layers=int(cfg["num_gnn_layers"]),
            dropout=float(cfg["dropout"]),
            att_hidden=int(cfg["att_hidden"]),
        ).to(self.device)

        model.load_state_dict(ckpt["model_state_dict"], strict=True)

        return model

    def _matrix_from_agent_flows(self, flows: List[Dict[str, Any]]) -> np.ndarray:
        rows = []
        expected = self.artifacts.selected_features

        for flow in flows:
            order = flow["features_order"]
            values = flow["features"]

            if len(order) != len(values):
                raise ValueError("features_order and features length mismatch.")

            if order == expected:
                row = values
            else:
                mapping = {name: values[i] for i, name in enumerate(order)}
                missing = [f for f in expected if f not in mapping]

                if missing:
                    raise ValueError(f"Missing selected features: {missing}")

                row = [mapping[f] for f in expected]

            rows.append(row)

        return np.asarray(rows, dtype=np.float32)

    @torch.no_grad()
    def predict_flows(self, flows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not flows:
            return []

        x_raw = self._matrix_from_agent_flows(flows)
        x_scaled = self.artifacts.scaler.transform(x_raw).astype(np.float32)

        x_tensor = torch.tensor(
            x_scaled,
            dtype=torch.float32,
            device=self.device,
        )

        encoder_out = self.encoder(x_tensor, return_embedding=True)
        z_tensor = encoder_out[0] if isinstance(encoder_out, tuple) else encoder_out

        z_np = z_tensor.detach().cpu().numpy().astype(np.float32)

        neighbor_scores, neighbor_indices = self.artifacts.search_neighbors(
            z_np,
            k=self.online_k,
        )

        graph = build_online_subgraph(
            new_embeddings=z_np,
            neighbor_indices=neighbor_indices,
            neighbor_scores=neighbor_scores,
            reference_embeddings=self.artifacts.reference_embeddings,
            device=self.device,
            trust_gate_gamma=float(self.artifacts.gnn_config.get("trust_gate_gamma", 0.35)),
            trust_gate_min=float(self.artifacts.gnn_config.get("trust_gate_min", 0.65)),
            trust_gate_max=float(self.artifacts.gnn_config.get("trust_gate_max", 1.10)),
        )

        binary_logits, attack_logits = self.gnn(
            graph["x"],
            graph["edge_index"],
            graph["edge_attr"],
        )

        batch_size = int(graph["batch_size"])

        binary_logits = binary_logits[:batch_size]
        attack_logits = attack_logits[:batch_size]

        attack_prob = torch.sigmoid(binary_logits)
        attack_softmax = torch.softmax(attack_logits, dim=1)

        is_attack = attack_prob >= float(self.artifacts.attack_threshold)

        pred_class_ids = torch.empty(
            batch_size,
            dtype=torch.long,
            device=self.device,
        )

        pred_class_ids[~is_attack] = int(self.artifacts.benign_id)

        attack_id_to_class = torch.tensor(
            self.artifacts.attack_class_ids,
            dtype=torch.long,
            device=self.device,
        )

        attack_pred_idx = attack_softmax.argmax(dim=1)
        pred_class_ids[is_attack] = attack_id_to_class[attack_pred_idx[is_attack]]

        pred_class_ids_np = pred_class_ids.detach().cpu().numpy()
        attack_prob_np = attack_prob.detach().cpu().numpy()
        attack_conf_np = attack_softmax.max(dim=1).values.detach().cpu().numpy()

        outputs = []
        now = time.time()

        for i, flow in enumerate(flows):
            class_id = int(pred_class_ids_np[i])
            class_name = self.artifacts.class_names[class_id]
            attack_p = float(attack_prob_np[i])

            observed_protocol = get_flow_protocol(flow)
            src_ip, dst_ip, src_port, dst_port = get_ip_ports(flow)
            packets_per_second, bytes_per_second = compute_speed(flow)

            if class_id == self.artifacts.benign_id:
                confidence = float(1.0 - attack_p)
                subtype_confidence = confidence
                attack_flag = False
                attack_type = "Benign"
            else:
                subtype_confidence = float(attack_conf_np[i])
                confidence = float(attack_p * subtype_confidence)
                attack_flag = True
                attack_type = get_main_attack_group(class_name)

            network_status = get_network_status(
                is_attack=attack_flag,
                attack_probability=attack_p,
            )

            status_level = get_status_level(network_status)

            outputs.append(
                {
                    "received_at": now,

                    "attack_type": attack_type,
                    "network_status": network_status,
                    "status_level": status_level,

                    "source_ip": src_ip,
                    "source_port": src_port,
                    "destination_ip": dst_ip,
                    "destination_port": dst_port,
                    "protocol": observed_protocol,
                    "total_packets": int(flow.get("packet_count", 0)),
                    "packets_per_second": float(packets_per_second),
                    "bytes_per_second": float(bytes_per_second),

                    "class_id": class_id,
                    "class_name": class_name,
                    "is_attack": attack_flag,
                    "confidence": clamp01(confidence),
                    "attack_probability": clamp01(attack_p),
                    "subtype_confidence": clamp01(subtype_confidence),

                    "flow_key": flow.get("flow_key", {}),
                    "packet_count": int(flow.get("packet_count", 0)),
                    "window_start_ts": float(flow.get("window_start_ts", 0.0)),
                    "window_end_ts": float(flow.get("window_end_ts", 0.0)),

                    "features_order": flow.get("features_order", []),
                    "features": flow.get("features", []),
                }
            )

        return outputs