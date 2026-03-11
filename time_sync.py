"""
TamaAI Time Sync — Maps real-world clock to environment factors.
Syncs the pet's day to a realistic child's schedule.
"""

from datetime import datetime


# ── Child's Daily Schedule ────────────────────────────────────
# These define the "ideal" schedule the game rewards

SCHEDULE = {
    'wake_up': 7,           # 7:00 AM
    'breakfast': (7, 8),    # 7-8 AM
    'morning_play': (9, 11),
    'lunch': (12, 13),      # 12-1 PM
    'afternoon_activity': (14, 16),
    'dinner': (18, 19),     # 6-7 PM
    'evening_wind_down': (19, 20),
    'bedtime': 21,          # 9:00 PM
    'sleep_hours': (21, 7), # 9 PM - 7 AM
}

MEAL_WINDOWS = [
    {'name': 'breakfast', 'start': 7, 'end': 9, 'peak': 8},
    {'name': 'lunch', 'start': 11, 'end': 13, 'peak': 12},
    {'name': 'dinner', 'start': 17, 'end': 19, 'peak': 18},
]


def get_current_time_info():
    """Get full time context for the current moment."""
    now = datetime.now()
    return get_time_info(now.hour, now.minute, now.month)


def get_time_info(hour, minute=0, month=1):
    """
    Compute all time-dependent factors.

    Returns dict with:
        hour, minute, month, period, is_sleep_time, is_meal_time,
        current_meal, meal_urgency, temperature_idx, light_idx,
        seasonal_idx, hunger_multiplier, energy_multiplier,
        mood_modifier, activity_type
    """
    info = {
        'hour': hour,
        'minute': minute,
        'month': month,
    }

    # ── Period of day ─────────────────────────────────────────
    if 7 <= hour < 9:
        info['period'] = 'morning'
    elif 9 <= hour < 12:
        info['period'] = 'late_morning'
    elif 12 <= hour < 14:
        info['period'] = 'midday'
    elif 14 <= hour < 17:
        info['period'] = 'afternoon'
    elif 17 <= hour < 20:
        info['period'] = 'evening'
    elif 20 <= hour < 21:
        info['period'] = 'wind_down'
    else:
        info['period'] = 'night'

    # ── Sleep time ────────────────────────────────────────────
    info['is_sleep_time'] = hour >= 21 or hour < 7

    # ── Meal time detection ───────────────────────────────────
    info['is_meal_time'] = False
    info['current_meal'] = None
    info['meal_urgency'] = 0.0  # 0-1, how urgent feeding is

    for meal in MEAL_WINDOWS:
        if meal['start'] <= hour <= meal['end']:
            info['is_meal_time'] = True
            info['current_meal'] = meal['name']
            # Urgency peaks at meal time, fades at edges
            distance_from_peak = abs(hour + minute / 60 - meal['peak'])
            info['meal_urgency'] = max(0, 1.0 - distance_from_peak / 2.0)
            break

    # ── Temperature (Bayesian index) ──────────────────────────
    # 0=cold, 1=mild, 2=warm
    if hour >= 21 or hour < 6:
        info['temperature_idx'] = 0  # cold at night
    elif 6 <= hour < 10:
        info['temperature_idx'] = 1  # mild morning
    elif 10 <= hour < 16:
        info['temperature_idx'] = 2  # warm afternoon
    elif 16 <= hour < 21:
        info['temperature_idx'] = 1  # mild evening
    else:
        info['temperature_idx'] = 1

    # ── Light (Bayesian index) ────────────────────────────────
    # 0=dark, 1=bright
    info['light_idx'] = 0 if (hour >= 20 or hour < 7) else 1

    # ── Seasonal (Bayesian index) ─────────────────────────────
    # 0=spring, 1=summer, 2=autumn, 3=winter
    if month in (3, 4, 5):
        info['seasonal_idx'] = 0
    elif month in (6, 7, 8):
        info['seasonal_idx'] = 1
    elif month in (9, 10, 11):
        info['seasonal_idx'] = 2
    else:
        info['seasonal_idx'] = 3

    # ── Hunger multiplier ─────────────────────────────────────
    # Hunger builds faster approaching meal times
    if info['is_meal_time']:
        info['hunger_multiplier'] = 1.5 + info['meal_urgency'] * 1.5  # 1.5x-3x during meals
    elif info['is_sleep_time']:
        info['hunger_multiplier'] = 0.3  # Very slow at night
    else:
        info['hunger_multiplier'] = 1.0

    # ── Energy multiplier ─────────────────────────────────────
    # Energy drains faster during active hours, recovers during sleep
    if info['is_sleep_time']:
        info['energy_multiplier'] = -1.5  # Negative = recovery during sleep
    elif info['period'] in ('morning', 'late_morning', 'afternoon'):
        info['energy_multiplier'] = 1.2  # Active drain
    elif info['period'] == 'wind_down':
        info['energy_multiplier'] = 1.5  # Getting tired
    else:
        info['energy_multiplier'] = 1.0

    # ── Mood modifier ─────────────────────────────────────────
    # Seasonal + time effects on mood baseline
    seasonal_mood = {0: 0.1, 1: 0.0, 2: -0.05, 3: -0.1}  # spring=happy, winter=sad
    time_mood = {
        'morning': 0.05, 'late_morning': 0.1, 'midday': 0.0,
        'afternoon': 0.05, 'evening': 0.0, 'wind_down': -0.05, 'night': -0.1
    }
    info['mood_modifier'] = seasonal_mood.get(info['seasonal_idx'], 0) + time_mood.get(info['period'], 0)

    # ── Expected activity ─────────────────────────────────────
    if info['is_sleep_time']:
        info['activity_type'] = 'sleep'
    elif info['is_meal_time']:
        info['activity_type'] = 'meal'
    elif info['period'] in ('morning', 'late_morning', 'afternoon'):
        info['activity_type'] = 'play'
    elif info['period'] == 'wind_down':
        info['activity_type'] = 'rest'
    else:
        info['activity_type'] = 'idle'

    return info


def is_action_timely(action, time_info):
    """
    Check if an action is appropriate for the current time.
    Returns a timeliness bonus (0.0-0.5) added to action quality.
    """
    if action == 'feed' and time_info['is_meal_time']:
        return 0.3 * time_info['meal_urgency']  # Bonus for feeding at meal time
    if action == 'rest' and time_info['period'] in ('wind_down', 'night'):
        return 0.2  # Bonus for resting at bedtime
    if action == 'play' and time_info['activity_type'] == 'play':
        return 0.15  # Bonus for playing during play hours
    if action == 'heal':
        return 0.1  # Healing is always somewhat timely
    return 0.0


def get_sleep_status(hour):
    """Returns sleep phase info for the dino."""
    if hour >= 21 or hour < 5:
        return {'phase': 'deep_sleep', 'can_interact': False, 'message': 'Rex is sleeping soundly... 💤🌙'}
    elif 5 <= hour < 7:
        return {'phase': 'waking', 'can_interact': True, 'message': 'Rex is starting to wake up... 🌅'}
    elif 20 <= hour < 21:
        return {'phase': 'drowsy', 'can_interact': True, 'message': 'Rex is getting sleepy... 😴'}
    else:
        return {'phase': 'awake', 'can_interact': True, 'message': None}
