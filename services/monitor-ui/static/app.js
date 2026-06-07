/** CSMP Monitor UI — Leaflet map consuming Monitor API (Phase 6, pt-BR). */

const CHAPECO_CENTER = [-27.098, -52.618];
const REFRESH_MS = 30_000;

const SIGNAL_PT = {
  GREEN: "Verde",
  RED: "Vermelho",
  YELLOW: "Amarelo",
  FLASHING_YELLOW: "Amarelo intermitente",
  UNKNOWN: "Desconhecido",
};

const FRESHNESS_PT = {
  FRESH: "Dados atualizados",
  STALE: "Dados desatualizados",
  UNKNOWN: "Sem dados",
};

const map = L.map("map", { zoomControl: true }).setView(CHAPECO_CENTER, 13);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  maxZoom: 19,
}).addTo(map);

const markerCluster = L.markerClusterGroup({
  showCoverageOnHover: false,
  maxClusterRadius: 45,
});
map.addLayer(markerCluster);

const markers = new Map();
let activeId = null;
let currentItems = [];

const healthBadge = document.getElementById("health-badge");
const countLabel = document.getElementById("intersection-count");
const listEl = document.getElementById("intersection-list");
const bottleneckOnly = document.getElementById("bottleneck-only");
const refreshBtn = document.getElementById("refresh-btn");

const SIGNAL_COLORS = {
  GREEN: "#22c55e",
  RED: "#ef4444",
  YELLOW: "#eab308",
  FLASHING_YELLOW: "#f97316",
  UNKNOWN: "#94a3b8",
};

function markerOptions(item) {
  const bottleneck = item.is_severe_bottleneck;
  return {
    radius: bottleneck ? 11 : 8,
    fillColor: SIGNAL_COLORS[item.signal_state] || SIGNAL_COLORS.UNKNOWN,
    color: bottleneck ? "#dc2626" : "#ffffff",
    weight: bottleneck ? 3 : 2,
    fillOpacity: 0.95,
    className: bottleneck ? "bottleneck-marker" : "signal-marker",
  };
}

function popupHtml(item) {
  const name = item.display_name || item.intersection_id;
  if (item.window_end === "1970-01-01T00:00:00Z") {
    return `
      <div class="popup-title">${name}</div>
      <div>Sem telemetria recente</div>
      <div class="popup-meta">Semáforo cadastrado (OpenStreetMap)</div>
    `;
  }
  const state = SIGNAL_PT[item.signal_state] || item.signal_state;
  const stop = item.avg_stop_duration_seconds?.toFixed(1) ?? "—";
  const speed = item.avg_vehicle_speed_kmh?.toFixed(1) ?? "—";
  const bottleneck = item.is_severe_bottleneck
    ? '<div class="popup-bottleneck">⚠ Gargalo severo</div>'
    : "";
  return `
    <div class="popup-title">${name}</div>
    <div>Sinal: <strong>${state}</strong></div>
    <div>Parada média: ${stop}s</div>
    <div>Velocidade: ${speed} km/h</div>
    ${bottleneck}
  `;
}

function renderList(items) {
  listEl.replaceChildren();
  const label = items.length === 1 ? "1 cruzamento" : `${items.length} cruzamentos`;
  countLabel.textContent = label;

  for (const item of items) {
    const li = document.createElement("li");
    li.className = "intersection-item";
    if (item.is_severe_bottleneck) li.classList.add("bottleneck");
    if (item.intersection_id === activeId) li.classList.add("active");

    const name = item.display_name || item.intersection_id;
    const state =
      item.window_end === "1970-01-01T00:00:00Z"
        ? "Sem telemetria"
        : SIGNAL_PT[item.signal_state] || item.signal_state;
    const tag = item.is_severe_bottleneck
      ? '<span class="bottleneck-tag">Gargalo</span>'
      : "";

    li.innerHTML = `
      <div class="item-title">${name}</div>
      <div class="item-meta">${state} · ${stopLabel(item)} · ${speedLabel(item)}</div>
      ${tag}
    `;

    li.addEventListener("click", () => focusIntersection(item.intersection_id));
    listEl.appendChild(li);
  }
}

function stopLabel(item) {
  const v = item.avg_stop_duration_seconds;
  return v != null ? `${v.toFixed(0)}s parada` : "—";
}

function speedLabel(item) {
  const v = item.avg_vehicle_speed_kmh;
  return v != null ? `${v.toFixed(0)} km/h` : "—";
}

function focusIntersection(id) {
  activeId = id;
  renderList(currentItems);
  const marker = markers.get(id);
  if (marker) {
    map.setView(marker.getLatLng(), Math.max(map.getZoom(), 15));
    marker.openPopup();
  }
}

function updateMarkers(items) {
  const seen = new Set();
  const bounds = [];

  for (const item of items) {
    if (!item.location) continue;
    seen.add(item.intersection_id);
    const latlng = [item.location.latitude, item.location.longitude];
    bounds.push(latlng);

    let marker = markers.get(item.intersection_id);
    if (!marker) {
      marker = L.circleMarker(latlng, markerOptions(item));
      marker.on("click", () => focusIntersection(item.intersection_id));
      markerCluster.addLayer(marker);
      markers.set(item.intersection_id, marker);
    } else {
      marker.setLatLng(latlng);
      marker.setStyle(markerOptions(item));
    }
    marker.bindPopup(popupHtml(item));
  }

  for (const [id, marker] of markers) {
    if (!seen.has(id)) {
      markerCluster.removeLayer(marker);
      markers.delete(id);
    }
  }

  if (bounds.length > 0) {
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 16 });
  }
}

function setHealth(health) {
  const status = health?.freshness_status || "UNKNOWN";
  healthBadge.textContent = FRESHNESS_PT[status] || status;
  healthBadge.className = `health-badge health-${status.toLowerCase()}`;
  if (status === "FRESH" && health?.max_lag_seconds != null) {
    healthBadge.title = `Atraso máximo: ${Math.round(health.max_lag_seconds)}s`;
  }
}

async function loadData() {
  const onlyBottlenecks = bottleneckOnly.checked;
  const query = onlyBottlenecks ? "?bottleneck_only=true" : "";
  const [healthRes, listRes] = await Promise.all([
    fetch("/health"),
    fetch(`/intersections${query}`),
  ]);

  if (!healthRes.ok || !listRes.ok) {
    healthBadge.textContent = "Erro ao carregar API";
    healthBadge.className = "health-badge health-unknown";
    return;
  }

  const health = await healthRes.json();
  const body = await listRes.json();
  currentItems = body.items;
  setHealth(health);
  renderList(currentItems);
  updateMarkers(currentItems);
}

bottleneckOnly.addEventListener("change", loadData);
refreshBtn.addEventListener("click", loadData);

loadData();
setInterval(loadData, REFRESH_MS);
