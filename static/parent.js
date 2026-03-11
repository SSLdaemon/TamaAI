/* ═══════════════════════════════════════════════════════════
   TamaAI v2 — Parent Dashboard JS
   Auth check, Chart.js graphs, care report, alerts
   ═══════════════════════════════════════════════════════════ */

let statsChart = null;
let outcomesChart = null;
let heatmapChart = null;

// ── Init ────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
});

// ── Auth ────────────────────────────────────────────────────
async function checkAuth() {
    try {
        const res = await fetch('/auth/status');
        const data = await res.json();
        if (data.authenticated) {
            showDashboard(data);
        } else {
            showLogin();
        }
    } catch (e) {
        console.error('Auth check failed:', e);
        showLogin();
    }
}

function showLogin() {
    document.getElementById('login-screen').classList.remove('hidden');
    document.getElementById('dashboard').classList.add('hidden');
}

function showDashboard(user) {
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('dashboard').classList.remove('hidden');

    // Set user info
    document.getElementById('user-name').textContent = user.name || user.email;
    if (user.picture) {
        const avatar = document.getElementById('user-avatar');
        avatar.src = user.picture;
        avatar.classList.remove('hidden');
    }

    // Load all data
    loadOverview();
    loadCharts();
    loadReport();
    loadAlerts();
}

async function demoLogin() {
    try {
        const res = await fetch('/auth/demo-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: 'demo@parent.com' })
        });
        const data = await res.json();
        if (data.success) {
            checkAuth();
        }
    } catch (e) {
        console.error('Demo login failed:', e);
    }
}

// ── Overview ────────────────────────────────────────────────
async function loadOverview() {
    try {
        const res = await fetch('/api/parent/overview');
        if (res.status === 401) { showLogin(); return; }
        const data = await res.json();

        // Pet stats
        const pet = data.pet;
        if (pet && pet.stats) {
            setMiniBar('mini-health', pet.stats.health);
            setMiniBar('mini-hunger', pet.stats.hunger);
            setMiniBar('mini-mood', pet.stats.mood);
            setMiniBar('mini-energy', pet.stats.energy);
        }

        // Status badge
        const badge = document.getElementById('pet-status-badge');
        if (pet && pet.hospital) {
            if (pet.hospital.is_hospitalized) {
                badge.textContent = 'Hospitalized';
                badge.className = 'status-badge hospital';
            } else if (pet.hospital.is_critical) {
                badge.textContent = 'Critical';
                badge.className = 'status-badge critical';
            } else if (pet.hospital.is_recovering) {
                badge.textContent = 'Recovering';
                badge.className = 'status-badge';
            } else {
                badge.textContent = 'Healthy';
                badge.className = 'status-badge';
            }
        }

        // Weekly summary
        const week = data.week || {};
        document.getElementById('week-actions').textContent = week.total_actions || 0;
        const quality = week.avg_quality ? Math.round(week.avg_quality * 100) : 0;
        document.getElementById('week-quality').textContent = quality + '%';
        document.getElementById('week-meals').textContent = week.meals_on_time || 0;
        document.getElementById('week-hospital').textContent = pet ? pet.total_hospital_visits || 0 : 0;

    } catch (e) {
        console.error('Failed to load overview:', e);
    }
}

function setMiniBar(id, value) {
    const el = document.getElementById(id);
    if (el) el.style.width = `${Math.max(1, value)}%`;
}

// ── Charts ──────────────────────────────────────────────────
async function loadCharts() {
    try {
        const res = await fetch('/api/parent/charts?hours=168');
        if (res.status === 401) return;
        const data = await res.json();

        renderStatsChart(data.stats_history || []);
        renderOutcomesChart(data.stats_history || []);
        renderHeatmap(data.action_by_hour || {});
    } catch (e) {
        console.error('Failed to load charts:', e);
    }
}

function renderStatsChart(history) {
    const ctx = document.getElementById('stats-chart');
    if (!ctx) return;

    const labels = history.map((h, i) => {
        if (i % 6 === 0 && h.timestamp) {
            const d = new Date(h.timestamp);
            return d.toLocaleDateString('en-US', { weekday: 'short', hour: 'numeric' });
        }
        return '';
    });

    if (statsChart) statsChart.destroy();
    statsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                { label: 'Health', data: history.map(h => h.health), borderColor: '#4CAF50', backgroundColor: 'rgba(76,175,80,0.1)', fill: true, tension: 0.3, pointRadius: 0 },
                { label: 'Hunger', data: history.map(h => h.hunger), borderColor: '#FF9800', backgroundColor: 'rgba(255,152,0,0.1)', fill: true, tension: 0.3, pointRadius: 0 },
                { label: 'Mood', data: history.map(h => h.mood), borderColor: '#2196F3', backgroundColor: 'rgba(33,150,243,0.1)', fill: true, tension: 0.3, pointRadius: 0 },
                { label: 'Energy', data: history.map(h => h.energy), borderColor: '#FFC107', backgroundColor: 'rgba(255,193,7,0.1)', fill: true, tension: 0.3, pointRadius: 0 },
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { min: 0, max: 100, grid: { color: '#f0f0f0' } },
                x: { grid: { display: false }, ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 8 } }
            },
            plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, padding: 12 } } },
            interaction: { mode: 'index', intersect: false }
        }
    });
}

function renderOutcomesChart(history) {
    const ctx = document.getElementById('outcomes-chart');
    if (!ctx || history.length === 0) return;

    // Get latest outcomes from history
    const latest = history[history.length - 1] || {};
    const outcomes = {
        empathy: latest.empathy || 50,
        responsibility: latest.responsibility || 50,
        punctuality: latest.punctuality || 50,
        wellbeing: latest.wellbeing || 50
    };

    if (outcomesChart) outcomesChart.destroy();
    outcomesChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Empathy', 'Responsibility', 'Punctuality', 'Wellbeing'],
            datasets: [{
                label: 'Character Development',
                data: [outcomes.empathy, outcomes.responsibility, outcomes.punctuality, outcomes.wellbeing],
                backgroundColor: 'rgba(76,175,80,0.2)',
                borderColor: '#4CAF50',
                borderWidth: 2,
                pointBackgroundColor: '#4CAF50',
                pointRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { r: { min: 0, max: 100, ticks: { stepSize: 25 } } },
            plugins: { legend: { display: false } }
        }
    });
}

function renderHeatmap(actionByHour) {
    const ctx = document.getElementById('heatmap-chart');
    if (!ctx) return;

    // Build data: count of actions per hour
    const hours = Array.from({ length: 24 }, (_, i) => i);
    const counts = hours.map(h => {
        const actions = actionByHour[h] || [];
        return actions.length;
    });

    const colors = counts.map(c => {
        if (c === 0) return 'rgba(200,200,200,0.3)';
        if (c <= 2) return 'rgba(76,175,80,0.4)';
        if (c <= 5) return 'rgba(76,175,80,0.6)';
        return 'rgba(76,175,80,0.9)';
    });

    if (heatmapChart) heatmapChart.destroy();
    heatmapChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: hours.map(h => {
                if (h === 0) return '12am';
                if (h < 12) return h + 'am';
                if (h === 12) return '12pm';
                return (h - 12) + 'pm';
            }),
            datasets: [{
                label: 'Actions',
                data: counts,
                backgroundColor: colors,
                borderRadius: 4,
                barThickness: 14
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { display: false },
                x: { grid: { display: false }, ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: 12, font: { size: 10 } } }
            },
            plugins: { legend: { display: false } }
        }
    });
}

// ── Care Report ─────────────────────────────────────────────
async function loadReport() {
    try {
        const res = await fetch('/api/parent/care-report');
        if (res.status === 401) return;
        const data = await res.json();

        const container = document.getElementById('report-content');
        if (data.insights && data.insights.length > 0) {
            container.innerHTML = data.insights.map(insight => {
                let cls = 'report-insight';
                if (insight.includes('improve') || insight.includes('growth') || insight.includes('hasn\'t'))
                    cls += ' warning';
                if (insight.includes('hospital') || insight.includes('critically'))
                    cls += ' danger';
                return `<div class="${cls}">${insight}</div>`;
            }).join('');
        } else {
            container.innerHTML = '<p class="loading-text">No report data yet. Keep playing with Rex!</p>';
        }
    } catch (e) {
        console.error('Failed to load report:', e);
    }
}

// ── Alerts ──────────────────────────────────────────────────
async function loadAlerts() {
    try {
        const res = await fetch('/api/parent/alerts');
        if (res.status === 401) return;
        const data = await res.json();

        const countEl = document.getElementById('alert-count');
        const listEl = document.getElementById('alerts-list');
        const events = data.events || [];

        countEl.textContent = events.length;
        if (events.length === 0) {
            countEl.classList.add('zero');
            listEl.innerHTML = '<p class="no-alerts">No alerts — everything looks good!</p>';
            return;
        }

        countEl.classList.remove('zero');
        listEl.innerHTML = events.slice(0, 10).map(e => {
            const severityClass = e.severity >= 7 ? 'severity-high' : e.severity >= 4 ? 'severity-med' : 'severity-low';
            const icons = {
                'missed_meal': '🍖',
                'sleep_deprivation': '😴',
                'emotional_neglect': '💔',
                'low_health': '🏥',
                'starvation': '🍖',
                'exhaustion': '😴',
                'emotional_crisis': '💔'
            };
            const icon = icons[e.event_type] || '⚠️';
            const type = e.event_type.replace(/_/g, ' ');
            const time = e.timestamp ? new Date(e.timestamp).toLocaleString() : '';

            return `
                <div class="alert-item">
                    <span class="alert-icon">${icon}</span>
                    <div>
                        <span class="alert-type">${type}</span>
                        <span class="alert-severity ${severityClass}">Severity ${e.severity}</span>
                        <div class="alert-time">${time}</div>
                        <div style="font-size:12px;color:#888;margin-top:2px;">${e.details || ''}</div>
                    </div>
                </div>
            `;
        }).join('');

    } catch (e) {
        console.error('Failed to load alerts:', e);
    }
}
