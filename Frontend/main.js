/* =============================================
   SMART WASTE ANALYTICS — main.js
============================================= */

// ─── STATE ───────────────────────────────────────
let binStates = [];
let collectionLogs = [];
let lineChart = null;
let pieChart = null;
let pieChart2 = null;
let autoRefreshTimer = null;
let sortState = { col: null, dir: 1 };

// ─── API BASE ────────────────────────────────────
const API_BASE = "http://127.0.0.1:8000/api";

const WASTE_CATEGORIES = ["Plastic", "Organic", "Paper", "Metal", "Other"];

// ─── FETCH FUNCTIONS ─────────────────────────────
async function fetchBinData() {
  const res = await fetch(`${API_BASE}/bins`);
  if (!res.ok) throw new Error("Failed to fetch bins");
  return await res.json();
}

async function fetchLogs() {
  const res = await fetch(`${API_BASE}/logs`);
  if (!res.ok) throw new Error("Failed to fetch logs");
  return await res.json();
}

async function simulateData() {
  const res = await fetch(`${API_BASE}/simulate`);
  if (!res.ok) throw new Error("Simulation failed");
  return await res.json();
}

// ─── SETTINGS ────────────────────────────────────
function getSettings() {
  try {
    const s = JSON.parse(localStorage.getItem("wasteSettings"));
    return s || { interval: 30, threshold: 85, darkMode: false };
  } catch (e) {
    return { interval: 30, threshold: 85, darkMode: false };
  }
}

function saveSettingsToStorage(s) {
  localStorage.setItem("wasteSettings", JSON.stringify(s));
}

function getThreshold() {
  return getSettings().threshold;
}

// ─── UTILS ───────────────────────────────────────
function fillColor(pct) {
  const t = getThreshold();
  if (pct >= t) return '#c0392b';
  if (pct >= t - 20) return '#e67e22';
  return '#2e7d4f';
}

function pillHTML(status) {
  const map = { Full: 'pill-full', Filling: 'pill-warn', Normal: 'pill-ok', Offline: 'pill-offline' };
  const cls = map[status] || '';
  const style = !cls ? 'style="background:#eee;color:#777;"' : '';
  return `<span class="status-pill ${cls}" ${style}>${status}</span>`;
}

function showToast(msg, type = '') {
  const tc = document.getElementById('toast-container');
  if (!tc) return;
  const t = document.createElement('div');
  t.className = 'toast' + (type ? ' ' + type : '');
  t.textContent = msg;
  tc.appendChild(t);
  setTimeout(() => t.remove(), 3200);
}

// ─── CLOCK ───────────────────────────────────────
function updateClock() {
  const now = new Date();
  document.getElementById('clock-time').textContent =
    now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  document.getElementById('clock-date').textContent =
    now.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase();
}

// ─── TABS ────────────────────────────────────────
function initTabs() {
  const tabs = document.querySelectorAll('.nav-tab');
  const panels = document.querySelectorAll('.tab-panel');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.dataset.tab;
      tabs.forEach(t => t.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      const panel = document.getElementById('tab-' + target);
      if (panel) panel.classList.add('active');
    });
  });
}

// ─── CHART INIT ──────────────────────────────────
function initPieChart() {
  const ctx = document.getElementById('pieChart');
  if (!ctx) return;
  pieChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: WASTE_CATEGORIES,
      datasets: [{ data: [0, 0, 0, 0], backgroundColor: ['#1a3a5c', '#2e7d4f', '#e67e22', '#8e9aad'] }]
    },
    options: { plugins: { legend: { display: false } }, cutout: '60%' }
  });
}

function initPieChart2() {
  const ctx = document.getElementById('pieChart2');
  if (!ctx) return;
  pieChart2 = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: WASTE_CATEGORIES,
      datasets: [{ data: [0, 0, 0, 0], backgroundColor: ['#1a3a5c', '#2e7d4f', '#e67e22', '#8e9aad'] }]
    },
    options: { plugins: { legend: { display: false } }, cutout: '60%' }
  });
}

function initLineChart() {
  const ctx = document.getElementById('lineChart');
  if (!ctx) return;
  lineChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Plastic', 'Organic', 'Paper', 'Other'],
      datasets: [{
        label: 'Waste Entries',
        data: [0, 0, 0, 0],
        borderColor: '#1a3a5c',
        tension: 0.3,
        fill: false
      }]
    },
    options: {
      plugins: { legend: { display: true, position: 'bottom' } },
      responsive: true,
      maintainAspectRatio: false
    }
  });
}

// ─── WASTE COUNTS ────────────────────────────────
function getWasteCounts() {
  const counts = {
  Plastic: 0,
  Paper: 0,
  Organic: 0,
  Metal: 0,
  Other: 0
};
  binStates.forEach(bin => {
    if (counts[bin.type] !== undefined) counts[bin.type] += bin.entries;
    else counts.Other += bin.entries;
  });
  return counts;
}

// ─── PIE CHARTS ──────────────────────────────────
function updatePieChart() {
  if (!pieChart) return;

  const counts = getWasteCounts();
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  const order = WASTE_CATEGORIES;
  const colors = {
    Plastic: '#1a3a5c',
    Organic: '#2e7d4f',
    Paper: '#e67e22',
    Metal: '#95a5a6',
    Other: '#8e9aad'
  };

  pieChart.data.datasets[0].data = order.map(k => counts[k]);
  pieChart.update();

  const legend = document.getElementById('pie-legend');
  if (!legend) return;

  legend.innerHTML = order.map(k => {
    const pct = total ? Math.round(counts[k] / total * 100) : 0;
    return `
      <div class="legend-item">
        <div class="legend-swatch" style="background:${colors[k]};"></div>
        <span class="legend-name">${k === 'Organic' ? 'Organic / Food' :
        k === 'Metal' ? 'Metal / Can' : k}</span>
        <div class="legend-bar-track">
          <div class="legend-bar-fill" style="width:${pct}%;background:${colors[k]};"></div>
        </div>
        <span class="legend-pct">${pct}%</span>
      </div>`;
  }).join('');
}

function updatePieChart2() {
  if (!pieChart2) return;

  const counts = getWasteCounts();
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  const order = WASTE_CATEGORIES;
  const colors = {
    Plastic: '#1a3a5c',
    Organic: '#2e7d4f',
    Paper: '#e67e22',
    Metal: '#95a5a6',
    Other: '#8e9aad'
  };

  pieChart2.data.datasets[0].data = order.map(k => counts[k]);
  pieChart2.update();

  const legend = document.getElementById('pie2-legend');
  if (!legend) return;

  legend.innerHTML = order.map(k => {
    const pct = total ? Math.round(counts[k] / total * 100) : 0;
    return `
      <div class="legend-item">
        <div class="legend-swatch" style="background:${colors[k]};"></div>
        <span class="legend-name">${k}</span>
        <span class="legend-pct">${pct}%</span>
      </div>`;
  }).join('');
}

// ─── LINE CHART ──────────────────────────────────
function updateLineChart() {
  if (!lineChart) return;

  const counts = getWasteCounts();
  lineChart.data.labels = WASTE_CATEGORIES;
  lineChart.data.datasets[0].data = WASTE_CATEGORIES.map(type => counts[type]);
  lineChart.update();
}

// ─── OVERVIEW CARDS ──────────────────────────────
function updateOverviewCards() {
  const totalEntries = binStates.reduce((s, b) => s + b.entries, 0);

  const wasteCount = {};
  binStates.forEach(b => { wasteCount[b.type] = (wasteCount[b.type] || 0) + b.entries; });

  const commonType = Object.keys(wasteCount).length
    ? Object.keys(wasteCount).reduce((a, b) => wasteCount[a] > wasteCount[b] ? a : b)
    : '—';

  const alerts = binStates.filter(b => b.fill >= getThreshold()).length;
  const activeBins = binStates.filter(b => b.status !== 'Offline').length;
  const totalBins = binStates.length;
  const offlineBins = totalBins - activeBins;

  document.getElementById('ov-entries').textContent = totalEntries;
  document.getElementById('ov-entries-sub').textContent = `Across ${activeBins} active bin${activeBins !== 1 ? 's' : ''}`;

  document.getElementById('ov-common').textContent = commonType;
  const commonPct = totalEntries ? Math.round((wasteCount[commonType] || 0) / totalEntries * 100) : 0;
  document.getElementById('ov-common-sub').textContent = `${commonPct}% of all deposits`;

  document.getElementById('ov-active').innerHTML =
    `${activeBins} <span style="font-size:14px;color:#888;">/ ${totalBins}</span>`;
  document.getElementById('ov-active-sub').textContent =
    offlineBins > 0 ? `${offlineBins} bin${offlineBins > 1 ? 's' : ''} currently offline` : 'All bins online';
  document.getElementById('ov-offline-badge').textContent =
    offlineBins > 0 ? `${offlineBins} Offline` : 'All Online';

  document.getElementById('ov-alerts').textContent = alerts;
  const alertBins = binStates.filter(b => b.fill >= getThreshold()).map(b => b.id).join(', ');
  document.getElementById('ov-alerts-sub').textContent =
    alerts > 0 ? alertBins : 'No active alerts';
}

// ─── TABLE ───────────────────────────────────────
function getFilteredBins() {
  const search = (document.getElementById('table-search')?.value || '').toLowerCase();
  const fStatus = document.getElementById('filter-status')?.value || '';
  const fType = document.getElementById('filter-type')?.value || '';

  return binStates.filter(b => {
    const matchSearch = !search ||
      b.id.toLowerCase().includes(search) ||
      b.loc.toLowerCase().includes(search) ||
      b.type.toLowerCase().includes(search);
    const matchStatus = !fStatus || b.status === fStatus;
    const matchType = !fType || b.type === fType;
    return matchSearch && matchStatus && matchType;
  });
}

function renderTable() {
  const tbody = document.getElementById('bin-tbody');
  if (!tbody) return;

  let rows = getFilteredBins();

  if (sortState.col) {
    rows = [...rows].sort((a, b) => {
      const av = a[sortState.col];
      const bv = b[sortState.col];
      if (typeof av === 'number') return (av - bv) * sortState.dir;
      return String(av).localeCompare(String(bv)) * sortState.dir;
    });
  }

  tbody.innerHTML = rows.map(b => {
    const color = fillColor(b.fill);
    return `
      <tr>
        <td><strong>${b.id}</strong></td>
        <td>${b.loc}</td>
        <td>${b.entries}</td>
        <td>${b.type}</td>
        <td>
          <div class="tbl-bar-wrap">
            <div class="tbl-bar-track">
              <div class="tbl-bar-fill" style="width:${b.fill}%;background:${color};"></div>
            </div>
            <span class="tbl-bar-pct">${b.fill}%</span>
          </div>
        </td>
        <td>${b.last}</td>
        <td>${pillHTML(b.status)}</td>
      </tr>`;
  }).join('');
}

function initTableSortAndFilter() {
  document.querySelectorAll('.data-table th.sortable').forEach(th => {
    th.addEventListener('click', () => {
      const col = th.dataset.col;
      if (sortState.col === col) {
        sortState.dir *= -1;
      } else {
        sortState.col = col;
        sortState.dir = 1;
      }
      document.querySelectorAll('.sort-indicator').forEach(si => si.textContent = '');
      th.querySelector('.sort-indicator').textContent = sortState.dir === 1 ? ' ▲' : ' ▼';
      renderTable();
    });
  });

  document.getElementById('table-search')?.addEventListener('input', renderTable);
  document.getElementById('filter-status')?.addEventListener('change', renderTable);
  document.getElementById('filter-type')?.addEventListener('change', renderTable);
}

// ─── BIN GRID ────────────────────────────────────
function renderBinGrid() {
  const grid = document.getElementById('bin-grid');
  if (!grid) return;

  grid.innerHTML = binStates.map(b => {
    const color = fillColor(b.fill);
    const isOffline = b.status === 'Offline';
    return `
      <div class="bin-card${isOffline ? ' bin-offline' : ''}">
        <div class="bin-card-id">${b.id}</div>
        <div class="bin-card-loc">${b.loc}</div>
        <div class="bin-fill-bar">
          <div class="bin-fill-inner" style="width:${b.fill}%;background:${color};"></div>
        </div>
        <div class="bin-pct" style="color:${color};">${b.fill}% — ${b.status}</div>
        <div class="bin-meta">Type: ${b.type} &nbsp;|&nbsp; Entries: ${b.entries}</div>
      </div>`;
  }).join('');
}

// ─── WASTE TYPE ANALYSIS ─────────────────────────
function updateAnalysis() {
  const counts = getWasteCounts();
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  const colors = {
  Plastic: '#1a3a5c',
  Organic: '#2e7d4f',
  Paper: '#e67e22',
  Metal: '#95a5a6',
  Other: '#8e9aad'
  };

  const container = document.getElementById('analysis-bar-chart');
  if (!container) return;

  container.innerHTML = Object.keys(counts).map(type => {
    const pct = total ? Math.round(counts[type] / total * 100) : 0;
    return `
      <div style="margin-bottom:14px;">
        <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">
          <span style="color:var(--text-label);">${type}</span>
          <span style="font-weight:700;color:var(--navy);">${pct}% &nbsp;(${counts[type]} entries)</span>
        </div>
        <div style="background:#eee;height:20px;border:1px solid #ddd;position:relative;">
          <div style="width:${pct}%;height:100%;background:${colors[type]};transition:width 0.6s;
            display:flex;align-items:center;padding-left:6px;color:#fff;font-size:10px;font-weight:700;">
            ${pct > 10 ? pct + '%' : ''}
          </div>
        </div>
      </div>`;
  }).join('');
}

// ─── COLLECTION LOG ──────────────────────────────
function updateCollectionLog(filter = 'ALL') {
  const container = document.getElementById('log-list');
  if (!container) return;

  let logs = [...collectionLogs];

  if (filter !== 'ALL') {
    logs = logs.filter(log => (log.wasteType || '').toLowerCase() === filter.toLowerCase());
  }

  if (logs.length === 0) {
    container.innerHTML = `<div style="padding:20px;color:var(--text-muted);font-size:12px;">No entries for this filter.</div>`;
    return;
  }

  container.innerHTML = logs.map(log => `
    <div class="log-entry">
      <span>${log.timestamp || '-'}</span>
      <span>${log.binId || '-'}</span>
      <span>${log.wasteType || '-'}</span>
      <span>${log.fillLevel !== undefined ? log.fillLevel + '%' : '-'}</span>
      <span>
        ${log.imageUrl
  ? `<a href="http://127.0.0.1:8000${log.imageUrl}?t=${Math.random()}" target="_blank">View Image</a>`
  : '—'}
      </span>
    </div>
  `).join('');
}

// ─── INSIGHTS ────────────────────────────────────
function generateInsights() {
  const container = document.getElementById('insights-container');
  if (!container) return;

  const threshold = getThreshold();
  const insights = [];

  const highFill = binStates.filter(b => b.fill >= threshold);
  if (highFill.length > 0) {
    insights.push(`⚠️ <strong>${highFill.length} bin${highFill.length > 1 ? 's' : ''}</strong> are at or above ${threshold}% capacity: ${highFill.map(b => b.id).join(', ')}.`);
  }

  const plasticBins = binStates.filter(b => b.type === 'Plastic');
  if (plasticBins.length >= 2) {
    insights.push(`♻️ High plastic waste detected across <strong>${plasticBins.length} bins</strong>. Consider extra recycling collection runs.`);
  }

  const organicPeak = binStates.filter(b => b.type === 'Organic' && b.entries > 15);
  organicPeak.forEach(b => {
    insights.push(`🍃 Organic waste spike at <strong>${b.loc}</strong> (${b.entries} entries).`);
  });

  const offline = binStates.filter(b => b.status === 'Offline');
  if (offline.length > 0) {
    insights.push(`📡 <strong>${offline.length} bin${offline.length > 1 ? 's' : ''} offline</strong>: ${offline.map(b => b.id).join(', ')}. Sensor check required.`);
  }

  if (insights.length === 0) {
    insights.push('✅ All systems normal. No alerts at current threshold.');
  }

  container.innerHTML = insights.map(i => `<div class="insight-box">${i}</div>`).join('');

  const metalBins = binStates.filter(b => b.type === 'Metal');
  if (metalBins.length >= 2) {
    insights.push(`🔩 Metal waste detected in <strong>${metalBins.length} bins</strong>. Recycling opportunity identified.`);
  }

  const otherBins = binStates.filter(b => b.type === 'Other');
  if (otherBins.length >= 2) {
    insights.push(`⚠️ Mixed or unidentified waste increasing across bins.`);
  }
}

// ─── STATUS BAR ──────────────────────────────────
function updateTopBar() {
  const el = document.getElementById('status-bar-text');
  if (!el) return;

  const alerts = binStates.filter(b => b.fill >= getThreshold()).length;
  const offline = binStates.filter(b => b.status === 'Offline').length;

  const parts = ['<span style="color:#27ae60;">● System Online</span>'];
  if (alerts > 0) parts.push(`<span style="color:#c0392b;">⚠ ${alerts} bin${alerts > 1 ? 's' : ''} require collection</span>`);
  if (offline > 0) parts.push(`<span style="color:#e67e22;">⚡ ${offline} bin${offline > 1 ? 's' : ''} offline</span>`);
  if (alerts === 0 && offline === 0) parts.push('<span style="color:#2e7d4f;">All bins normal</span>');

  el.innerHTML = parts.join(' &nbsp;|&nbsp; ');

  const now = new Date();
  document.getElementById('last-refresh').textContent =
    now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false }) + ' hrs';
}

// ─── MAIN LOAD & RENDER ──────────────────────────
async function loadAndRender() {
  try {
    const [binData, logData] = await Promise.all([
      fetchBinData(),
      fetchLogs()
    ]);

    binStates = (binData.bins || []).map(bin => ({
      id: bin.id,
      loc: bin.location,
      entries: bin.entries,
      type: bin.waste,
      fill: bin.fill,
      last: bin.last,
      status: bin.status,
      imageUrl: bin.imageUrl || ""
    }));

    collectionLogs = logData.logs || [];

    renderTable();
    renderBinGrid();
    updateOverviewCards();
    updatePieChart();
    updatePieChart2();
    updateLineChart();
    updateAnalysis();
    updateCollectionLog('ALL');
    generateInsights();
    updateTopBar();

  } catch (err) {
    console.error('Data load error:', err);
    showToast('Failed to load data', 'error');
  }
}

// ─── AUTO REFRESH ────────────────────────────────
function startAutoRefresh() {
  if (autoRefreshTimer) clearInterval(autoRefreshTimer);
  const secs = getSettings().interval || 30;
  const label = document.getElementById('refresh-label');
  if (label) label.textContent = secs < 60 ? secs + 's' : Math.floor(secs / 60) + 'm';
  autoRefreshTimer = setInterval(loadAndRender, secs * 1000);
}

// ─── SETTINGS UI ─────────────────────────────────
function loadSettingsUI() {
  const s = getSettings();
  const ri = document.getElementById('refresh-interval');
  const ot = document.getElementById('overflow-threshold');
  const dm = document.getElementById('dark-mode-toggle');

  if (ri) ri.value = s.interval;
  if (ot) ot.value = s.threshold;
  if (dm) dm.checked = !!s.darkMode;

  toggleDarkMode(!!s.darkMode);
}

function saveSettings() {
  const interval = parseInt(document.getElementById('refresh-interval').value) || 30;
  const threshold = parseInt(document.getElementById('overflow-threshold').value) || 85;
  const darkMode = document.getElementById('dark-mode-toggle').checked;

  saveSettingsToStorage({ interval, threshold, darkMode });
  toggleDarkMode(darkMode);
  startAutoRefresh();

  renderTable();
  renderBinGrid();
  updateOverviewCards();
  generateInsights();
  updateTopBar();

  showToast('Settings saved!', 'success');
}

function toggleDarkMode(enabled) {
  document.body.classList.toggle('dark-mode', !!enabled);
}

// ─── REPORT DOWNLOAD ─────────────────────────────
function downloadReport(type) {
  const now = new Date().toLocaleString('en-IN');
  let content = `SMART WASTE ANALYTICS SYSTEM\n`;
  content += `Report Type : ${type.replace(/_/g, ' ')}\n`;
  content += `Generated   : ${now}\n`;
  content += `${'='.repeat(50)}\n\n`;

  binStates.forEach(bin => {
    content += `Bin ID   : ${bin.id}\n`;
    content += `Location : ${bin.loc}\n`;
    content += `Waste    : ${bin.type}\n`;
    content += `Entries  : ${bin.entries}\n`;
    content += `Fill     : ${bin.fill}%\n`;
    content += `Status   : ${bin.status}\n`;
    content += `Last     : ${bin.last}\n`;
    content += `${'-'.repeat(40)}\n`;
  });

  const blob = new Blob([content], { type: 'text/plain' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = type + '_report.txt';
  link.click();
  showToast('Report downloaded', 'success');
}

// ─── INIT ────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  setInterval(updateClock, 1000);
  updateClock();

  initTabs();
  initPieChart();
  initPieChart2();
  initLineChart();
  initTableSortAndFilter();

  loadSettingsUI();

  document.getElementById('settings-save')?.addEventListener('click', saveSettings);
  document.getElementById('dark-mode-toggle')?.addEventListener('change', e => toggleDarkMode(e.target.checked));

  document.querySelectorAll('.log-filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.log-filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      updateCollectionLog(btn.dataset.type || 'ALL');
    });
  });

  document.querySelectorAll('.report-btn').forEach(btn => {
    btn.addEventListener('click', () => downloadReport(btn.dataset.report));
  });

  // OPTIONAL: if you have a simulate button in HTML
  document.getElementById('simulate-btn')?.addEventListener('click', async () => {
    try {
      await simulateData();
      await loadAndRender();
      showToast('Simulation updated!', 'success');
    } catch (e) {
      showToast('Simulation failed', 'error');
    }
  });

  loadAndRender();
  startAutoRefresh();
});