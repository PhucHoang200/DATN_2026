const API_BASE = window.ASAT_CONFIG.API_BASE;
const WS_URL = window.ASAT_CONFIG.WS_URL;

const AUTO_NORMAL_AFTER_MS = 10000;

let events = [];
let stats = {
  total: 0,
  attack_count: 0,
  benign_count: 0,
  by_class: {}
};

let lastAttackEvent = null;
let lastAttackAt = 0;

const headerStatus = document.getElementById("headerStatus");
const headerTime = document.getElementById("headerTime");

const totalFlows = document.getElementById("totalFlows");
const attackFlows = document.getElementById("attackFlows");
const benignFlows = document.getElementById("benignFlows");
const topClass = document.getElementById("topClass");

const networkStatusCard = document.getElementById("networkStatusCard");
const networkStatusText = document.getElementById("networkStatusText");
const networkStatusDesc = document.getElementById("networkStatusDesc");

const trafficChartPanel = document.getElementById("trafficChartPanel");
const chartSubtitle = document.getElementById("chartSubtitle");
const latestAttackScore = document.getElementById("latestAttackScore");
const latestProtocol = document.getElementById("latestProtocol");
const latestSpeed = document.getElementById("latestSpeed");

const latestFlowCard = document.getElementById("latestFlowCard");
const lastAttackCard = document.getElementById("lastAttackCard");
const classBars = document.getElementById("classBars");
const alertList = document.getElementById("alertList");
const eventsTable = document.getElementById("eventsTable");

const trafficChart = document.getElementById("trafficChart");
const ctx = trafficChart.getContext("2d");

let chartPoints = [];

function formatDateTime(ts) {
  if (!ts) return "-";

  try {
    const d = new Date(ts * 1000);

    const dd = String(d.getDate()).padStart(2, "0");
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const yyyy = d.getFullYear();

    const hh = String(d.getHours()).padStart(2, "0");
    const mi = String(d.getMinutes()).padStart(2, "0");
    const ss = String(d.getSeconds()).padStart(2, "0");

    return `${dd}/${mm}/${yyyy} ${hh}:${mi}:${ss}`;
  } catch {
    return "-";
  }
}

function pct(x) {
  if (x === undefined || x === null || Number.isNaN(Number(x))) return "-";
  return `${(Number(x) * 100).toFixed(1)}%`;
}

function safeText(value, fallback = "-") {
  if (value === undefined || value === null || value === "") return fallback;
  return String(value);
}

function normalizeAttackGroup(value) {
  const text = safeText(value, "Unknown");

  if (text === "Benign") return "Benign";
  if (text.startsWith("DDoS")) return "DDoS";
  if (text.startsWith("DoS")) return "DoS";
  if (text.startsWith("Recon")) return "Recon";
  if (text.startsWith("Mirai")) return "Mirai";
  if (text.includes("Spoof")) return "Spoofing";
  if (text.includes("Brute")) return "Brute Force";

  if (
    text.includes("Injection") ||
    text.includes("XSS") ||
    text.includes("Backdoor") ||
    text.includes("Uploading") ||
    text.includes("Browser")
  ) {
    return "Web-Based";
  }

  return text;
}

function getAttackType(event) {
  if (!event || !event.is_attack) return "Benign";
  return normalizeAttackGroup(event.attack_type || event.class_name || "Unknown");
}

function getSource(event) {
  const ip = event?.source_ip || event?.flow_key?.first_src_ip || event?.flow_key?.src_ip || "-";
  const port = event?.source_port || event?.flow_key?.first_src_port || event?.flow_key?.src_port || "";

  return port ? `${ip}:${port}` : ip;
}

function getDestination(event) {
  const ip = event?.destination_ip || event?.flow_key?.first_dst_ip || event?.flow_key?.dst_ip || "-";
  const port = event?.destination_port || event?.flow_key?.first_dst_port || event?.flow_key?.dst_port || "";

  return port ? `${ip}:${port}` : ip;
}

function getProtocol(event) {
  return safeText(
    event?.protocol ||
    event?.observed_protocol ||
    event?.flow_key?.proto ||
    "-",
    "-"
  ).toUpperCase();
}

function getTotalPackets(event) {
  return event?.total_packets || event?.packet_count || 0;
}

function getSpeedValue(event) {
  const pps = Number(event?.packets_per_second || 0);
  if (!Number.isFinite(pps) || pps <= 0) return 0;
  return pps;
}

function getSpeed(event) {
  const pps = getSpeedValue(event);

  if (pps <= 0) return "-";

  if (pps >= 1000) {
    return `${(pps / 1000).toFixed(2)} kpps`;
  }

  return `${pps.toFixed(1)} pkt/s`;
}

function isAttackActive() {
  return Date.now() - lastAttackAt <= AUTO_NORMAL_AFTER_MS;
}

function computeLocalStats() {
  const local = {
    total: events.length,
    attack_count: 0,
    benign_count: 0,
    by_attack_type: {}
  };

  for (const event of events) {
    if (event.is_attack) {
      local.attack_count += 1;
    } else {
      local.benign_count += 1;
    }

    const attackType = getAttackType(event);
    local.by_attack_type[attackType] = (local.by_attack_type[attackType] || 0) + 1;
  }

  return local;
}

function resizeChart() {
  const rect = trafficChart.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;

  trafficChart.width = Math.max(1, Math.floor(rect.width * dpr));
  trafficChart.height = Math.max(1, Math.floor(rect.height * dpr));

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}

function pushChartPoint(value, isAttack = false) {
  const now = Date.now();

  chartPoints.push({
    ts: now,
    value,
    isAttack
  });

  const windowMs = 60000;
  chartPoints = chartPoints.filter((p) => now - p.ts <= windowMs);
}

function pushNormalSyntheticPoint() {
  const base = 20 + Math.sin(Date.now() / 1200) * 7;
  const jitter = Math.random() * 10;
  pushChartPoint(Math.max(4, base + jitter), false);
}

function pushEventChartPoint(event) {
  const pps = getSpeedValue(event);
  const packets = Number(getTotalPackets(event) || 0);

  let value = pps > 0 ? pps : packets;

  if (!Number.isFinite(value) || value <= 0) {
    value = event.is_attack ? 120 + Math.random() * 120 : 18 + Math.random() * 18;
  }

  if (event.is_attack) {
    value = Math.max(value, 120 + Math.random() * 240);
  }

  pushChartPoint(value, Boolean(event.is_attack));
}

function drawTrafficChart() {
  const rect = trafficChart.getBoundingClientRect();
  const width = rect.width || 800;
  const height = rect.height || 300;

  ctx.clearRect(0, 0, width, height);

  const now = Date.now();
  const windowMs = 60000;

  const visible = chartPoints.filter((p) => now - p.ts <= windowMs);

  if (!visible.length) {
    requestAnimationFrame(drawTrafficChart);
    return;
  }

  const maxValue = Math.max(60, ...visible.map((p) => p.value)) * 1.18;
  const padLeft = 42;
  const padRight = 18;
  const padTop = 22;
  const padBottom = 34;

  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;

  ctx.lineWidth = 1;
  ctx.strokeStyle = "rgba(100, 116, 139, 0.20)";

  for (let i = 0; i <= 4; i += 1) {
    const y = padTop + (chartH / 4) * i;

    ctx.beginPath();
    ctx.moveTo(padLeft, y);
    ctx.lineTo(width - padRight, y);
    ctx.stroke();
  }

  ctx.fillStyle = "#64748b";
  ctx.font = "12px Arial";

  for (let i = 0; i <= 4; i += 1) {
    const value = Math.round(maxValue - (maxValue / 4) * i);
    const y = padTop + (chartH / 4) * i + 4;
    ctx.fillText(String(value), 8, y);
  }

  function xFor(p) {
    const age = now - p.ts;
    return padLeft + chartW * (1 - age / windowMs);
  }

  function yFor(p) {
    return padTop + chartH * (1 - Math.min(1, p.value / maxValue));
  }

  const normalPoints = visible.filter((p) => !p.isAttack);
  const attackPoints = visible.filter((p) => p.isAttack);

  if (normalPoints.length >= 2) {
    ctx.beginPath();

    normalPoints.forEach((p, idx) => {
      const x = xFor(p);
      const y = yFor(p);

      if (idx === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });

    ctx.lineWidth = 3;
    ctx.strokeStyle = "#16a34a";
    ctx.stroke();
  }

  if (attackPoints.length >= 1) {
    for (const p of attackPoints) {
      const x = xFor(p);
      const y = yFor(p);

      ctx.beginPath();
      ctx.arc(x, y, 4.5, 0, Math.PI * 2);
      ctx.fillStyle = "#dc2626";
      ctx.fill();

      ctx.beginPath();
      ctx.arc(x, y, 9, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(220, 38, 38, 0.30)";
      ctx.lineWidth = 3;
      ctx.stroke();
    }
  }

  ctx.fillStyle = "#64748b";
  ctx.font = "12px Arial";
  ctx.fillText("60s ago", padLeft, height - 10);
  ctx.fillText("now", width - padRight - 24, height - 10);

  requestAnimationFrame(drawTrafficChart);
}

function renderLatestFlowCard(event) {
  if (!event) {
    latestFlowCard.innerHTML = `<div class="empty-state">Chưa có flow prediction nào.</div>`;
    return;
  }

  const attackType = getAttackType(event);
  const source = getSource(event);
  const destination = getDestination(event);
  const protocol = getProtocol(event);
  const speed = getSpeed(event);

  latestFlowCard.innerHTML = `
    <div class="latest-flow-box">
      <div class="latest-flow-title ${event.is_attack ? "attack" : "benign"}">
        ${safeText(attackType)}
      </div>
      <div class="latest-flow-meta">
        <b>${formatDateTime(event.received_at)}</b><br />
        ${source} → ${destination}<br />
        Protocol=${protocol} · Packets=${safeText(getTotalPackets(event), "0")} · Speed=${speed}
      </div>
    </div>
  `;
}

function renderLastAttackCard() {
  if (!lastAttackEvent) {
    lastAttackCard.innerHTML = `<div class="empty-state">Chưa phát hiện tấn công.</div>`;
    return;
  }

  const attackType = getAttackType(lastAttackEvent);
  const source = getSource(lastAttackEvent);
  const destination = getDestination(lastAttackEvent);
  const protocol = getProtocol(lastAttackEvent);
  const speed = getSpeed(lastAttackEvent);

  lastAttackCard.innerHTML = `
    <div class="latest-flow-box">
      <div class="latest-flow-title attack">
        ${safeText(attackType)}
      </div>
      <div class="latest-flow-meta">
        <b>${formatDateTime(lastAttackEvent.received_at)}</b><br />
        ${source} → ${destination}<br />
        Protocol=${protocol} · Packets=${safeText(getTotalPackets(lastAttackEvent), "0")} · Speed=${speed}<br />
        Attack score=${pct(lastAttackEvent.attack_probability)}
      </div>
    </div>
  `;
}

function updateNetworkStatusView() {
  const latest = events[0];
  const activeAttack = isAttackActive();

  renderLatestFlowCard(latest);
  renderLastAttackCard();

  if (!latest) {
    headerStatus.textContent = "Normal Traffic";
    headerTime.textContent = "-";

    networkStatusCard.className = "status-card normal";
    trafficChartPanel.className = "traffic-chart-panel normal";

    networkStatusText.textContent = "NORMAL TRAFFIC";
    networkStatusDesc.textContent = "Hệ thống đang giám sát lưu lượng mạng theo thời gian thực.";
    chartSubtitle.textContent = "Normal traffic is being monitored continuously";

    latestAttackScore.textContent = "0.0%";
    latestProtocol.textContent = "-";
    latestSpeed.textContent = "-";
    return;
  }

  headerTime.textContent = formatDateTime(latest.received_at);
  latestAttackScore.textContent = pct(latest.attack_probability || 0);
  latestProtocol.textContent = getProtocol(latest);
  latestSpeed.textContent = getSpeed(latest);

  if (activeAttack && lastAttackEvent) {
    const attackType = getAttackType(lastAttackEvent);
    const remaining = Math.max(
      0,
      Math.ceil((AUTO_NORMAL_AFTER_MS - (Date.now() - lastAttackAt)) / 1000)
    );

    headerStatus.textContent = "Attack Detected";

    networkStatusCard.className = "status-card critical";
    trafficChartPanel.className = "traffic-chart-panel attack";

    networkStatusText.textContent = "ATTACK DETECTED";
    networkStatusDesc.textContent = `Phát hiện nhóm tấn công ${attackType}. Hệ thống sẽ tự trở về Normal nếu không có log tấn công mới trong ${remaining}s.`;
    chartSubtitle.textContent = "Attack traffic has caused a visible spike in current network flow";
    return;
  }

  headerStatus.textContent = "Normal Traffic";

  networkStatusCard.className = "status-card normal";
  trafficChartPanel.className = "traffic-chart-panel normal";

  networkStatusText.textContent = "NORMAL TRAFFIC";
  networkStatusDesc.textContent = lastAttackEvent
    ? "Không còn log tấn công mới trong 10 giây. Trạng thái hiện tại đã trở về bình thường."
    : "Luồng mới nhất đang được nhận diện là bình thường.";

  chartSubtitle.textContent = "Normal traffic is being monitored continuously";
}

function updateStatsView() {
  const local = computeLocalStats();

  totalFlows.textContent = stats.total || local.total || 0;
  attackFlows.textContent = stats.attack_count || local.attack_count || 0;
  benignFlows.textContent = stats.benign_count || local.benign_count || 0;

  const entries = Object.entries(local.by_attack_type || {}).sort((a, b) => b[1] - a[1]);

  topClass.textContent = entries.length ? entries[0][0] : "-";

  classBars.innerHTML = "";

  if (!entries.length) {
    classBars.innerHTML = `
      <div class="empty-state">
        Chưa có dữ liệu. Dashboard sẽ tự cập nhật khi agent gửi flow mới.
      </div>
    `;
    return;
  }

  const maxCount = entries[0][1] || 1;

  for (const [attackType, count] of entries.slice(0, 8)) {
    const row = document.createElement("div");
    row.className = "bar-row";

    const name = document.createElement("div");
    name.className = "bar-name";
    name.title = attackType;
    name.textContent = attackType;

    const bg = document.createElement("div");
    bg.className = "bar-bg";

    const fill = document.createElement("div");
    fill.className = `bar-fill ${attackType === "Benign" ? "benign" : "attack"}`;
    fill.style.width = `${Math.max(4, (count / maxCount) * 100)}%`;

    bg.appendChild(fill);

    const c = document.createElement("div");
    c.className = "bar-count";
    c.textContent = count;

    row.appendChild(name);
    row.appendChild(bg);
    row.appendChild(c);

    classBars.appendChild(row);
  }
}

function renderAlerts() {
  alertList.innerHTML = "";

  const topEvents = events.slice(0, 10);

  if (!topEvents.length) {
    alertList.innerHTML = `
      <div class="alert">
        <div class="title">No events yet</div>
        <div class="meta">Waiting for Python agent data...</div>
      </div>
    `;
    return;
  }

  for (const event of topEvents) {
    const attackType = getAttackType(event);
    const source = getSource(event);
    const destination = getDestination(event);
    const protocol = getProtocol(event);
    const totalPackets = getTotalPackets(event);
    const speed = getSpeed(event);

    const div = document.createElement("div");
    div.className = `alert ${event.is_attack ? "attack" : ""}`;

    div.innerHTML = `
      <div class="title">
        #${safeText(event.event_id)} — ${safeText(attackType)}
      </div>

      <div class="meta">
        ${formatDateTime(event.received_at)}
        &nbsp;|&nbsp;
        ${source} → ${destination}
        &nbsp;|&nbsp;
        ${protocol}
        &nbsp;|&nbsp;
        packets=${safeText(totalPackets, "0")}
        &nbsp;|&nbsp;
        speed=${speed}
        &nbsp;|&nbsp;
        attack=${pct(event.attack_probability)}
      </div>
    `;

    alertList.appendChild(div);
  }
}

function renderTable() {
  eventsTable.innerHTML = "";

  if (!events.length) {
    eventsTable.innerHTML = `
      <tr>
        <td colspan="9">
          <div class="empty-state">
            Chưa có flow prediction nào. Hãy kiểm tra Python agent và backend API.
          </div>
        </td>
      </tr>
    `;
    return;
  }

  for (const event of events.slice(0, 200)) {
    const attackType = getAttackType(event);
    const source = getSource(event);
    const destination = getDestination(event);
    const protocol = getProtocol(event);
    const totalPackets = getTotalPackets(event);
    const speed = getSpeed(event);

    const tr = document.createElement("tr");
    tr.className = event.is_attack ? "attack-row" : "benign-row";

    tr.innerHTML = `
      <td>${safeText(event.event_id)}</td>
      <td>${formatDateTime(event.received_at)}</td>
      <td>
        <span class="badge ${event.is_attack ? "attack" : "benign"}">
          ${safeText(attackType)}
        </span>
      </td>
      <td>${source}</td>
      <td>${destination}</td>
      <td><span class="protocol-pill">${protocol}</span></td>
      <td>${safeText(totalPackets, "0")}</td>
      <td>${speed}</td>
      <td>${pct(event.attack_probability)}</td>
    `;

    eventsTable.appendChild(tr);
  }
}

function renderAll() {
  updateNetworkStatusView();
  updateStatsView();
  renderAlerts();
  renderTable();
}

function ingestEvent(event) {
  events.unshift(event);
  events = events.slice(0, 500);

  pushEventChartPoint(event);

  if (event.is_attack) {
    lastAttackEvent = event;
    lastAttackAt = Date.now();
  }

  renderAll();
}

async function loadEvents() {
  try {
    const res = await fetch(`${API_BASE}/api/events?limit=300`);

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }

    const data = await res.json();

    events = data.events || [];
    stats = data.stats || stats;

    const latestAttack = events.find((event) => event.is_attack);
    if (latestAttack) {
      lastAttackEvent = latestAttack;
      lastAttackAt = Date.now() - AUTO_NORMAL_AFTER_MS - 1;
    }

    for (const event of events.slice(0, 30).reverse()) {
      pushEventChartPoint(event);
    }

    renderAll();
  } catch (err) {
    console.error("Failed to load events:", err);
  }
}

function connectWebSocket() {
  const ws = new WebSocket(WS_URL);

  ws.onclose = () => {
    setTimeout(connectWebSocket, 2000);
  };

  ws.onerror = () => {
    try {
      ws.close();
    } catch {
      // ignored
    }
  };

  ws.onmessage = (msg) => {
    try {
      const data = JSON.parse(msg.data);

      if (data.type === "prediction") {
        const event = data.event;

        ingestEvent(event);

        if (data.stats) {
          stats = data.stats;
        }

        renderAll();
      }

      if (data.type === "connected") {
        if (data.stats) {
          stats = data.stats;
          renderAll();
        }
      }
    } catch (err) {
      console.error("Bad WS message:", err);
    }
  };
}

window.addEventListener("resize", resizeChart);

setInterval(() => {
  pushNormalSyntheticPoint();
  renderAll();
}, 1000);

setInterval(() => {
  renderAll();
}, 500);

resizeChart();
drawTrafficChart();

loadEvents();
connectWebSocket();