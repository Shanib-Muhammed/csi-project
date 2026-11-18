const $ = (id) => document.getElementById(id);
const signalHistory = [];
let lastState = {};

function setText(id, value) { $(id).textContent = value; }

function updateDashboard(state) {
  lastState = state;
  const online = !!state.connected;
  $("connectionDot").parentElement.classList.toggle("online", online);
  setText("connectionText", online ? "RECEIVER ONLINE" : "RECEIVER OFFLINE");
  setText("presence", state.status || "WAITING");
  setText("presenceHint", state.message || "Waiting for data");
  setText("motion", Number(state.motion_score || 0).toFixed(1));
  setText("signal", Number(state.signal_score || 0).toFixed(1));
  setText("packets", Number(state.packet_count || 0).toLocaleString());
  setText("source", state.source === "real-csi" ? "REAL CSI DATA" : "NO LIVE SOURCE");
  setText("rssi", state.connected ? String(state.rssi) + " dBm" : "— dBm");
  setText("channel", state.channel || "—");
  setText("subcarriers", state.subcarriers || "—");
  setText("amplitude", Number(state.amplitude_mean || 0).toFixed(1));
  setText("fieldState", state.calibrated ? (state.presence ? "PRESENCE DETECTED" : "BASELINE ACTIVE") : "NOT CALIBRATED");
  setText("calibrationHint", state.calibrated ? "Baseline ready. Recalibrate after moving either board or changing the room." : "Keep the sensing area empty and still while calibration collects samples.");
  drawHeatmap(Number(state.heat || 0), !!state.presence);
  signalHistory.push(Number(state.amplitude_mean || 0));
  if (signalHistory.length > 100) signalHistory.shift();
  drawChart();
}

function connectSocket() {
  const scheme = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(scheme + "://" + location.host + "/ws");
  socket.onmessage = (event) => {
    try { updateDashboard(JSON.parse(event.data)); } catch (error) { console.error(error); }
  };
  socket.onclose = () => setTimeout(connectSocket, 1500);
  socket.onerror = () => socket.close();
}

function drawHeatmap(level, present) {
  const canvas = $("heatmap"), rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.floor(rect.width * dpr));
  canvas.height = Math.max(1, Math.floor(rect.height * dpr));
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  const w = rect.width, h = rect.height;
  ctx.fillStyle = "#061329"; ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = "rgba(76,157,190,.16)"; ctx.lineWidth = 1;
  for (let x = 0; x < w; x += 28) { ctx.beginPath(); ctx.moveTo(x,0); ctx.lineTo(x,h); ctx.stroke(); }
  for (let y = 0; y < h; y += 28) { ctx.beginPath(); ctx.moveTo(0,y); ctx.lineTo(w,y); ctx.stroke(); }
  // A single RF link cannot localize an object in 2D. This field visualizes
  // measured deviation strength in a fixed zone; it is not a coordinate map.
  const intensity = Math.max(0, Math.min(1, level));
  const cx = w * 0.5, cy = h * 0.53;
  const radius = Math.min(w,h) * (present ? 0.31 : 0.12 + intensity * 0.12);
  const gradient = ctx.createRadialGradient(cx,cy,4,cx,cy,radius);
  gradient.addColorStop(0, "rgba(255,65,45," + (0.15 + intensity * 0.75) + ")");
  gradient.addColorStop(.35, "rgba(255,191,65," + (intensity * .55) + ")");
  gradient.addColorStop(1, "rgba(30,140,220,0)");
  ctx.fillStyle = gradient; ctx.fillRect(0,0,w,h);
  ctx.strokeStyle = "rgba(87,226,222,.7)"; ctx.lineWidth = 1.5;
  ctx.strokeRect(w*.12,h*.2,w*.76,h*.62);
  ctx.fillStyle = "#a8d4e7"; ctx.font = "11px Segoe UI";
  ctx.fillText("TRANSMITTER  ⇄  RECEIVER LINK", w*.12, h*.16);
  ctx.fillStyle = present ? "#ffb36b" : "#7ee6d8";
  ctx.beginPath(); ctx.arc(cx,cy,5 + intensity*8,0,Math.PI*2); ctx.fill();
}

function drawChart() {
  const canvas = $("signalChart"), rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.max(1, Math.floor(rect.width*dpr));
  canvas.height = Math.max(1, Math.floor(rect.height*dpr));
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr,dpr);
  const w=rect.width,h=rect.height;
  ctx.clearRect(0,0,w,h); ctx.strokeStyle="rgba(100,160,190,.18)";
  for(let y=25;y<h;y+=30){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(w,y);ctx.stroke();}
  if(signalHistory.length<2)return;
  const max=Math.max(1,...signalHistory), min=Math.min(0,...signalHistory), span=Math.max(1,max-min);
  ctx.beginPath();
  signalHistory.forEach((v,i)=>{const x=i/(signalHistory.length-1)*w;const y=h-12-((v-min)/span)*(h-24);if(i)ctx.lineTo(x,y);else ctx.moveTo(x,y);});
  ctx.strokeStyle="#71efbd";ctx.lineWidth=2;ctx.stroke();
}

async function loadEvents() {
  try {
    const response = await fetch("/api/events");
    const events = await response.json();
    $("events").innerHTML = events.length ? events.map(e =>
      '<div class="event"><span><b>' + escapeHtml(e.status) + '</b> · ' + escapeHtml(e.event_type) +
      '</span><span>' + escapeHtml(e.created_at) + '</span></div>'
    ).join("") : '<p class="muted">No detection transitions recorded yet.</p>';
  } catch (_) {}
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}

$("calibrate").addEventListener("click", async () => {
  $("calibrate").disabled = true;
  try { await fetch("/api/calibrate", {method:"POST"}); }
  finally { setTimeout(() => $("calibrate").disabled = false, 1200); }
});
$("refreshEvents").addEventListener("click", loadEvents);
window.addEventListener("resize", () => drawHeatmap(Number(lastState.heat||0),!!lastState.presence));
connectSocket(); loadEvents(); setInterval(loadEvents, 8000);
