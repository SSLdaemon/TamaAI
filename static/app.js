/* ═══════════════════════════════════════════════════════════
   TamaAI v2 — Front-end Application
   Hospital UI, particles, day/night, enhanced dino SVG
   ═══════════════════════════════════════════════════════════ */

let currentState = null;
let particleCtx = null;
let particles = [];
let starsGenerated = false;

// ── Init ────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('particles');
    particleCtx = canvas.getContext('2d');
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    generateStars();
    fetchState();
    setInterval(fetchState, 5000);
    requestAnimationFrame(animateParticles);
});

function resizeCanvas() {
    const canvas = document.getElementById('particles');
    const stage = document.getElementById('dino-stage');
    canvas.width = stage.offsetWidth;
    canvas.height = stage.offsetHeight;
}

// ── API ─────────────────────────────────────────────────────
async function fetchState() {
    try {
        const res = await fetch('/api/state');
        const data = await res.json();
        currentState = data;
        renderState(data);
    } catch (e) {
        console.error('Failed to fetch state:', e);
    }
}

async function doAction(action) {
    // Disable buttons briefly
    document.querySelectorAll('.action-btn').forEach(b => b.disabled = true);

    try {
        const res = await fetch('/api/action', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });
        const data = await res.json();
        currentState = data;
        renderState(data);

        // Trigger action animation
        triggerActionEffect(action);
    } catch (e) {
        console.error('Action failed:', e);
    }

    setTimeout(() => {
        document.querySelectorAll('.action-btn').forEach(b => b.disabled = false);
    }, 800);
}

async function resetPet() {
    if (!confirm('Start a new pet? Rex will be reset.')) return;
    try {
        const res = await fetch('/api/reset', { method: 'POST' });
        const data = await res.json();
        currentState = data;
        renderState(data);
    } catch (e) {
        console.error('Reset failed:', e);
    }
}

// ── Render State ────────────────────────────────────────────
function renderState(s) {
    // Pet name
    document.getElementById('pet-name').textContent = s.pet_name || 'Rex';

    // Message
    document.getElementById('message-text').textContent = s.last_message || '';

    // Stats bars
    updateBar('health', s.stats.health);
    updateBar('hunger', s.stats.hunger);
    updateBar('mood', s.stats.mood);
    updateBar('energy', s.stats.energy);

    // Outcomes
    if (s.outcomes) {
        updateOutcome('empathy', s.outcomes.empathy);
        updateOutcome('responsibility', s.outcomes.responsibility);
        updateOutcome('punctuality', s.outcomes.punctuality);
        updateOutcome('wellbeing', s.outcomes.wellbeing);
    }

    // Time display
    updateTimeDisplay(s.time);

    // Sky background
    updateSky(s.time);

    // Hospital / critical banners
    updateHospitalUI(s.hospital);

    // Action buttons visibility
    updateActions(s.available_actions);

    // Dino expression
    updateDinoSVG(s.expression, s.hospital);
    updateDinoAnimation(s.expression);
}

function updateBar(stat, value) {
    const bar = document.getElementById(`bar-${stat}`);
    const val = document.getElementById(`val-${stat}`);
    if (bar) bar.style.width = `${Math.max(1, value)}%`;
    if (val) val.textContent = Math.round(value);
}

function updateOutcome(name, value) {
    const bar = document.getElementById(`bar-${name}`);
    if (bar) bar.style.width = `${Math.max(1, value)}%`;
}

// ── Time Display ────────────────────────────────────────────
function updateTimeDisplay(time) {
    if (!time) return;
    const icon = document.getElementById('time-icon');
    const label = document.getElementById('time-label');
    const meal = document.getElementById('meal-badge');

    const periodLabels = {
        'morning': '🌅 Morning',
        'late_morning': '☀️ Late Morning',
        'midday': '☀️ Midday',
        'afternoon': '🌤️ Afternoon',
        'evening': '🌇 Evening',
        'wind_down': '🌙 Wind Down',
        'night': '🌙 Night'
    };

    const pl = periodLabels[time.period] || '☀️ Day';
    icon.textContent = pl.split(' ')[0];
    label.textContent = pl.substring(pl.indexOf(' ') + 1);

    if (time.is_meal_time && time.current_meal) {
        meal.classList.remove('hidden');
        meal.textContent = `🍖 ${time.current_meal.charAt(0).toUpperCase() + time.current_meal.slice(1)} time!`;
    } else {
        meal.classList.add('hidden');
    }
}

// ── Sky ─────────────────────────────────────────────────────
function updateSky(time) {
    if (!time) return;
    const sky = document.getElementById('sky-bg');
    sky.className = 'sky';

    const h = time.hour;
    if (h >= 5 && h < 7) sky.classList.add('dawn');
    else if (h >= 7 && h < 17) sky.classList.add('day');
    else if (h >= 17 && h < 20) sky.classList.add('sunset');
    else sky.classList.add('night');
}

// ── Stars ───────────────────────────────────────────────────
function generateStars() {
    if (starsGenerated) return;
    starsGenerated = true;
    const container = document.getElementById('stars');
    for (let i = 0; i < 60; i++) {
        const star = document.createElement('div');
        star.style.cssText = `
            position:absolute;
            width:${1 + Math.random() * 3}px;
            height:${1 + Math.random() * 3}px;
            background:#fff;
            border-radius:50%;
            top:${Math.random() * 100}%;
            left:${Math.random() * 100}%;
            opacity:${0.3 + Math.random() * 0.7};
            animation: twinkle ${2 + Math.random() * 3}s ease infinite;
            animation-delay: ${Math.random() * 3}s;
        `;
        container.appendChild(star);
    }
    // Add twinkle keyframes
    const style = document.createElement('style');
    style.textContent = `@keyframes twinkle { 0%,100% { opacity: 0.3; } 50% { opacity: 1; } }`;
    document.head.appendChild(style);
}

// ── Hospital UI ─────────────────────────────────────────────
function updateHospitalUI(hospital) {
    const banner = document.getElementById('hospital-banner');
    const critical = document.getElementById('critical-banner');

    if (!hospital) {
        banner.classList.add('hidden');
        critical.classList.add('hidden');
        return;
    }

    if (hospital.is_hospitalized) {
        banner.classList.remove('hidden');
        critical.classList.add('hidden');
        const pct = hospital.recovery_needed > 0
            ? (hospital.recovery_done / hospital.recovery_needed) * 100 : 0;
        document.getElementById('hospital-bar').style.width = `${pct}%`;
        document.getElementById('hospital-visits').textContent =
            `Visit ${hospital.recovery_done}/${hospital.recovery_needed}`;
    } else if (hospital.is_critical) {
        banner.classList.add('hidden');
        critical.classList.remove('hidden');
    } else {
        banner.classList.add('hidden');
        critical.classList.add('hidden');
    }
}

// ── Actions ─────────────────────────────────────────────────
function updateActions(available) {
    if (!available) return;
    const allBtns = ['feed', 'play', 'rest', 'heal', 'visit'];
    allBtns.forEach(action => {
        const btn = document.querySelector(`.${action}-btn`);
        if (!btn) return;
        if (available.includes(action)) {
            btn.style.display = '';
        } else {
            btn.style.display = 'none';
        }
    });
}

// ── Action Effects ──────────────────────────────────────────
function triggerActionEffect(action) {
    const container = document.getElementById('dino-container');

    // Temporary animation class
    const effectMap = {
        'feed': 'dino-eating',
        'play': 'dino-playing',
        'rest': 'dino-sleeping',
        'heal': 'dino-happy',
        'visit': 'dino-happy'
    };
    const cls = effectMap[action];
    if (cls) {
        container.className = cls;
        setTimeout(() => {
            if (currentState) updateDinoAnimation(currentState.expression);
        }, 1500);
    }

    // Particles
    const particleMap = {
        'feed': { emoji: '🍖', count: 6 },
        'play': { emoji: '⭐', count: 8 },
        'rest': { emoji: '💤', count: 5 },
        'heal': { emoji: '💚', count: 6 },
        'visit': { emoji: '💗', count: 8 }
    };
    const pconf = particleMap[action];
    if (pconf) spawnEmojiParticles(pconf.emoji, pconf.count);
}

// ── Dino Animation Class ────────────────────────────────────
function updateDinoAnimation(expression) {
    const container = document.getElementById('dino-container');
    container.className = `dino-${expression || 'neutral'}`;
}

// ── Particle System ─────────────────────────────────────────
function spawnEmojiParticles(emoji, count) {
    const canvas = document.getElementById('particles');
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    for (let i = 0; i < count; i++) {
        particles.push({
            x: cx + (Math.random() - 0.5) * 80,
            y: cy + (Math.random() - 0.5) * 40,
            vx: (Math.random() - 0.5) * 3,
            vy: -1.5 - Math.random() * 2,
            life: 1.0,
            decay: 0.012 + Math.random() * 0.008,
            emoji: emoji,
            size: 16 + Math.random() * 10
        });
    }
}

function animateParticles() {
    if (!particleCtx) { requestAnimationFrame(animateParticles); return; }
    const canvas = particleCtx.canvas;
    particleCtx.clearRect(0, 0, canvas.width, canvas.height);

    particles = particles.filter(p => p.life > 0);
    particles.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        p.vy -= 0.02; // Float up
        p.life -= p.decay;

        particleCtx.globalAlpha = Math.max(0, p.life);
        particleCtx.font = `${p.size}px sans-serif`;
        particleCtx.fillText(p.emoji, p.x, p.y);
    });
    particleCtx.globalAlpha = 1;

    // Ambient particles based on state
    if (currentState && Math.random() < 0.03) {
        spawnAmbientParticle();
    }

    requestAnimationFrame(animateParticles);
}

function spawnAmbientParticle() {
    if (!currentState) return;
    const canvas = document.getElementById('particles');
    const expr = currentState.expression;
    let emoji = '';
    if (expr === 'sleeping') emoji = '💤';
    else if (expr === 'happy') emoji = Math.random() > 0.5 ? '✨' : '💛';
    else if (expr === 'hospital') emoji = '💊';
    else if (expr === 'sad') emoji = '💧';
    else return;

    particles.push({
        x: canvas.width / 2 + (Math.random() - 0.5) * 60,
        y: canvas.height * 0.4,
        vx: (Math.random() - 0.5) * 0.8,
        vy: -0.8 - Math.random() * 0.5,
        life: 1.0,
        decay: 0.008,
        emoji: emoji,
        size: 14 + Math.random() * 6
    });
}

// ── Dino SVG ────────────────────────────────────────────────
function updateDinoSVG(expression, hospital) {
    const svg = document.getElementById('dino-svg');
    const isHospital = hospital && hospital.is_hospitalized;
    const isRecovering = hospital && hospital.is_recovering;

    // ── Color palettes per expression ────────────────────────
    let body = '#43B581';       // bright emerald green
    let bodyDark = '#3AA076';   // darker shade for spikes/accents
    let belly = '#8FE8A0';      // light green belly
    let cheek = '#FF9AA2';      // soft pink cheeks

    if (expression === 'sick' || expression === 'hospital' || expression === 'nauseous') {
        body = '#90A4AE';
        bodyDark = '#78909C';
        belly = '#CFD8DC';
        cheek = '#EF9A9A';
    } else if (expression === 'recovering') {
        body = '#6ECF8A';
        bodyDark = '#5BB97A';
        belly = '#B9F6CA';
        cheek = '#FFAB91';
    } else if (expression === 'sleeping') {
        body = '#3D9970';
        bodyDark = '#2E8B57';
        belly = '#76D7A0';
        cheek = '#FFCCBC';
    }

    // ── Eyes ─────────────────────────────────────────────────
    let eyes = '';
    if (expression === 'happy') {
        // Happy arc eyes (^_^)
        eyes = `
            <path d="M68 72 Q75 62 82 72" stroke="#2C2C2C" stroke-width="3" fill="none" stroke-linecap="round"/>
            <path d="M108 72 Q115 62 122 72" stroke="#2C2C2C" stroke-width="3" fill="none" stroke-linecap="round"/>`;
    } else if (expression === 'sleeping' || expression === 'sleepy') {
        // Closed sleepy eyes
        eyes = `
            <path d="M67 72 Q75 76 83 72" stroke="#2C2C2C" stroke-width="2.5" fill="none" stroke-linecap="round"/>
            <path d="M107 72 Q115 76 123 72" stroke="#2C2C2C" stroke-width="2.5" fill="none" stroke-linecap="round"/>`;
    } else if (expression === 'sad') {
        // Sad eyes with angled brows and tear
        eyes = `
            <circle cx="75" cy="72" r="7" fill="#2C2C2C"/>
            <circle cx="115" cy="72" r="7" fill="#2C2C2C"/>
            <circle cx="73" cy="69" r="2.5" fill="#fff"/>
            <circle cx="113" cy="69" r="2.5" fill="#fff"/>
            <line x1="65" y1="60" x2="80" y2="63" stroke="#2C2C2C" stroke-width="2.5" stroke-linecap="round"/>
            <line x1="125" y1="60" x2="110" y2="63" stroke="#2C2C2C" stroke-width="2.5" stroke-linecap="round"/>
            <ellipse cx="82" cy="80" rx="2" ry="3" fill="#64B5F6" opacity="0.7"/>`;
    } else if (expression === 'sick' || expression === 'hospital') {
        // X_X eyes
        eyes = `
            <line x1="69" y1="66" x2="81" y2="78" stroke="#546E7A" stroke-width="3" stroke-linecap="round"/>
            <line x1="81" y1="66" x2="69" y2="78" stroke="#546E7A" stroke-width="3" stroke-linecap="round"/>
            <line x1="121" y1="66" x2="109" y2="78" stroke="#546E7A" stroke-width="3" stroke-linecap="round"/>`;
    } else if (expression === 'nauseous') {
        // Swirly eyes
        eyes = `
            <path d="M75 72 m-6 0 a 6 6 0 1 0 12 0 a 6 6 0 1 0 -12 0 M115 72 m-6 0 a 6 6 0 1 0 12 0 a 6 6 0 1 0 -12 0" 
                  stroke="#546E7A" stroke-width="2" fill="none" stroke-dasharray="2,2"/>`;
    } else if (expression === 'hungry') {
        // Big round sparkle eyes (wanting food)
        eyes = `
            <circle cx="75" cy="72" r="9" fill="#2C2C2C"/>
            <circle cx="115" cy="72" r="9" fill="#2C2C2C"/>
            <circle cx="72" cy="68" r="3.5" fill="#fff"/>
            <circle cx="78" cy="74" r="1.5" fill="#fff"/>
            <circle cx="112" cy="68" r="3.5" fill="#fff"/>
            <circle cx="118" cy="74" r="1.5" fill="#fff"/>`;
    } else {
        // Neutral / recovering — cute sparkle eyes
        eyes = `
            <circle cx="75" cy="72" r="8" fill="#2C2C2C"/>
            <circle cx="115" cy="72" r="8" fill="#2C2C2C"/>
            <circle cx="72" cy="68" r="3" fill="#fff"/>
            <circle cx="78" cy="74" r="1.5" fill="#fff"/>
            <circle cx="112" cy="68" r="3" fill="#fff"/>
            <circle cx="118" cy="74" r="1.5" fill="#fff"/>`;
    }

    // ── Mouth ────────────────────────────────────────────────
    let mouth = '';
    if (expression === 'happy') {
        // Big happy smile with teeth
        mouth = `
            <path d="M82 88 Q95 104 108 88" stroke="#2C2C2C" stroke-width="2.5" fill="#fff" stroke-linecap="round"/>
            <polygon points="87,88 90,93 93,88" fill="#fff"/>
            <polygon points="97,88 100,93 103,88" fill="#fff"/>`;
    } else if (expression === 'sad' || expression === 'sick') {
        // Frown
        mouth = `<path d="M84 94 Q95 86 106 94" stroke="#2C2C2C" stroke-width="2" fill="none" stroke-linecap="round"/>`;
    } else if (expression === 'hungry') {
        // Open "O" mouth
        mouth = `
            <ellipse cx="95" cy="92" rx="8" ry="7" fill="#2C2C2C"/>
            <ellipse cx="95" cy="90" rx="6" ry="3" fill="#E57373" opacity="0.6"/>
            <polygon points="89,86 91,89 93,86" fill="#fff"/>
            <polygon points="97,86 99,89 101,86" fill="#fff"/>`;
    } else if (expression === 'sleeping' || expression === 'sleepy') {
        // Tiny peaceful mouth
        mouth = `<path d="M90 90 Q95 93 100 90" stroke="#2C2C2C" stroke-width="1.5" fill="none" stroke-linecap="round"/>`;
    } else if (expression === 'hospital' || expression === 'nauseous') {
        // Wobbly sick mouth
        mouth = `<path d="M84 92 Q89 88 95 92 Q101 96 106 92" stroke="#546E7A" stroke-width="2" fill="none" stroke-linecap="round"/>`;
    } else {
        // Gentle smile with tiny teeth
        mouth = `
            <path d="M84 88 Q95 98 106 88" stroke="#2C2C2C" stroke-width="2" fill="none" stroke-linecap="round"/>
            <polygon points="90,88 92,92 94,88" fill="#fff"/>
            <polygon points="96,88 98,92 100,88" fill="#fff"/>`;
    }

    // ── Spikes (rounded, cute) ───────────────────────────────
    let spikes = '';
    const spikePositions = [
        { x: 78, y: 32, s: 8 },
        { x: 88, y: 26, s: 10 },
        { x: 100, y: 24, s: 11 },
        { x: 112, y: 28, s: 9 },
        { x: 121, y: 35, s: 7 },
    ];
    for (const sp of spikePositions) {
        spikes += `<ellipse cx="${sp.x}" cy="${sp.y}" rx="${sp.s * 0.45}" ry="${sp.s * 0.7}" fill="${bodyDark}" transform="rotate(${(sp.x - 100) * 0.5} ${sp.x} ${sp.y})"/>`;
    }

    // ── Hospital extras ──────────────────────────────────────
    let extras = '';
    if (isHospital) {
        extras = `
            <!-- Hospital bed -->
            <rect x="35" y="162" width="130" height="8" rx="4" fill="#E0E0E0"/>
            <rect x="35" y="158" width="5" height="14" rx="2" fill="#BDBDBD"/>
            <rect x="160" y="158" width="5" height="14" rx="2" fill="#BDBDBD"/>
            <!-- IV drip -->
            <line x1="158" y1="20" x2="158" y2="80" stroke="#90A4AE" stroke-width="2"/>
            <rect x="153" y="14" width="10" height="12" rx="2" fill="#64B5F6"/>
            <circle cx="158" cy="84" r="3" fill="#64B5F6" opacity="0.6"/>
            <!-- Bandage -->
            <rect x="60" y="44" width="16" height="6" rx="2" fill="#FFF9C4"/>
            <line x1="64" y1="44" x2="64" y2="50" stroke="#E0E0E0" stroke-width="0.5"/>
            <line x1="68" y1="44" x2="68" y2="50" stroke="#E0E0E0" stroke-width="0.5"/>
            <line x1="72" y1="44" x2="72" y2="50" stroke="#E0E0E0" stroke-width="0.5"/>`;
    }
    if (isRecovering) {
        extras = `
            <rect x="62" y="46" width="14" height="5" rx="2" fill="#FFF9C4"/>
            <line x1="66" y1="46" x2="66" y2="51" stroke="#E0E0E0" stroke-width="0.5"/>
            <line x1="70" y1="46" x2="70" y2="51" stroke="#E0E0E0" stroke-width="0.5"/>`;
    }

    // ── Sleeping extras (Zzz) ────────────────────────────────
    let sleepExtras = '';
    if (expression === 'sleeping' || expression === 'sleepy') {
        sleepExtras = `
            <text x="130" y="50" font-size="16" fill="#5C6BC0" opacity="0.8" font-weight="bold">z</text>
            <text x="140" y="38" font-size="12" fill="#5C6BC0" opacity="0.6" font-weight="bold">z</text>
            <text x="148" y="28" font-size="9" fill="#5C6BC0" opacity="0.4" font-weight="bold">z</text>`;
    } else if (expression === 'nauseous') {
        sleepExtras = `
            <circle cx="130" cy="50" r="3" fill="#81C784" opacity="0.6"/>
            <circle cx="135" cy="40" r="2" fill="#81C784" opacity="0.4"/>`;
    }

    svg.innerHTML = `
        <!-- Tail -->
        <path d="M42 130 Q28 120 22 108 Q18 98 30 104 Q38 110 48 124"
              fill="${body}"/>

        <!-- Body (round chubby) -->
        <ellipse cx="95" cy="128" rx="48" ry="38" fill="${body}"/>

        <!-- Belly (large light oval) -->
        <ellipse cx="95" cy="134" rx="30" ry="26" fill="${belly}"/>

        <!-- Legs (short stubby) -->
        <ellipse cx="74" cy="160" rx="14" ry="9" fill="${body}"/>
        <ellipse cx="116" cy="160" rx="14" ry="9" fill="${body}"/>
        <!-- Feet pads -->
        <ellipse cx="74" cy="165" rx="12" ry="5" fill="${bodyDark}"/>
        <ellipse cx="116" cy="165" rx="12" ry="5" fill="${bodyDark}"/>
        <!-- Toe marks -->
        <circle cx="67" cy="165" r="2.5" fill="${body}"/>
        <circle cx="74" cy="167" r="2.5" fill="${body}"/>
        <circle cx="81" cy="165" r="2.5" fill="${body}"/>
        <circle cx="109" cy="165" r="2.5" fill="${body}"/>
        <circle cx="116" cy="167" r="2.5" fill="${body}"/>
        <circle cx="123" cy="165" r="2.5" fill="${body}"/>

        <!-- Head (oversized, kawaii chibi) -->
        <ellipse cx="95" cy="68" rx="40" ry="36" fill="${body}"/>

        <!-- Spikes -->
        ${spikes}

        <!-- Arms (tiny stubby, raised up) -->
        <ellipse cx="52" cy="118" rx="12" ry="7" fill="${body}" transform="rotate(-30 52 118)"/>
        <ellipse cx="138" cy="118" rx="12" ry="7" fill="${body}" transform="rotate(30 138 118)"/>
        <!-- Arm pads -->
        <circle cx="44" cy="114" r="3.5" fill="${bodyDark}"/>
        <circle cx="146" cy="114" r="3.5" fill="${bodyDark}"/>

        <!-- Eyes -->
        ${eyes}

        <!-- Cheeks (soft rosy) -->
        <ellipse cx="58" cy="82" rx="8" ry="5" fill="${cheek}" opacity="0.45"/>
        <ellipse cx="132" cy="82" rx="8" ry="5" fill="${cheek}" opacity="0.45"/>

        <!-- Nose dots -->
        <circle cx="90" cy="80" r="1.5" fill="${bodyDark}"/>
        <circle cx="100" cy="80" r="1.5" fill="${bodyDark}"/>

        <!-- Mouth -->
        ${mouth}

        <!-- Hospital extras -->
        ${extras}

        <!-- Sleep Zzz -->
        ${sleepExtras}
    `;
}
