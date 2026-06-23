# ASAT GNN IDS Realtime Dashboard

This repository contains a real-time Network Intrusion Detection System (IDS) demo based on an ASAT-GNN model. The system is designed to receive network-flow features from an Ubuntu traffic agent, run real-time inference through a FastAPI backend, and visualize IDS results on a browser-based dashboard.

The demo focuses on the following IDS outputs:

* Attack group
* Source IP
* Destination IP
* Protocol
* Total packets
* Traffic speed
* Attack score
* Current network status
* Last detected attack
* Recent alerts
* Flow prediction history

---

## Project Structure

```text
project-root/
│
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   └── logging.py
│   │   │
│   │   ├── ml/
│   │   │   ├── graph/
│   │   │   │   └── online_graph_builder.py
│   │   │   │
│   │   │   ├── models/
│   │   │   │   ├── asat_gnn.py
│   │   │   │   └── encoder.py
│   │   │   │
│   │   │   ├── artifact_loader.py
│   │   │   ├── feature_schema.py
│   │   │   └── predictor.py
│   │   │
│   │   ├── store/
│   │   │   └── memory_store.py
│   │   │
│   │   ├── websocket/
│   │   │   └── manager.py
│   │   │
│   │   ├── main.py
│   │   └── schemas.py
│   │
│   ├── requirements.txt
│   └── README.md
│
├── frontend/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── config.js
│
└── README.md
```

---

## Backend

The `backend/` directory contains the FastAPI server used for real-time intrusion detection. It receives flow-level features from the Ubuntu traffic agent, loads the trained ASAT-GNN model, performs inference, stores recent prediction events, and broadcasts live updates to the frontend dashboard through WebSocket.

---

### `backend/app/main.py`

This is the main FastAPI application entry point.

Main responsibilities:

* Start the FastAPI application.
* Load the trained ASAT-GNN demo predictor.
* Receive incoming flow features from the Ubuntu agent.
* Run real-time IDS inference.
* Store prediction events in memory.
* Provide recent event history for the dashboard.
* Broadcast prediction results to WebSocket clients.

---

### `backend/app/schemas.py`

This file defines the Pydantic schemas used by the backend API.

Main objects:

* `FlowInput`: represents one extracted network flow.
* `AgentFlowPayload`: represents a batch of flows sent by the Ubuntu agent.
* `PredictionOutput`: represents one IDS prediction event.
* `HealthOutput`: represents backend health-check information.

These schemas help validate input payloads and standardize backend responses.

---

### `backend/app/core/logging.py`

This file contains the logging configuration for the backend.

It provides a consistent logging format for:

* API requests
* Model loading
* Prediction flow
* Runtime errors
* Debugging information

---

### `backend/app/ml/feature_schema.py`

This file defines the selected feature order expected by the trained IDS model.

The feature order must match the exact order used during training and preprocessing. If the feature order is changed, the model input may become inconsistent and prediction quality may be incorrect.

---

### `backend/app/ml/artifact_loader.py`

This module loads all trained artifacts required for real-time inference.

Typical loaded artifacts include:

* Selected feature list
* StandardScaler object
* Label encoder or class metadata
* Encoder checkpoint
* GNN model checkpoint
* FAISS index or graph reference bank
* Reference embeddings
* Attack threshold and decision metadata

This module ensures that the runtime prediction pipeline uses the same preprocessing configuration, class mapping, and graph-related artifacts as the training pipeline.

---

### `backend/app/ml/predictor.py`

This file implements the main real-time IDS prediction pipeline.

Main responsibilities:

* Validate and reorder incoming flow features.
* Apply the trained StandardScaler.
* Generate embeddings using the trained feature encoder.
* Build an online graph neighborhood.
* Run the ASAT-GNN model.
* Compute attack probability.
* Map detailed model classes into main IDS attack groups.
* Return source IP, destination IP, protocol, packet count, speed, attack score, and status information.

The dashboard mainly displays high-level attack groups such as:

```text
Benign
DDoS
DoS
Recon
Spoofing
Mirai
```

---

### `backend/app/ml/models/encoder.py`

This file defines the feature encoder architecture used before the GNN model.

The encoder transforms selected network-flow features into latent embeddings. These embeddings are then used for online graph construction and GNN inference.

---

### `backend/app/ml/models/asat_gnn.py`

This file defines the ASAT-GNN model architecture used for intrusion detection.

The model is responsible for:

* Benign-vs-attack prediction
* Attack subtype prediction
* Producing logits used to compute attack probabilities
* Supporting graph-based message passing and attention/trust-aware prediction

---

### `backend/app/ml/graph/online_graph_builder.py`

This module builds an online inference graph for newly received flows.

Main responsibilities:

* Receive new flow embeddings.
* Search for nearest reference nodes.
* Build graph edge indices.
* Build edge attributes.
* Apply similarity or trust-gate based edge weighting.
* Prepare graph tensors for GNN inference.

---

### `backend/app/store/memory_store.py`

This file provides an in-memory event store for recent prediction results.

Main responsibilities:

* Store recent prediction events.
* Maintain event counters.
* Provide summary statistics.
* Return recent events to the frontend.

Typical stored statistics include:

* Total flows
* Attack flows
* Benign flows
* Attack group distribution

---

### `backend/app/websocket/manager.py`

This module manages WebSocket connections between the backend and the frontend dashboard.

Main responsibilities:

* Track active WebSocket clients.
* Send real-time prediction events to connected clients.
* Handle client connection and disconnection.

---

### `backend/requirements.txt`

This file lists the Python dependencies required to run the backend server and model inference pipeline.

Typical dependencies include:

```text
fastapi
uvicorn
numpy
torch
scikit-learn
faiss-cpu
pydantic
python-dotenv
```

The exact dependencies may vary depending on the exported model artifacts and runtime environment.

---

## Frontend

The `frontend/` directory contains the browser-based IDS dashboard. It connects to the backend API and WebSocket server, displays real-time prediction results, visualizes current traffic trends, and highlights detected attacks.

---

### `frontend/index.html`

This is the main HTML structure of the dashboard.

It defines the layout of the IDS interface, including:

* Dashboard header
* Current network status
* Flow statistics
* Latest flow information
* Last detected attack
* Realtime traffic trend chart
* Attack group distribution
* Realtime alerts
* Latest flow prediction table

The dashboard is designed to clearly show the difference between normal traffic and attack traffic during a live demo.

---

### `frontend/styles.css`

This file defines the visual design of the dashboard.

The dashboard uses a simple and modern color scheme:

* Green for normal traffic
* Red for attack traffic
* Blue for neutral system information
* Light backgrounds for readability

The CSS controls:

* Three-column dashboard layout
* Responsive layout for smaller screens
* Status cards
* Metric cards
* Traffic chart panel
* Attack distribution bars
* Alert cards
* Prediction table styling

---

### `frontend/app.js`

This file contains the frontend logic for real-time dashboard behavior.

Main responsibilities:

* Fetch recent events from the backend API.
* Connect to the backend WebSocket stream.
* Receive new prediction events in real time.
* Update dashboard statistics.
* Update the current network status.
* Render the realtime traffic trend chart.
* Render recent alerts.
* Render flow prediction history.
* Preserve the last detected attack for review.
* Automatically return the main status to `NORMAL TRAFFIC` if no new attack log is received for 10 seconds.

Important behavior:

* When a new attack event is received, the dashboard changes the main status to `ATTACK DETECTED`.
* If no new attack event is received for 10 seconds, the main status automatically returns to `NORMAL TRAFFIC`.
* The last detected attack remains visible in the dashboard for investigation and explanation.
* The traffic chart continues running even when there is no attack to simulate continuous real-time monitoring.

---

### `frontend/config.js`

This file stores frontend configuration values such as the backend API base URL and WebSocket URL.

Example:

```javascript
window.ASAT_CONFIG = {
  API_BASE: "http://192.168.116.1:8000",
  WS_URL: "ws://192.168.116.1:8000/ws"
};
```

The values should be updated depending on where the backend server is running.

---

## Runtime Data Flow

The system follows this real-time data flow:

```text
Kali attacker / normal traffic generator
        ↓
Ubuntu victim network interface
        ↓
Ubuntu Python traffic agent
        ↓
Flow feature extraction
        ↓
FastAPI backend
        ↓
Feature scaling + encoder embedding
        ↓
Online graph construction
        ↓
ASAT-GNN prediction
        ↓
Event store + WebSocket broadcast
        ↓
Frontend IDS dashboard
```

---

## Dashboard Output

The dashboard focuses on the following IDS fields:

| Field                | Description                                                         |
| -------------------- | ------------------------------------------------------------------- |
| Attack group         | Main IDS group such as DDoS, DoS, Recon, Spoofing, Mirai, or Benign |
| Source IP            | IP address of the traffic source                                    |
| Destination IP       | IP address of the traffic destination                               |
| Protocol             | Network protocol such as TCP, UDP, or ICMP                          |
| Total packets        | Total packet count in the detected flow                             |
| Speed                | Estimated packet rate, usually displayed as packets per second      |
| Attack score         | Model confidence that the flow is attack traffic                    |
| Current status       | Current IDS state: normal or attack                                 |
| Last detected attack | Most recent attack preserved for review                             |
| Realtime alerts      | Recent prediction alerts                                            |
| Flow history         | Latest prediction records                                           |

---

## Demo Behavior

During normal traffic, the dashboard displays:

```text
Current status: NORMAL TRAFFIC
Traffic color: Green
Attack score: Low or stable
Traffic chart: Normal baseline
```

During attack traffic, the dashboard displays:

```text
Current status: ATTACK DETECTED
Traffic color: Red
Attack group: DDoS / DoS / Recon / Spoofing / Mirai
Source IP: Kali attacker
Destination IP: Ubuntu victim
Protocol: TCP / UDP / ICMP
Packet count and speed: Increased
Traffic chart: Red spike or abnormal traffic increase
```

If no new attack log is received for 10 seconds, the main status automatically returns to:

```text
Current status: NORMAL TRAFFIC
```

However, the last detected attack is still preserved in:

* Last detected attack
* Realtime alerts
* Latest flow predictions

This behavior makes the dashboard suitable for real-time IDS demonstration because it separates the current network state from historical attack evidence.

---

## Example Demo Scenarios

### UDP Flood Test

Expected dashboard behavior:

```text
Attack group: DDoS or DoS
Protocol: UDP
Source IP: Kali attacker
Destination IP: Ubuntu victim
Packet count: Increased
Speed: Increased
Current status: ATTACK DETECTED
```

Example Kali command:

```bash
sudo hping3 -2 -c 1000 -d 1200 -i u1000 192.168.116.129 -p 5000
```

---

### TCP SYN Flood Test

Expected dashboard behavior:

```text
Attack group: DDoS or DoS
Protocol: TCP
Source IP: Kali attacker
Destination IP: Ubuntu victim
Packet count: Increased
Speed: Increased
Current status: ATTACK DETECTED
```

Example Kali command:

```bash
sudo hping3 -S -c 1000 -i u1000 192.168.116.129 -p 80
```

---

## Notes

This project is intended for a controlled lab environment only. The demo should be performed inside a private virtualized environment such as VMware or VirtualBox. Traffic generation commands should only target machines owned and controlled by the user.

The real-time dashboard focuses on practical IDS visualization rather than exact fine-grained attack subtype interpretation. The model may internally predict detailed classes, but the dashboard groups them into higher-level IDS categories for clearer demonstration and explanation.
