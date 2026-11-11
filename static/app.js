const state = {
  sensors: [],
  alerts: [],
  history: [],
  mqttConnected: false,
};

const sensorCardsEl = document.getElementById('sensorCards');
const alertListEl = document.getElementById('alertList');
const sensorTableBody = document.getElementById('sensorTableBody');
const systemStatus = document.getElementById('systemStatus');
const chartCanvas = document.getElementById('telemetryChart');
const chartCtx = chartCanvas.getContext('2d');

function utcLabel(isoString) {
  const date = new Date(isoString);
  return Number.isNaN(date.getTime()) ? 'now' : date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function renderCards() {
  sensorCardsEl.innerHTML = state.sensors.map((sensor) => `
    <article class="sensor-card">
      <div class="meta">
        <span class="sensor-name">${sensor.name}</span>
        <span class="badge ${sensor.status}">${sensor.status}</span>
      </div>
      <div class="metric-row"><span>Temperature</span><strong>${sensor.temperature.toFixed(1)}°C</strong></div>
      <div class="metric-row"><span>Pressure</span><strong>${sensor.pressure.toFixed(1)} psi</strong></div>
      <div class="metric-row"><span>Vibration</span><strong>${sensor.vibration.toFixed(2)} mm/s</strong></div>
      <div class="metric-row"><span>Humidity</span><strong>${sensor.humidity.toFixed(1)}%</strong></div>
    </article>
  `).join('');
}

function renderAlerts() {
  if (!state.alerts.length) {
    alertListEl.innerHTML = '<li class="alert-item">No active alerts.</li>';
    return;
  }

  alertListEl.innerHTML = state.alerts.map((alert) => `
    <li class="alert-item ${alert.level}">
      <strong>${alert.sensor}</strong><br />
      ${alert.message} · ${alert.level.toUpperCase()}
    </li>
  `).join('');
}

function renderTable() {
  sensorTableBody.innerHTML = state.history.slice(0, 8).map((reading) => `
    <tr>
      <td>${reading.name}</td>
      <td>${reading.temperature.toFixed(1)}</td>
      <td>${reading.pressure.toFixed(1)}</td>
      <td>${reading.vibration.toFixed(2)}</td>
      <td>${reading.humidity.toFixed(1)}</td>
      <td><span class="badge ${reading.status}">${reading.status}</span></td>
      <td>${utcLabel(reading.timestamp)}</td>
    </tr>
  `).join('');
}

function renderChart() {
  const series = state.history.slice(0, 12).reverse();
  const width = chartCanvas.width;
  const height = chartCanvas.height;
  const padding = 24;
  const minVal = 0;
  const maxVal = 140;

  chartCtx.clearRect(0, 0, width, height);
  chartCtx.strokeStyle = '#2a3d5d';
  chartCtx.lineWidth = 1;
  chartCtx.beginPath();
  chartCtx.moveTo(padding, padding);
  chartCtx.lineTo(padding, height - padding);
  chartCtx.lineTo(width - padding, height - padding);
  chartCtx.stroke();

  if (!series.length) return;

  const pts = series.map((entry, index) => {
    const x = padding + (index * (width - padding * 2)) / Math.max(series.length - 1, 1);
    const y = height - padding - ((entry.temperature - minVal) / (maxVal - minVal || 1)) * (height - padding * 2);
    return { x, y };
  });

  chartCtx.beginPath();
  pts.forEach((point, index) => {
    if (index === 0) chartCtx.moveTo(point.x, point.y);
    else chartCtx.lineTo(point.x, point.y);
  });
  chartCtx.strokeStyle = '#60a5fa';
  chartCtx.lineWidth = 2;
  chartCtx.stroke();

  pts.forEach((point) => {
    chartCtx.beginPath();
    chartCtx.arc(point.x, point.y, 2.5, 0, 2 * Math.PI);
    chartCtx.fillStyle = '#93c5fd';
    chartCtx.fill();
  });
}

function render() {
  renderCards();
  renderAlerts();
  renderTable();
  renderChart();

  const badge = state.mqttConnected ? 'MQTT connected' : 'MQTT offline';
  systemStatus.textContent = badge;
  systemStatus.style.background = state.mqttConnected ? 'rgba(34, 197, 94, 0.15)' : 'rgba(96, 165, 250, 0.15)';
  systemStatus.style.borderColor = state.mqttConnected ? 'rgba(34, 197, 94, 0.4)' : 'rgba(96, 165, 250, 0.4)';
}

function applySnapshot(data) {
  state.sensors = data.sensors || [];
  state.alerts = data.alerts || [];
  state.history = data.history || [];
  state.mqttConnected = !!data.mqtt_connected;
  render();
}

async function fetchSnapshot() {
  try {
    const res = await fetch('/api/snapshot');
    const data = await res.json();
    applySnapshot(data);
  } catch (err) {
    console.error(err);
  }
}

function connectWebSocket() {
  const socket = new WebSocket(`ws://${window.location.host}/ws`);

  socket.onopen = () => {
    console.log('WebSocket connected');
  };

  socket.onmessage = (event) => {
    const message = JSON.parse(event.data);

    if (message.type === 'update') {
      applySnapshot(message.data);
    }

    if (message.type === 'mqtt_status') {
      if (message.status === 'online') {
        state.mqttConnected = true;
        hideMqttPopup();
      }
    

      if (message.status === 'offline') {
        state.mqttConnected = false;
        showMqttPopup();
      }
    }

  };
  

  

  socket.onclose = () => {
    setTimeout(connectWebSocket, 2500);
  };


}

function hideMqttPopup() {
  const popup = document.getElementById('mqttPopup');

  if (popup) {
    popup.remove();
  }
}


function showMqttPopup() {
  let popup = document.getElementById('mqttPopup');

  if (!popup) {
    popup = document.createElement('div');
    popup.id = 'mqttPopup';
    popup.textContent = '⚠ MQTT is offline';
    document.body.appendChild(popup);
  }
  else
  {
    popup.textContent = 'MQTT is not connected';
  }

}

fetchSnapshot();
connectWebSocket();
setInterval(fetchSnapshot, 5000);
c