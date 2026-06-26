# ASAT GNN IDS Realtime Demo

## 1. Introduction

This project implements a network intrusion detection system using a Graph Neural Network (GNN)-based model. The system is designed to detect abnormal network traffic in a controlled IoT/lab environment. The research pipeline is built on the CICIoT2023 dataset and combines data preprocessing, feature selection, feature encoding, graph construction, and hierarchical GNN-based intrusion detection.

The demo version follows a near real-time architecture:

```text
Kali Linux / traffic source
        ↓
Ubuntu victim + Python Agent
        ↓
Feature extraction from pcap/live traffic
        ↓
FastAPI Backend
        ↓
Scaler → Encoder → FAISS neighbor search → Local graph → GNN prediction
        ↓
WebSocket
        ↓
Frontend Dashboard
```

This project is intended for academic research, graduation thesis work, and controlled lab demonstration only. Do not use this system, traffic generation scripts, or any attack simulation method against public systems or systems that you do not own or have explicit permission to test.

---

## 2. Project Objectives

The main objective of this project is to build a network intrusion detection system that can:

* Preprocess and select relevant features from the CICIoT2023 dataset.
* Train a feature encoder that maps network-flow feature vectors into an embedding space.
* Construct a behavior graph based on similarity between network flows.
* Train a hierarchical GNN model for benign-vs-attack detection and attack classification.
* Export trained model artifacts for near real-time inference.
* Build a backend and frontend dashboard for visualizing detected attacks in a controlled lab environment.

---

## 3. Overall Project Structure

```text
ids-demo/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── ml/
│   │   │   ├── models/
│   │   │   └── graph/
│   │   ├── store/
│   │   └── websocket/
│   │
│   ├── artifacts/
│   │   └── hierarchical_asat_gnn_demo_minimal_artifacts/
│   │
│   ├── requirements.txt
│   ├── .env.example
│   └── run_backend.sh
│
├── frontend/
│   ├── index.html
│   ├── styles.css
│   ├── config.js
│   ├── app.js
│   └── run_frontend.sh
│
├── ubuntu-agent/
│   ├── run_agent.py
│   ├── requirements.txt
│   ├── .env.example
│   └── ids_agent/
│       ├── config.py
│       ├── tcpdump_capture.py
│       ├── pcap_watcher.py
│       ├── feature_extractor.py
│       ├── csv_logger.py
│       └── sender.py
│
├── .gitignore
└── README.md
```

---

## 4. Main Components

### 4.1. Ubuntu Python Agent

The Ubuntu Python Agent runs on the Ubuntu victim machine. It is responsible for capturing network traffic and extracting flow-level features.

Main responsibilities:

* Start `tcpdump` to capture traffic in short time windows.
* Watch newly generated pcap files.
* Group packets into flow-like records.
* Extract the selected 28 features according to the schema used during training.
* Optionally write extracted features to a CSV log file for verification.
* Send feature payloads to the backend through HTTP POST requests.

The agent does not load the GNN model, does not load the FAISS index, and does not perform model inference. All model inference is handled by the backend.

---

### 4.2. Backend

The backend is implemented with FastAPI. It receives extracted features from the Ubuntu agent, loads the exported model artifacts, performs near real-time inference, stores recent prediction events, and broadcasts results to the frontend dashboard.

Main responsibilities:

* Receive feature payloads from the Ubuntu agent.
* Load exported artifacts from the offline training pipeline.
* Apply the trained `StandardScaler`.
* Encode selected features into embeddings using the trained encoder.
* Search nearest reference embeddings using FAISS.
* Build a local inference graph for new flows.
* Run the Hierarchical ASAT Attention GraphSAGE model.
* Return benign/attack prediction results and attack group information.
* Broadcast prediction events to the dashboard through WebSocket.

---

### 4.3. Frontend Dashboard

The frontend is a browser-based dashboard implemented with HTML, CSS, and JavaScript. It displays near real-time IDS predictions from the backend.

Main responsibilities:

* Connect to the backend API.
* Connect to the backend WebSocket stream.
* Display the current network status.
* Display the total number of processed flows.
* Display benign and attack flow counts.
* Display attack group distribution.
* Display real-time alerts.
* Display the latest flow prediction table.
* Show a traffic trend chart over time.
* Automatically return the main status to `NORMAL TRAFFIC` if no new attack log is received for 10 seconds.

---

## 5. Machine Learning Pipeline

The machine learning pipeline consists of the following stages:

```text
CICIoT2023 CSV files
    ↓
Sampling + class filtering
    ↓
Train/test split
    ↓
Feature selection
    ↓
StandardScaler
    ↓
Mild-balanced training pool
    ↓
Supervised Contrastive Encoder
    ↓
Hybrid-kNN graph construction
    ↓
Hierarchical ASAT Attention GraphSAGE
    ↓
Adversarial training
    ↓
Attack-head rescue / decision calibration
    ↓
Export model artifacts for demo
```

The demo model uses the following components:

* `StandardScaler` for the selected 28 features.
* A supervised contrastive feature encoder that maps raw features into a 64-dimensional embedding space.
* A FAISS cosine-similarity index for nearest-neighbor retrieval.
* An online local graph builder for inference-time graph construction.
* A Hierarchical ASAT Attention GraphSAGE model.
* A binary head for benign-vs-attack detection.
* An attack head for attack-type prediction.

---

## 6. Input Features

The demo version uses 28 selected features from CICIoT2023:

```text
IAT
Protocol Type
ICMP
Magnitue
Variance
syn_flag_number
syn_count
AVG
UDP
Tot size
psh_flag_number
Min
Tot sum
Header_Length
TCP
fin_flag_number
ack_flag_number
flow_duration
Max
HTTP
Weight
rst_flag_number
Std
Number
Radius
ack_count
fin_count
Duration
```

Note: The feature name `Magnitue` is kept unchanged because it follows the original feature name used in the dataset/training pipeline.

---

## 7. Model Artifacts

The backend requires an exported artifact folder from the offline training pipeline:

```text
backend/artifacts/hierarchical_asat_gnn_demo_minimal_artifacts/
```

Expected artifact groups:

```text
01_preprocess/
02_encoder/
03_gnn_model/
04_graph_bank/
05_metadata/
06_thresholds_and_rescue/
07_reports/
08_runtime_loader/
demo_master_config.json
requirements_demo.txt
```

Important artifact files:

```text
01_preprocess/feature_scaler_standardscaler.pkl
01_preprocess/label_encoder.pkl
01_preprocess/selected_features.json
01_preprocess/original_feature_columns.json
01_preprocess/selected_idx_from_original_features.npy

02_encoder/encoder_checkpoint.pt
02_encoder/encoder_metadata.json

03_gnn_model/hierarchical_asat_gnn_demo_checkpoint.pt
03_gnn_model/gnn_model_config.json

04_graph_bank/reference_train_embeddings.npy
04_graph_bank/reference_train_labels.npy
04_graph_bank/reference_train_faiss_cosine.index

05_metadata/class_metadata.json
05_metadata/class_mapping_for_demo.csv

06_thresholds_and_rescue/threshold_and_rescue_config.json
```

Model artifacts can be large and should not be pushed directly to GitHub. The repository should contain source code, configuration templates, and documentation only. Large artifacts should be stored separately, for example in Google Drive, cloud storage, or a release artifact repository.

---

## 8. Backend Setup

### 8.1. Create a Python Virtual Environment

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### 8.2. Create the Backend Configuration File

```bash
cp .env.example .env
```

Example `.env`:

```env
APP_HOST=0.0.0.0
APP_PORT=8000

ARTIFACT_DIR=./artifacts/hierarchical_asat_gnn_demo_minimal_artifacts

DEVICE=cpu
ONLINE_K=8

MAX_EVENTS_IN_MEMORY=5000

CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
```

If CUDA is available and PyTorch is properly installed with GPU support, the device can be changed to:

```env
DEVICE=cuda
```

### 8.3. Run the Backend

```bash
chmod +x run_backend.sh
./run_backend.sh
```

Or run it directly:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 8.4. Check Backend Health

```bash
curl http://127.0.0.1:8000/api/health
```

Expected response example:

```json
{
  "status": "ok",
  "model_loaded": true,
  "artifact_dir": "./artifacts/hierarchical_asat_gnn_demo_minimal_artifacts",
  "device": "cpu"
}
```

---

## 9. Frontend Setup

### 9.1. Configure Backend Endpoints

Open:

```text
frontend/config.js
```

If the backend runs on the same machine:

```javascript
window.ASAT_CONFIG = {
  API_BASE: "http://127.0.0.1:8000",
  WS_URL: "ws://127.0.0.1:8000/ws/events"
};
```

If the backend runs on another machine or the host machine in a VMware lab, replace the IP address accordingly:

```javascript
window.ASAT_CONFIG = {
  API_BASE: "http://192.168.116.1:8000",
  WS_URL: "ws://192.168.116.1:8000/ws/events"
};
```

### 9.2. Run the Frontend

```bash
cd frontend

chmod +x run_frontend.sh
./run_frontend.sh
```

Or run it directly with Python’s built-in static server:

```bash
python3 -m http.server 8080
```

Open the dashboard in a browser:

```text
http://127.0.0.1:8080
```

---

## 10. Ubuntu Agent Setup

### 10.1. Install tcpdump

```bash
sudo apt update
sudo apt install -y tcpdump
```

### 10.2. Create a Python Virtual Environment

```bash
cd ubuntu-agent

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### 10.3. Configure the Agent

```bash
cp .env.example .env
```

Example `.env`:

```env
AGENT_ID=ubuntu-victim-01

INTERFACE=ens33
VICTIM_IP=192.168.116.129
ATTACKER_IP=192.168.116.128

BACKEND_URL=http://192.168.116.1:8000/api/agent/flows

PCAP_DIR=/tmp/asat_ids_pcap
WINDOW_SECONDS=3
DELETE_PROCESSED_PCAP=true

TCPDUMP_FILTER=src host 192.168.116.128 and dst host 192.168.116.129 and (tcp or udp or icmp)

TIME_UNIT_MULTIPLIER=1.0

BATCH_SIZE=64
REQUEST_TIMEOUT=3
MAX_RETRIES=3

ENABLE_FEATURE_CSV_LOG=true
AGENT_FEATURE_LOG_CSV=/tmp/asat_agent_features_log.csv

MIN_PACKETS_PER_FLOW=2
LOG_LEVEL=INFO
```

Configuration notes:

* `INTERFACE` is the Ubuntu VM network interface, for example `ens33` or `eth0`.
* `VICTIM_IP` is the Ubuntu victim IP address.
* `ATTACKER_IP` is the Kali attacker IP address in the lab.
* `BACKEND_URL` is the backend endpoint.
* `TCPDUMP_FILTER` should be adjusted depending on the test scenario.
* `AGENT_FEATURE_LOG_CSV` stores extracted features for verification.

Check the Ubuntu network interface:

```bash
ip addr
```

### 10.4. Prepare pcap and Log Permissions

Before running the agent, make sure the pcap directory is writable:

```bash
sudo pkill tcpdump

sudo rm -rf /tmp/asat_ids_pcap
sudo mkdir -p /tmp/asat_ids_pcap
sudo chmod 777 /tmp/asat_ids_pcap

sudo rm -f /tmp/asat_agent_features_log.csv
sudo touch /tmp/asat_agent_features_log.csv
sudo chmod 666 /tmp/asat_agent_features_log.csv
```

### 10.5. Run the Agent

The agent requires packet-capture privileges. Run the virtual-environment Python interpreter with `sudo`:

```bash
cd ubuntu-agent
source .venv/bin/activate

sudo .venv/bin/python run_agent.py
```

Do not use:

```bash
sudo python3 run_agent.py
```

This may use the system Python interpreter instead of the virtual-environment interpreter and can cause missing-package errors.

---

## 11. Controlled Lab Demo Flow

After the backend, frontend, Ubuntu victim, and Kali machine are prepared in the same controlled lab network, the demo can be performed as follows.

### Step 1: Check Network Connectivity

On Ubuntu, check the IP address:

```bash
ip addr
```

From Kali, check connectivity to Ubuntu:

```bash
ping <UBUNTU_IP>
```

From Ubuntu, check the backend:

```bash
curl http://<BACKEND_IP>:8000/api/health
```

### Step 2: Run the Backend

```bash
cd backend
source .venv/bin/activate
./run_backend.sh
```

### Step 3: Run the Frontend

```bash
cd frontend
./run_frontend.sh
```

Open the dashboard:

```text
http://127.0.0.1:8080
```

### Step 4: Run the Ubuntu Agent

```bash
cd ubuntu-agent
source .venv/bin/activate
sudo .venv/bin/python run_agent.py
```

### Step 5: Generate Controlled Lab Traffic

Generate benign traffic first:

```bash
ping <UBUNTU_IP>
curl http://<UBUNTU_IP>
```

Then perform controlled traffic simulation only against the Ubuntu VM that you own and control. Do not send test traffic to public networks or unauthorized systems.

### Step 6: Observe the Dashboard

The dashboard updates:

* Total number of flows.
* Number of benign flows.
* Number of attack flows.
* Predicted attack group.
* Source and destination IP addresses.
* Protocol.
* Packet count.
* Traffic speed.
* Attack score.
* Current network status.
* Last detected attack.
* Recent alerts.

---

## 12. Agent Feature Verification

The agent can write extracted features to a CSV file:

```text
/tmp/asat_agent_features_log.csv
```

Check the file:

```bash
ls -lh /tmp/asat_agent_features_log.csv
head -n 5 /tmp/asat_agent_features_log.csv
tail -f /tmp/asat_agent_features_log.csv
```

This CSV file is useful for checking whether live extracted features follow the same schema and scale as the CICIoT2023 features used during training.

Suggested verification workflow:

```text
Agent CSV log
    ↓
Copy to Colab or an analysis machine
    ↓
Load the trained scaler and selected training features
    ↓
Inverse-transform scaled training features if needed
    ↓
Compare training feature statistics with agent feature statistics
    ↓
Identify unit mismatches or distribution shifts
```

Features that should be checked carefully:

```text
IAT
flow_duration
Duration
Protocol Type
Header_Length
Tot size
Tot sum
AVG
Std
Magnitue
Radius
Variance
Weight
```

---

## 13. Backend API

### 13.1. Health Check

```http
GET /api/health
```

### 13.2. Get Recent Events

```http
GET /api/events?limit=200
```

### 13.3. Get Statistics

```http
GET /api/stats
```

### 13.4. Receive Flows from the Agent

```http
POST /api/agent/flows
```

Example payload:

```json
{
  "agent_id": "ubuntu-victim-01",
  "sent_at": 1790000000.0,
  "num_flows": 1,
  "flows": [
    {
      "flow_key": {
        "first_src_ip": "192.168.116.128",
        "first_dst_ip": "192.168.116.129",
        "first_src_port": 12345,
        "first_dst_port": 80,
        "proto": "TCP"
      },
      "packet_count": 10,
      "window_start_ts": 1790000000.0,
      "window_end_ts": 1790000001.0,
      "features_order": [
        "IAT",
        "Protocol Type",
        "ICMP",
        "Magnitue",
        "Variance",
        "syn_flag_number",
        "syn_count",
        "AVG",
        "UDP",
        "Tot size",
        "psh_flag_number",
        "Min",
        "Tot sum",
        "Header_Length",
        "TCP",
        "fin_flag_number",
        "ack_flag_number",
        "flow_duration",
        "Max",
        "HTTP",
        "Weight",
        "rst_flag_number",
        "Std",
        "Number",
        "Radius",
        "ack_count",
        "fin_count",
        "Duration"
      ],
      "features": [
        0.001,
        6.0,
        0.0,
        10.0,
        0.0,
        1.0,
        10.0,
        60.0,
        0.0,
        600.0,
        0.0,
        60.0,
        600.0,
        400.0,
        1.0,
        0.0,
        0.0,
        1.0,
        60.0,
        1.0,
        0.0,
        0.0,
        0.0,
        10.0,
        0.0,
        0.0,
        0.0,
        64.0
      ]
    }
  ]
}
```

### 13.5. WebSocket Endpoint

```text
/ws/events
```

Whenever the backend finishes predicting a flow, the event is broadcast to connected dashboard clients.

---

## 14. Near Real-Time Behavior

The system operates in a near real-time manner using short pcap capture windows:

```text
tcpdump capture window
    ↓
agent reads new pcap files
    ↓
agent extracts flow features
    ↓
agent sends features to backend
    ↓
backend performs online inference
    ↓
dashboard updates through WebSocket
```

The practical delay depends on the capture window and system load. In a typical lab setup, the end-to-end delay is usually around:

```text
1–3 seconds
```

Because the system processes short pcap windows rather than individual packets instantly, it should be described as a near real-time IDS demo, not a hard real-time packet-level IDS.

---

## 15. Deployment Notes

### 15.1. Do Not Push Large Artifacts to GitHub

The following files and folders should not be committed:

```text
*.pt
*.pkl
*.npy
*.index
*.pcap
*.csv
artifacts/
.venv/
.env
```

Recommended repository contents:

```text
source code
.env.example
requirements.txt
README.md
configuration templates
small sample files if needed
```

### 15.2. Keep the Feature Schema Consistent

The agent and backend must use the same 28-feature order. If the order is incorrect, the scaler and encoder will receive incorrect inputs.

The backend should always verify or reorder incoming features using:

```text
features_order
```

against:

```text
selected_features.json
```

### 15.3. Keep Runtime Model Classes Consistent with Training

The runtime model definitions must match the training-time model definitions.

Important classes include:

```text
FeatureEncoder
EncoderClassifier
ASATAttentionSAGEConv
HierarchicalASATAttentionGraphSAGE
```

If layer names, dimensions, or architecture definitions are changed, checkpoint loading may fail or produce unreliable predictions.

### 15.4. Use a Controlled Lab Environment

All traffic simulation should be performed only inside a controlled lab environment, such as VMware or VirtualBox, and only against machines that you own or are explicitly authorized to test.

---

## 16. Common Issues

### 16.1. `ModuleNotFoundError: No module named 'dotenv'`

This usually happens when the system Python interpreter is used instead of the virtual-environment interpreter.

Correct command:

```bash
cd ubuntu-agent
source .venv/bin/activate
sudo .venv/bin/python run_agent.py
```

Incorrect command:

```bash
sudo python3 run_agent.py
```

---

### 16.2. `tcpdump` Permission Denied

If `tcpdump` fails to write pcap files to `/tmp/asat_ids_pcap`, reset the directory permissions:

```bash
sudo pkill tcpdump

sudo rm -rf /tmp/asat_ids_pcap
sudo mkdir -p /tmp/asat_ids_pcap
sudo chmod 777 /tmp/asat_ids_pcap
```

Then run the agent again:

```bash
sudo .venv/bin/python run_agent.py
```

---

### 16.3. Backend Cannot Load Checkpoints

Check the following paths:

```text
ARTIFACT_DIR
03_gnn_model/hierarchical_asat_gnn_demo_checkpoint.pt
02_encoder/encoder_checkpoint.pt
```

If checkpoint loading fails because of a `state_dict` mismatch, make sure the runtime model classes are identical to the classes used during training.

---

### 16.4. Dashboard Does Not Receive Events

Check:

```text
frontend/config.js
backend server status
WebSocket URL
CORS_ORIGINS in backend .env
agent POST logs
browser console
```

---

### 16.5. Agent Does Not Generate CSV Logs

Check the agent `.env` file:

```env
ENABLE_FEATURE_CSV_LOG=true
AGENT_FEATURE_LOG_CSV=/tmp/asat_agent_features_log.csv
```

Check file permissions:

```bash
ls -lh /tmp/asat_agent_features_log.csv
```

---

### 16.6. Agent Does Not Capture Packets

Check the network interface:

```bash
ip addr
```

Test tcpdump manually:

```bash
sudo tcpdump -i ens33 -nn
```

If the interface is not `ens33`, update `INTERFACE` in the agent `.env` file.

---

## 17. Technologies Used

### Backend

```text
Python
FastAPI
Uvicorn
PyTorch
FAISS
scikit-learn
NumPy
Pandas
Pydantic
```

Depending on the exported model implementation, the backend may also require:

```text
PyTorch Geometric
```

### Ubuntu Agent

```text
Python
tcpdump
Scapy
requests
python-dotenv
```

### Frontend

```text
HTML
CSS
JavaScript
WebSocket
Canvas API
```

---

## 18. Demo Scenarios

The following examples are intended only for a controlled lab environment.

### 18.1. UDP Flood Simulation

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

Example command from Kali:

```bash
sudo hping3 -2 -c 1000 -d 1200 -i u1000 192.168.116.129 -p 5000
```

For a cleaner UDP-only demo, set the agent filter to:

```env
TCPDUMP_FILTER=src host 192.168.116.128 and dst host 192.168.116.129 and udp
MIN_PACKETS_PER_FLOW=10
```

---

### 18.2. TCP SYN Flood Simulation

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

Example command from Kali:

```bash
sudo hping3 -S -c 1000 -i u1000 192.168.116.129 -p 80
```

For a cleaner TCP-only demo, set the agent filter to:

```env
TCPDUMP_FILTER=src host 192.168.116.128 and dst host 192.168.116.129 and tcp
MIN_PACKETS_PER_FLOW=10
```

---

## 19. Dashboard Behavior

During normal traffic, the dashboard displays:

```text
Current status: NORMAL TRAFFIC
Traffic color: Green
Traffic chart: Normal baseline
Attack score: Low or stable
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

The last detected attack is still preserved in:

* Last detected attack
* Realtime alerts
* Latest flow predictions

This design separates the current network state from historical attack evidence, which makes the dashboard easier to explain during a live IDS demonstration.

---

## 20. Conclusion

This project implements a GNN-based network intrusion detection pipeline from offline model training to near real-time lab demonstration. The model is trained on CICIoT2023 and exported as runtime artifacts so that the backend can perform online inference without retraining.

The demo architecture visualizes the full IDS workflow:

```text
Lab traffic
→ feature extraction
→ model inference
→ realtime dashboard
```

The system is suitable for academic research, graduation thesis work, and controlled demonstrations of how GNN-based models can be applied to network intrusion detection.

## License

This project is released under a custom non-commercial license. The source code and associated materials may be used for personal, educational, academic, and non-commercial research purposes only.

Commercial use, redistribution, sublicensing, product integration, or paid deployment is not allowed without prior written permission from the author.

For commercial permission, please contact:

phucphuc2004444@gmail.com

See the [LICENSE](LICENSE) file for full terms.
