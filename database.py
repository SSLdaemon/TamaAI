"""
TamaAI Database Layer — SQLite persistence for pets, history, hospital visits, parents.
"""

import sqlite3
import json
import time
import uuid
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'tamaai.db')


def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize all database tables."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS parent_accounts (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            google_id TEXT UNIQUE,
            name TEXT,
            profile_picture TEXT,
            created_at REAL,
            last_login REAL
        );

        CREATE TABLE IF NOT EXISTS pets (
            id TEXT PRIMARY KEY,
            parent_id TEXT,
            name TEXT DEFAULT 'Rex',
            created_at REAL,
            last_update REAL,
            stats_json TEXT,
            outcomes_json TEXT,
            hospital_status TEXT DEFAULT 'healthy',
            hospital_enter_time REAL,
            hospital_recovery_needed INTEGER DEFAULT 0,
            hospital_recovery_done INTEGER DEFAULT 0,
            action_count INTEGER DEFAULT 0,
            total_hospital_visits INTEGER DEFAULT 0,
            feeding_scores_json TEXT DEFAULT '[]',
            healthcare_scores_json TEXT DEFAULT '[]',
            emotional_scores_json TEXT DEFAULT '[]',
            rest_scores_json TEXT DEFAULT '[]',
            FOREIGN KEY (parent_id) REFERENCES parent_accounts(id)
        );

        CREATE TABLE IF NOT EXISTS action_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id TEXT NOT NULL,
            action_type TEXT,
            action_quality REAL,
            timestamp REAL,
            hour_of_day INTEGER,
            stats_before TEXT,
            stats_after TEXT,
            FOREIGN KEY (pet_id) REFERENCES pets(id)
        );

        CREATE TABLE IF NOT EXISTS stats_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id TEXT NOT NULL,
            timestamp REAL,
            hour_of_day INTEGER,
            health REAL, hunger REAL, mood REAL, energy REAL,
            empathy REAL, responsibility REAL, punctuality REAL, wellbeing REAL,
            FOREIGN KEY (pet_id) REFERENCES pets(id)
        );

        CREATE TABLE IF NOT EXISTS hospital_visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id TEXT NOT NULL,
            admit_time REAL,
            discharge_time REAL,
            reason TEXT,
            recovery_required INTEGER,
            recovery_completed INTEGER DEFAULT 0,
            resolved INTEGER DEFAULT 0,
            FOREIGN KEY (pet_id) REFERENCES pets(id)
        );

        CREATE TABLE IF NOT EXISTS neglect_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id TEXT NOT NULL,
            event_type TEXT,
            severity INTEGER,
            timestamp REAL,
            details TEXT,
            FOREIGN KEY (pet_id) REFERENCES pets(id)
        );

        CREATE INDEX IF NOT EXISTS idx_action_history_pet ON action_history(pet_id, timestamp);
        CREATE INDEX IF NOT EXISTS idx_stats_snapshots_pet ON stats_snapshots(pet_id, timestamp);
        CREATE INDEX IF NOT EXISTS idx_hospital_visits_pet ON hospital_visits(pet_id, admit_time);
    """)
    conn.commit()
    conn.close()


# ── Pet CRUD ──────────────────────────────────────────────────

def create_pet(parent_id=None, name="Rex"):
    """Create a new pet and return its ID."""
    conn = get_db()
    pet_id = str(uuid.uuid4())[:8]
    now = time.time()
    default_stats = json.dumps({'health': 80.0, 'hunger': 30.0, 'mood': 75.0, 'energy': 70.0})
    default_outcomes = json.dumps({'empathy': 50.0, 'responsibility': 50.0, 'punctuality': 50.0, 'wellbeing': 60.0})

    conn.execute("""
        INSERT INTO pets (id, parent_id, name, created_at, last_update, stats_json, outcomes_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (pet_id, parent_id, name, now, now, default_stats, default_outcomes))
    conn.commit()
    conn.close()
    return pet_id


def save_pet_state(pet_id, stats, outcomes, hospital_status, hospital_enter_time,
                   hospital_recovery_needed, hospital_recovery_done, action_count,
                   total_hospital_visits, feeding_scores, healthcare_scores,
                   emotional_scores, rest_scores):
    """Save full pet state to database."""
    conn = get_db()
    conn.execute("""
        UPDATE pets SET
            last_update=?, stats_json=?, outcomes_json=?,
            hospital_status=?, hospital_enter_time=?,
            hospital_recovery_needed=?, hospital_recovery_done=?,
            action_count=?, total_hospital_visits=?,
            feeding_scores_json=?, healthcare_scores_json=?,
            emotional_scores_json=?, rest_scores_json=?
        WHERE id=?
    """, (
        time.time(), json.dumps(stats), json.dumps(outcomes),
        hospital_status, hospital_enter_time,
        hospital_recovery_needed, hospital_recovery_done,
        action_count, total_hospital_visits,
        json.dumps(feeding_scores[-20:]), json.dumps(healthcare_scores[-20:]),
        json.dumps(emotional_scores[-20:]), json.dumps(rest_scores[-20:]),
        pet_id
    ))
    conn.commit()
    conn.close()


def load_pet_state(pet_id):
    """Load pet state from database. Returns dict or None."""
    conn = get_db()
    row = conn.execute("SELECT * FROM pets WHERE id=?", (pet_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def get_default_pet():
    """Get or create the default pet (for single-user prototype)."""
    conn = get_db()
    row = conn.execute("SELECT id FROM pets ORDER BY created_at DESC LIMIT 1").fetchone()
    conn.close()
    if row:
        return row['id']
    return create_pet()


# ── History Logging ───────────────────────────────────────────

def log_action(pet_id, action_type, quality, hour, stats_before, stats_after):
    """Log an action to history."""
    conn = get_db()
    conn.execute("""
        INSERT INTO action_history (pet_id, action_type, action_quality, timestamp, hour_of_day, stats_before, stats_after)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (pet_id, action_type, quality, time.time(), hour, json.dumps(stats_before), json.dumps(stats_after)))
    conn.commit()
    conn.close()


def log_stats_snapshot(pet_id, hour, stats, outcomes):
    """Log a periodic stats snapshot."""
    conn = get_db()
    conn.execute("""
        INSERT INTO stats_snapshots (pet_id, timestamp, hour_of_day, health, hunger, mood, energy, empathy, responsibility, punctuality, wellbeing)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (pet_id, time.time(), hour,
          stats['health'], stats['hunger'], stats['mood'], stats['energy'],
          outcomes['empathy'], outcomes['responsibility'], outcomes['punctuality'], outcomes['wellbeing']))
    conn.commit()
    conn.close()


def log_hospital_visit(pet_id, reason, recovery_required):
    """Log a hospital admission."""
    conn = get_db()
    conn.execute("""
        INSERT INTO hospital_visits (pet_id, admit_time, reason, recovery_required)
        VALUES (?, ?, ?, ?)
    """, (pet_id, time.time(), reason, recovery_required))
    conn.commit()
    conn.close()


def discharge_hospital(pet_id):
    """Mark current hospital visit as resolved."""
    conn = get_db()
    conn.execute("""
        UPDATE hospital_visits SET discharge_time=?, resolved=1
        WHERE pet_id=? AND resolved=0
    """, (time.time(), pet_id))
    conn.commit()
    conn.close()


def log_neglect(pet_id, event_type, severity, details=""):
    """Log a neglect event."""
    conn = get_db()
    conn.execute("""
        INSERT INTO neglect_events (pet_id, event_type, severity, timestamp, details)
        VALUES (?, ?, ?, ?, ?)
    """, (pet_id, event_type, severity, time.time(), details))
    conn.commit()
    conn.close()


# ── Analytics Queries ─────────────────────────────────────────

def get_action_history(pet_id, hours=168):
    """Get action history for last N hours (default 7 days)."""
    conn = get_db()
    cutoff = time.time() - (hours * 3600)
    rows = conn.execute("""
        SELECT * FROM action_history WHERE pet_id=? AND timestamp>? ORDER BY timestamp
    """, (pet_id, cutoff)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats_history(pet_id, hours=168):
    """Get stats snapshots for last N hours."""
    conn = get_db()
    cutoff = time.time() - (hours * 3600)
    rows = conn.execute("""
        SELECT * FROM stats_snapshots WHERE pet_id=? AND timestamp>? ORDER BY timestamp
    """, (pet_id, cutoff)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_hospital_history(pet_id):
    """Get all hospital visits."""
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM hospital_visits WHERE pet_id=? ORDER BY admit_time DESC
    """, (pet_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_neglect_events(pet_id, hours=168):
    """Get neglect events for last N hours."""
    conn = get_db()
    cutoff = time.time() - (hours * 3600)
    rows = conn.execute("""
        SELECT * FROM neglect_events WHERE pet_id=? AND timestamp>? ORDER BY timestamp DESC
    """, (pet_id, cutoff)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_care_summary(pet_id, hours=24):
    """Generate care summary stats for last N hours."""
    actions = get_action_history(pet_id, hours)
    stats_history = get_stats_history(pet_id, hours)

    summary = {
        'total_actions': len(actions),
        'actions_by_type': {},
        'avg_quality': 0,
        'meals_on_time': 0,
        'missed_meals': 0,
        'avg_health': 0,
        'avg_mood': 0,
    }

    if actions:
        for a in actions:
            t = a['action_type']
            summary['actions_by_type'][t] = summary['actions_by_type'].get(t, 0) + 1
        summary['avg_quality'] = sum(a['action_quality'] for a in actions) / len(actions)

        # Count meals at proper times (7-9, 11-13, 17-19)
        meal_windows = [(7, 9), (11, 13), (17, 19)]
        feeds = [a for a in actions if a['action_type'] == 'feed']
        for a in feeds:
            h = a.get('hour_of_day', 12)
            if any(start <= h <= end for start, end in meal_windows):
                summary['meals_on_time'] += 1

    if stats_history:
        summary['avg_health'] = sum(s['health'] for s in stats_history) / len(stats_history)
        summary['avg_mood'] = sum(s['mood'] for s in stats_history) / len(stats_history)

    return summary


# ── Parent Account ────────────────────────────────────────────

def get_or_create_parent(email, google_id, name="", picture=""):
    """Get or create a parent account. Returns parent_id."""
    conn = get_db()
    row = conn.execute("SELECT id FROM parent_accounts WHERE email=?", (email,)).fetchone()
    if row:
        conn.execute("UPDATE parent_accounts SET last_login=? WHERE id=?", (time.time(), row['id']))
        conn.commit()
        conn.close()
        return row['id']

    parent_id = str(uuid.uuid4())[:8]
    conn.execute("""
        INSERT INTO parent_accounts (id, email, google_id, name, profile_picture, created_at, last_login)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (parent_id, email, google_id, name, picture, time.time(), time.time()))
    conn.commit()
    conn.close()
    return parent_id


def get_pet_for_parent(parent_id):
    """Get pet ID for a parent, creating one if needed."""
    conn = get_db()
    row = conn.execute("SELECT id FROM pets WHERE parent_id=?", (parent_id,)).fetchone()
    conn.close()
    if row:
        return row['id']
    return create_pet(parent_id)
