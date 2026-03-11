"""
TamaAI Google OAuth Authentication

Implements Google OAuth 2.0 login flow for parent dashboard.
For localhost development, uses a simplified flow.

Setup:
1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID (Web application)
3. Add redirect URI: http://localhost:5000/auth/google/callback
4. Set environment variables: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
"""

import os
import json
import secrets
import urllib.parse
from functools import wraps
from flask import session, redirect, request, jsonify
import database as db

# OAuth configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'
REDIRECT_URI = os.environ.get('OAUTH_REDIRECT_URI', 'http://localhost:5000/auth/google/callback')


def is_oauth_configured():
    """Check if Google OAuth credentials are set."""
    return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)


def require_parent_auth(f):
    """Decorator to require parent authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'parent_email' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'Authentication required', 'login_url': '/auth/google/login'}), 401
            return redirect('/parent?login=required')
        return f(*args, **kwargs)
    return decorated


def get_google_login_url():
    """Generate Google OAuth consent URL."""
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state

    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': 'openid email profile',
        'response_type': 'code',
        'state': state,
        'access_type': 'offline',
        'prompt': 'consent',
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(code):
    """Exchange authorization code for access token."""
    import urllib.request

    data = urllib.parse.urlencode({
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code',
    }).encode('utf-8')

    req = urllib.request.Request(GOOGLE_TOKEN_URL, data=data, method='POST')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {'error': str(e)}


def get_user_info(access_token):
    """Fetch user profile from Google."""
    import urllib.request

    req = urllib.request.Request(GOOGLE_USERINFO_URL)
    req.add_header('Authorization', f'Bearer {access_token}')

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {'error': str(e)}


def handle_oauth_callback(code, state):
    """
    Process OAuth callback: exchange code, fetch profile, create/update account.
    Returns (success, parent_id_or_error)
    """
    # Verify state
    expected_state = session.pop('oauth_state', None)
    if not expected_state or state != expected_state:
        return False, 'Invalid OAuth state'

    # Exchange code for token
    token_data = exchange_code_for_token(code)
    if 'error' in token_data:
        return False, f"Token exchange failed: {token_data['error']}"

    access_token = token_data.get('access_token')
    if not access_token:
        return False, 'No access token received'

    # Get user profile
    user_info = get_user_info(access_token)
    if 'error' in user_info:
        return False, f"Profile fetch failed: {user_info['error']}"

    email = user_info.get('email')
    google_id = user_info.get('sub')
    name = user_info.get('name', '')
    picture = user_info.get('picture', '')

    if not email:
        return False, 'No email in Google profile'

    # Create or update parent account
    parent_id = db.get_or_create_parent(email, google_id, name, picture)

    # Ensure parent has a pet
    pet_id = db.get_pet_for_parent(parent_id)

    # Set session
    session['parent_id'] = parent_id
    session['parent_email'] = email
    session['parent_name'] = name
    session['parent_picture'] = picture
    session['pet_id'] = pet_id

    return True, parent_id


def demo_login(email="demo@parent.com"):
    """
    Demo login for development without Google OAuth.
    Creates a demo parent account.
    """
    parent_id = db.get_or_create_parent(email, f"demo_{email}", "Demo Parent", "")
    pet_id = db.get_pet_for_parent(parent_id)

    session['parent_id'] = parent_id
    session['parent_email'] = email
    session['parent_name'] = "Demo Parent"
    session['parent_picture'] = ''
    session['pet_id'] = pet_id

    return parent_id
