# \## Project Structure

# 

# This project is organized into two main parts: the \*\*backend\*\* and the \*\*frontend\*\*. The backend is responsible for receiving network-flow features from the Ubuntu agent, loading the trained ASAT-GNN intrusion detection model, performing real-time prediction, storing recent events in memory, and broadcasting prediction results to the dashboard through WebSocket. The frontend provides a real-time IDS dashboard for visualizing traffic status, detected attack groups, source/destination information, protocols, packet counts, traffic speed, attack scores, and recent alerts.

# 

# ```text

# project-root/

# │

# ├── backend/

# │   ├── app/

# │   │   ├── core/

# │   │   │   └── logging.py

# │   │   │

# │   │   ├── ml/

# │   │   │   ├── graph/

# │   │   │   │   └── online\_graph\_builder.py

# │   │   │   │

# │   │   │   ├── models/

# │   │   │   │   ├── asat\_gnn.py

# │   │   │   │   └── encoder.py

# │   │   │   │

# │   │   │   ├── artifact\_loader.py

# │   │   │   ├── feature\_schema.py

# │   │   │   └── predictor.py

# │   │   │

# │   │   ├── store/

# │   │   │   └── memory\_store.py

# │   │   │

# │   │   ├── websocket/

# │   │   │   └── manager.py

# │   │   │

# │   │   ├── main.py

# │   │   └── schemas.py

# │   │

# │   ├── requirements.txt

# │   └── README.md

# │

# ├── frontend/

# │   ├── index.html

# │   ├── styles.css

# │   ├── app.js

# │   └── config.js

# │

# └── README.md

# ```

# 

# \### Backend

# 

# The `backend/` directory contains the FastAPI-based server used for real-time intrusion detection. It exposes API endpoints for receiving flow-level features from the Ubuntu traffic agent, runs the trained ASAT-GNN model, stores prediction results, and sends live updates to the dashboard.

# 

# \#### `backend/app/main.py`

# 

# This is the main FastAPI application entry point. It initializes the API server, loads the IDS predictor, receives flow data from the Ubuntu agent, performs inference, stores prediction events, and broadcasts new results to connected frontend clients.

# 

# Main responsibilities:

# 

# \* Start the FastAPI application.

# \* Load the trained ASAT-GNN demo predictor.

# \* Receive incoming flow features from the Ubuntu agent.

# \* Return prediction results.

# \* Provide recent event history for the dashboard.

# \* Broadcast prediction events through WebSocket.

# 

# \#### `backend/app/schemas.py`

# 

# This file defines the Pydantic data schemas used by the backend API. It validates incoming agent payloads and standardizes outgoing prediction responses.

# 

# Main objects:

# 

# \* `FlowInput`: represents one extracted network flow.

# \* `AgentFlowPayload`: represents a batch of flows sent by the Ubuntu agent.

# \* `PredictionOutput`: represents one prediction event returned by the IDS model.

# \* `HealthOutput`: represents backend health-check information.

# 

# \#### `backend/app/core/logging.py`

# 

# This file contains the logging configuration for the backend. It provides a consistent logging format for debugging API requests, model loading, prediction flow, and runtime errors.

# 

# \#### `backend/app/ml/feature\_schema.py`

# 

# This file defines the selected feature order expected by the trained model. The feature order must match the exact order used during training and preprocessing.

# 

# It is important because the IDS model expects input features in a fixed order. If the order is changed, prediction quality may become incorrect.

# 

# \#### `backend/app/ml/artifact\_loader.py`

# 

# This module loads all trained model artifacts required for real-time inference.

# 

# Typical loaded artifacts include:

# 

# \* Selected feature list.

# \* StandardScaler object.

# \* Label encoder or class metadata.

# \* Encoder checkpoint.

# \* GNN model checkpoint.

# \* FAISS index or graph reference bank.

# \* Reference embeddings.

# \* Attack threshold and rescue/decision metadata.

# 

# This module ensures that the runtime prediction pipeline uses the same preprocessing and class mapping as the training pipeline.

# 

# \#### `backend/app/ml/predictor.py`

# 

# This file implements the main real-time IDS prediction pipeline. It receives flow features from the backend API, applies preprocessing, generates embeddings using the trained encoder, builds an online graph neighborhood, runs the ASAT-GNN model, and returns the final prediction.

# 

# Main responsibilities:

# 

# \* Validate and reorder incoming features.

# \* Apply the trained StandardScaler.

# \* Generate feature embeddings using the encoder.

# \* Build an online subgraph with reference neighbors.

# \* Run the ASAT-GNN model.

# \* Compute attack probability.

# \* Map detailed model classes into main IDS attack groups such as `DDoS`, `DoS`, `Recon`, `Spoofing`, `Mirai`, and `Benign`.

# \* Return source IP, destination IP, protocol, packet count, speed, attack score, and status information.

# 

# \#### `backend/app/ml/models/encoder.py`

# 

# This file defines the feature encoder architecture used before the GNN model. The encoder transforms raw selected features into latent embeddings. These embeddings are then used for graph construction and GNN inference.

# 

# \#### `backend/app/ml/models/asat\_gnn.py`

# 

# This file defines the ASAT-GNN model architecture used for intrusion detection. The model combines graph neural network message passing with attention/trust-based mechanisms and hierarchical attack prediction heads.

# 

# The model is responsible for:

# 

# \* Benign-vs-attack prediction.

# \* Attack subtype prediction.

# \* Producing logits used to compute attack probabilities.

# 

# \#### `backend/app/ml/graph/online\_graph\_builder.py`

# 

# This module builds an online inference graph for newly received flows. It connects new flow embeddings with reference embeddings from the trained graph bank.

# 

# Main responsibilities:

# 

# \* Receive new flow embeddings.

# \* Search for nearest reference nodes.

# \* Build edge indices and edge attributes.

# \* Apply trust-gate or similarity-based edge weighting.

# \* Prepare graph tensors for the GNN model.

# 

# \#### `backend/app/store/memory\_store.py`

# 

# This file provides an in-memory event store for recent prediction results. It allows the dashboard to request recent IDS events without requiring a database.

# 

# Main responsibilities:

# 

# \* Store recent prediction events.

# \* Maintain event counters.

# \* Provide summary statistics such as total flows, attack flows, benign flows, and class/group distribution.

# \* Return recent events to the frontend.

# 

# \#### `backend/app/websocket/manager.py`

# 

# This module manages WebSocket connections between the backend and the frontend dashboard.

# 

# Main responsibilities:

# 

# \* Track active WebSocket clients.

# \* Send real-time prediction events to connected clients.

# \* Handle client connection and disconnection.

# 

# \#### `backend/requirements.txt`

# 

# This file lists the Python dependencies required to run the backend server, model inference pipeline, and WebSocket service.

# 

# Typical dependencies include:

# 

# \* FastAPI

# \* Uvicorn

# \* NumPy

# \* PyTorch

# \* scikit-learn

# \* FAISS

# \* Pydantic

# \* python-multipart or other API-related packages

# 

# \---

# 

# \### Frontend

# 

# The `frontend/` directory contains the browser-based IDS dashboard. It connects to the backend API and WebSocket server, displays real-time prediction results, visualizes network traffic trends, and highlights attack activity.

# 

# \#### `frontend/index.html`

# 

# This is the main HTML structure of the dashboard. It defines the layout of the IDS interface, including:

# 

# \* Dashboard header.

# \* Current network status card.

# \* Flow statistics.

# \* Latest flow information.

# \* Last detected attack.

# \* Realtime traffic trend chart.

# \* Attack group distribution.

# \* Realtime alerts.

# \* Latest flow prediction table.

# 

# The dashboard is designed to clearly show the difference between normal traffic and attack traffic during a live demo.

# 

# \#### `frontend/styles.css`

# 

# This file defines the visual design of the dashboard. It uses a simple and modern color scheme:

# 

# \* Green for normal traffic.

# \* Red for attack traffic.

# \* Blue for neutral system information.

# \* Light backgrounds for readability.

# 

# The CSS controls:

# 

# \* Three-column dashboard layout.

# \* Responsive layout for smaller screens.

# \* Status cards.

# \* Metric cards.

# \* Traffic chart panel.

# \* Attack distribution bars.

# \* Alert cards.

# \* Prediction table styling.

# 

# \#### `frontend/app.js`

# 

# This file contains the frontend logic for real-time dashboard behavior.

# 

# Main responsibilities:

# 

# \* Fetch recent events from the backend API.

# \* Connect to the backend WebSocket stream.

# \* Receive new prediction events in real time.

# \* Update dashboard statistics.

# \* Update the current network status.

# \* Automatically return the main status to `NORMAL TRAFFIC` if no attack log is received for 10 seconds.

# \* Keep the last detected attack visible for investigation.

# \* Render the realtime traffic trend chart.

# \* Render recent alerts and flow prediction history.

# 

# Important behavior:

# 

# \* When a new attack event is received, the dashboard changes the main status to `ATTACK DETECTED`.

# \* If no new attack event is received for 10 seconds, the main status automatically returns to `NORMAL TRAFFIC`.

# \* Historical attack information remains available in the `Last detected attack`, `Realtime alerts`, and `Latest flow predictions` sections.

# 

# \#### `frontend/config.js`

# 

# This file stores frontend configuration values such as the backend API base URL and WebSocket URL.

# 

# Example:

# 

# ```javascript

# window.ASAT\_CONFIG = {

# &#x20; API\_BASE: "http://192.168.116.1:8000",

# &#x20; WS\_URL: "ws://192.168.116.1:8000/ws"

# };

# ```

# 

# The values should be updated depending on where the backend server is running.

# 

# \---

# 

# \## Runtime Data Flow

# 

# The system follows this real-time data flow:

# 

# ```text

# Kali attacker / normal traffic generator

# &#x20;       ↓

# Ubuntu victim network interface

# &#x20;       ↓

# Ubuntu Python traffic agent

# &#x20;       ↓

# Flow feature extraction

# &#x20;       ↓

# FastAPI backend

# &#x20;       ↓

# Feature scaling + encoder embedding

# &#x20;       ↓

# Online graph construction

# &#x20;       ↓

# ASAT-GNN prediction

# &#x20;       ↓

# Event store + WebSocket broadcast

# &#x20;       ↓

# Frontend IDS dashboard

# ```

# 

# The dashboard focuses on the following key IDS fields:

# 

# \* Attack group.

# \* Source IP.

# \* Destination IP.

# \* Protocol.

# \* Total packets.

# \* Traffic speed.

# \* Attack score.

# \* Current network status.

# \* Last detected attack.

# \* Recent alerts.

# \* Flow prediction history.

# 

# \---

# 

# \## Demo Behavior

# 

# During normal traffic, the dashboard displays:

# 

# ```text

# Current status: NORMAL TRAFFIC

# Traffic color: Green

# Attack score: Low or stable

# ```

# 

# During attack traffic, the dashboard displays:

# 

# ```text

# Current status: ATTACK DETECTED

# Traffic color: Red

# Attack group: DDoS / DoS / Recon / Spoofing / Mirai

# Source IP: Kali attacker

# Destination IP: Ubuntu victim

# Protocol: TCP / UDP / ICMP

# Packet count and speed: Increased

# ```

# 

# If no new attack log is received for 10 seconds, the main status automatically returns to:

# 

# ```text

# Current status: NORMAL TRAFFIC

# ```

# 

# The last detected attack is still preserved in the dashboard for review and explanation.



