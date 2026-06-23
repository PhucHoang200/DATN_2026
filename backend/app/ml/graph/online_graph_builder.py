from typing import Dict, Any

import numpy as np
import torch

from app.ml.models.asat_gnn import build_asat_edge_attr


def build_online_subgraph(
    new_embeddings: np.ndarray,
    neighbor_indices: np.ndarray,
    neighbor_scores: np.ndarray,
    reference_embeddings: np.ndarray,
    device: torch.device,
    trust_gate_gamma: float = 0.35,
    trust_gate_min: float = 0.65,
    trust_gate_max: float = 1.10,
) -> Dict[str, Any]:
    """
    Build a local inference graph.

    Node layout:
        [0 ... B-1]                      : new realtime flow nodes
        [B ... B+num_unique_neighbors-1] : selected reference train nodes

    Edge direction:
        reference_neighbor -> new_node

    This matches source_neighbor_to_target_node inference logic.
    """

    new_embeddings = np.asarray(new_embeddings, dtype=np.float32)
    neighbor_indices = np.asarray(neighbor_indices, dtype=np.int64)
    neighbor_scores = np.asarray(neighbor_scores, dtype=np.float32)

    if new_embeddings.ndim != 2:
        raise ValueError("new_embeddings must be 2D [B, D].")

    batch_size = new_embeddings.shape[0]

    if neighbor_indices.shape != neighbor_scores.shape:
        raise ValueError("neighbor_indices and neighbor_scores shape mismatch.")

    unique_ref_ids = sorted(set(int(x) for x in neighbor_indices.reshape(-1).tolist()))

    ref_to_local = {
        ref_id: batch_size + local_i
        for local_i, ref_id in enumerate(unique_ref_ids)
    }

    ref_emb = reference_embeddings[unique_ref_ids].astype(np.float32)

    x_np = np.vstack([new_embeddings, ref_emb]).astype(np.float32)

    edges_src = []
    edges_dst = []
    edge_weights = []

    for new_i in range(batch_size):
        for j in range(neighbor_indices.shape[1]):
            ref_id = int(neighbor_indices[new_i, j])
            score = float(neighbor_scores[new_i, j])

            src = ref_to_local[ref_id]
            dst = new_i

            edges_src.append(src)
            edges_dst.append(dst)
            edge_weights.append(score)

    if len(edges_src) == 0:
        raise RuntimeError("No online edges were created.")

    edge_index_np = np.asarray([edges_src, edges_dst], dtype=np.int64)
    base_edge_attr_np = np.asarray(edge_weights, dtype=np.float32).reshape(-1, 1)

    x = torch.tensor(x_np, dtype=torch.float32, device=device)
    edge_index = torch.tensor(edge_index_np, dtype=torch.long, device=device)
    base_edge_attr = torch.tensor(base_edge_attr_np, dtype=torch.float32, device=device)

    reliability = torch.ones(
        (base_edge_attr.size(0), 1),
        dtype=torch.float32,
        device=device,
    )

    edge_attr = build_asat_edge_attr(
        base_edge_attr=base_edge_attr,
        edge_reliability=reliability,
        trust_gate_gamma=trust_gate_gamma,
        trust_gate_min=trust_gate_min,
        trust_gate_max=trust_gate_max,
    )

    return {
        "x": x,
        "edge_index": edge_index,
        "edge_attr": edge_attr,
        "batch_size": batch_size,
        "unique_reference_ids": unique_ref_ids,
    }