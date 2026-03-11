"""
TamaAI Flask Application v2
Full platform: kid pet view + parent dashboard + Google OAuth
"""

import os
import secrets
from flask import Flask, jsonify, request, send_from_directory, session, redirect, url_for
from flask_cors import CORS
from game_state import GameState
from auth import (is_oauth_configured, get_google_login_url, handle_oauth_callback,
                  require_parent_auth, demo_login)
import database as db

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
CORS(app)

# Initialize database
db.init_db()

# Initialize MCP servers (for Memory, Time, Filesystem, Fetch capabilities)
try:
    from mcp_manager import mcp_manager
    mcp_manager.start()
    print("✓ MCP servers initialized")
except Exception as e:
    print(f"Warning: MCP servers not available: {e}")
    mcp_manager = None

# Game state (single-user prototype)
game = GameState()



# ═══════════════════════════════════════════════════════════════
# KID PET VIEW
# ═══════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)


# ── Pet API ───────────────────────────────────────────────────

@app.route('/api/state', methods=['GET'])
def get_state():
    return jsonify(game.get_state())


@app.route('/api/action', methods=['POST'])
def perform_action():
    data = request.get_json()
    action = data.get('action', '').lower()

    valid_actions = ['feed', 'play', 'rest', 'heal', 'visit']
    if action not in valid_actions:
        return jsonify({'error': f'Invalid action. Must be one of: {valid_actions}'}), 400

    new_state = game.perform_action(action)
    return jsonify(new_state)


@app.route('/api/reset', methods=['POST'])
def reset_game():
    game.reset()
    return jsonify(game.get_state())


# ═══════════════════════════════════════════════════════════════
# PARENT AUTHENTICATION
# ═══════════════════════════════════════════════════════════════

@app.route('/auth/google/login')
def google_login():
    if is_oauth_configured():
        return redirect(get_google_login_url())
    else:
        # Demo mode — auto-login without Google
        demo_login()
        return redirect('/parent')


@app.route('/auth/google/callback')
def google_callback():
    code = request.args.get('code')
    state = request.args.get('state')

    if not code:
        return redirect('/parent?error=no_code')

    success, result = handle_oauth_callback(code, state)
    if success:
        return redirect('/parent')
    else:
        return redirect(f'/parent?error={result}')


@app.route('/auth/demo-login', methods=['POST'])
def auth_demo():
    """Quick demo login for development."""
    data = request.get_json() or {}
    email = data.get('email', 'demo@parent.com')
    demo_login(email)
    return jsonify({'success': True, 'email': email})


@app.route('/auth/logout')
def logout():
    session.clear()
    return redirect('/parent')


@app.route('/auth/status')
def auth_status():
    """Check if user is authenticated."""
    if 'parent_email' in session:
        return jsonify({
            'authenticated': True,
            'email': session['parent_email'],
            'name': session.get('parent_name', ''),
            'picture': session.get('parent_picture', ''),
        })
    return jsonify({'authenticated': False})


# ═══════════════════════════════════════════════════════════════
# PARENT DASHBOARD
# ═══════════════════════════════════════════════════════════════

@app.route('/parent')
def parent_dashboard():
    return send_from_directory('static', 'parent.html')


@app.route('/api/parent/overview')
@require_parent_auth
def parent_overview():
    """Current pet state + summary stats for parent."""
    state = game.get_state()
    summary_24h = db.get_care_summary(game.pet_id, hours=24)
    summary_7d = db.get_care_summary(game.pet_id, hours=168)

    return jsonify({
        'pet': state,
        'today': summary_24h,
        'week': summary_7d,
        'parent': {
            'email': session.get('parent_email'),
            'name': session.get('parent_name'),
            'picture': session.get('parent_picture'),
        }
    })


@app.route('/api/parent/charts')
@require_parent_auth
def parent_charts():
    """Chart data for stats over time."""
    hours = int(request.args.get('hours', 168))
    stats_history = db.get_stats_history(game.pet_id, hours)
    action_history = db.get_action_history(game.pet_id, hours)

    # Aggregate actions by hour for heatmap
    action_by_hour = {}
    for a in action_history:
        h = a.get('hour_of_day', 0)
        action_by_hour.setdefault(h, []).append({
            'type': a['action_type'],
            'quality': a['action_quality'],
        })

    return jsonify({
        'stats_history': stats_history,
        'action_history': action_history,
        'action_by_hour': action_by_hour,
    })


@app.route('/api/parent/hospital')
@require_parent_auth
def parent_hospital():
    """Hospital visit history."""
    visits = db.get_hospital_history(game.pet_id)
    return jsonify({'visits': visits, 'total': len(visits)})


@app.route('/api/parent/alerts')
@require_parent_auth
def parent_alerts():
    """Current neglect alerts and patterns."""
    events = db.get_neglect_events(game.pet_id, hours=48)

    # Group by type and count
    alert_summary = {}
    for e in events:
        t = e['event_type']
        if t not in alert_summary:
            alert_summary[t] = {'count': 0, 'max_severity': 0, 'latest': None}
        alert_summary[t]['count'] += 1
        alert_summary[t]['max_severity'] = max(alert_summary[t]['max_severity'], e['severity'])
        if not alert_summary[t]['latest'] or e['timestamp'] > alert_summary[t]['latest']:
            alert_summary[t]['latest'] = e['timestamp']

    return jsonify({
        'events': events[:20],  # Last 20 events
        'summary': alert_summary,
    })


@app.route('/api/parent/care-report')
@require_parent_auth
def parent_care_report():
    """Generate a prose care report."""
    summary = db.get_care_summary(game.pet_id, hours=168)
    hospital_visits = db.get_hospital_history(game.pet_id)
    neglect = db.get_neglect_events(game.pet_id, hours=168)
    state = game.get_state()

    # Generate insights
    insights = []

    total_actions = summary.get('total_actions', 0)
    if total_actions > 20:
        insights.append(f"Your child has been active with {total_actions} care actions this week.")
    elif total_actions > 5:
        insights.append(f"Your child has performed {total_actions} care actions. Encouraging more engagement would help Rex thrive.")
    else:
        insights.append("Rex hasn't received much attention this week. Encourage your child to check on Rex regularly.")

    avg_quality = summary.get('avg_quality', 0)
    if avg_quality > 0.7:
        insights.append("Excellent care quality! Actions are well-timed and appropriate.")
    elif avg_quality > 0.4:
        insights.append("Good care quality. There's room to improve timing of actions.")
    else:
        insights.append("Care quality could improve. Help your child learn when Rex needs each type of care.")

    meals_on_time = summary.get('meals_on_time', 0)
    if meals_on_time >= 3:
        insights.append(f"Great meal routine! {meals_on_time} meals given at proper times.")
    else:
        insights.append("Meal timing could improve. Encourage feeding Rex at breakfast, lunch, and dinner time.")

    if hospital_visits:
        recent = [v for v in hospital_visits if not v.get('resolved')]
        if recent:
            insights.append(f"Rex has had {len(hospital_visits)} hospital visit(s). Focus on consistent daily care to prevent future visits.")

    # Character development
    outcomes = state.get('outcomes', {})
    strong = [k for k, v in outcomes.items() if v > 65]
    weak = [k for k, v in outcomes.items() if v < 40]
    if strong:
        insights.append(f"Strong development in: {', '.join(strong)}.")
    if weak:
        insights.append(f"Areas for growth: {', '.join(weak)}.")

    return jsonify({
        'insights': insights,
        'summary': summary,
        'outcomes': outcomes,
        'hospital_count': len(hospital_visits),
    })


# ═══════════════════════════════════════════════════════════════
# RUN
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("\nTamaAI Dino Pet Server v2 starting!")
    print("   Kid view:      http://localhost:5000")
    print("   Parent login:  http://localhost:5000/parent")
    if not is_oauth_configured():
        print("   Google OAuth not configured -- using demo login mode")
        print("   Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET for production")
    print()
    app.run(debug=True, host='0.0.0.0', port=5000)
