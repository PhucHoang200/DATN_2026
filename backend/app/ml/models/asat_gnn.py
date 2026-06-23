import torch
import torch.nn as nn
import torch.nn.functional as F

from torch_geometric.nn import MessagePassing
from torch_geometric.utils import softmax


DEFAULT_TRUST_GATE_GAMMA = 0.35
DEFAULT_TRUST_GATE_MIN = 0.65
DEFAULT_TRUST_GATE_MAX = 1.10


def compute_edge_cosine(x, edge_index):
    src = edge_index[0]
    dst = edge_index[1]

    x_norm = F.normalize(x, p=2, dim=1)
    sim = (x_norm[src] * x_norm[dst]).sum(dim=1, keepdim=True)

    return sim.clamp(min=-1.0, max=1.0)


def build_asat_edge_attr(
    base_edge_attr,
    edge_reliability,
    trust_gate_gamma: float = DEFAULT_TRUST_GATE_GAMMA,
    trust_gate_min: float = DEFAULT_TRUST_GATE_MIN,
    trust_gate_max: float = DEFAULT_TRUST_GATE_MAX,
):
    if base_edge_attr.dim() == 1:
        base_w = base_edge_attr.view(-1, 1)
    else:
        base_w = base_edge_attr[:, :1]

    r = edge_reliability.view(-1, 1)
    final_w = base_w * r

    trust_gate = 1.0 + float(trust_gate_gamma) * (final_w - 1.0)
    trust_gate = torch.clamp(
        trust_gate,
        min=float(trust_gate_min),
        max=float(trust_gate_max),
    )

    return torch.cat(
        [
            base_w,
            r,
            final_w,
            trust_gate,
        ],
        dim=1,
    )


class ASATAttentionSAGEConv(MessagePassing):
    def __init__(
        self,
        in_channels,
        out_channels,
        edge_dim=4,
        att_hidden=64,
        dropout=0.25,
    ):
        super().__init__(aggr="add", node_dim=0)

        self.dropout = dropout

        self.lin_self = nn.Linear(in_channels, out_channels)
        self.lin_neigh = nn.Linear(in_channels, out_channels)

        self.att_mlp = nn.Sequential(
            nn.Linear(2 * out_channels + edge_dim, att_hidden),
            nn.LeakyReLU(0.2),
            nn.Dropout(dropout),
            nn.Linear(att_hidden, 1),
        )

        self.norm = nn.BatchNorm1d(out_channels)

    def forward(self, x, edge_index, edge_attr):
        x_neigh = self.lin_neigh(x)

        out = self.propagate(
            edge_index=edge_index,
            x=x_neigh,
            edge_attr=edge_attr,
            size=(x.size(0), x.size(0)),
        )

        out = out + self.lin_self(x)
        out = self.norm(out)

        return out

    def message(self, x_i, x_j, edge_attr, index, ptr, size_i):
        att_input = torch.cat([x_i, x_j, edge_attr], dim=-1)

        e = self.att_mlp(att_input).view(-1)

        alpha = softmax(e, index, ptr, size_i)
        alpha = F.dropout(alpha, p=self.dropout, training=self.training)

        trust_gate = edge_attr[:, 3].view(-1)

        msg = x_j * alpha.view(-1, 1) * trust_gate.view(-1, 1)

        return msg


class HierarchicalASATAttentionGraphSAGE(nn.Module):
    def __init__(
        self,
        input_dim,
        hidden_dim,
        num_attack_classes,
        num_layers=2,
        dropout=0.25,
        att_hidden=64,
    ):
        super().__init__()

        self.dropout = dropout
        self.convs = nn.ModuleList()

        for layer_idx in range(int(num_layers)):
            in_dim = input_dim if layer_idx == 0 else hidden_dim

            self.convs.append(
                ASATAttentionSAGEConv(
                    in_channels=in_dim,
                    out_channels=hidden_dim,
                    edge_dim=4,
                    att_hidden=att_hidden,
                    dropout=dropout,
                )
            )

        self.shared_norm = nn.LayerNorm(hidden_dim)

        self.binary_head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
        )

        self.attack_head = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, num_attack_classes),
        )

    def forward(self, x, edge_index, edge_attr):
        h = x

        for conv in self.convs:
            h = conv(h, edge_index, edge_attr)
            h = F.relu(h)
            h = F.dropout(h, p=self.dropout, training=self.training)

        h = self.shared_norm(h)

        binary_logit = self.binary_head(h).view(-1)
        attack_logits = self.attack_head(h)

        return binary_logit, attack_logits