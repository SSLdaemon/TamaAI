"""
TamaAI Game State Manager v2

Integrates: Bayesian network, time-of-day sync, hospital mechanic,
database persistence, neglect tracking.
"""

import time
import json
import numpy as np
from datetime import datetime
from bayesian_model import BayesianPetModel
from time_sync import get_current_time_info, is_action_timely, get_sleep_status, MEAL_WINDOWS
from hospital import HospitalManager, HospitalStatus
import database as db


class GameState:
    """Manages the full state of a TamaAI pet session with persistence."""

    def __init__(self, pet_id=None):
        self.model = BayesianPetModel()
        self.hospital = HospitalManager()
        self.pet_id = pet_id or db.get_default_pet()
        self._snapshot_interval = 300  # Log stats every 5 minutes
        self._last_snapshot = 0
        self._last_neglect_check = 0
        self._load_or_reset()

    def _load_or_reset(self):
        """Load from DB or initialize fresh state."""
        data = db.load_pet_state(self.pet_id)
        if data and data.get('stats_json'):
            self.pet_name = data.get('name', 'Rex')
            self.created_at = data.get('created_at', time.time())
            self.last_update = data.get('last_update', time.time())
            self.action_count = data.get('action_count', 0)
            self.stats = json.loads(data['stats_json'])
            self.outcomes = json.loads(data['outcomes_json'])
            self.total_hospital_visits = data.get('total_hospital_visits', 0)

            # Load score histories
            self._feeding_scores = json.loads(data.get('feeding_scores_json') or '[]')
            self._healthcare_scores = json.loads(data.get('healthcare_scores_json') or '[]')
            self._emotional_scores = json.loads(data.get('emotional_scores_json') or '[]')
            self._rest_scores = json.loads(data.get('rest_scores_json') or '[]')

            self.last_action = None
            self.last_message = "Welcome back!"

            # Load hospital state
            self.hospital.load_state(
                data.get('hospital_status', 'healthy'),
                data.get('hospital_enter_time'),
                data.get('hospital_recovery_needed', 0),
                data.get('hospital_recovery_done', 0)
            )
        else:
            self.reset()

    def reset(self):
        """Reset pet to initial happy state."""
        self.pet_name = "Rex"
        self.created_at = time.time()
        self.last_update = time.time()
        self.action_count = 0
        self.total_hospital_visits = 0

        self.stats = {
            'health': 80.0,
            'hunger': 30.0,
            'mood': 75.0,
            'energy': 70.0,
        }

        self.outcomes = {
            'empathy': 50.0,
            'responsibility': 50.0,
            'punctuality': 50.0,
            'wellbeing': 60.0,
        }

        self._feeding_scores = []
        self._healthcare_scores = []
        self._emotional_scores = []
        self._rest_scores = []

        self.hospital = HospitalManager()

        self.expression = 'happy'
        self.last_action = None
        self.last_message = "Rex the dinosaur is ready to play! 🦕"
        self._save()

    def _save(self):
        """Persist state to database."""
        db.save_pet_state(
            self.pet_id, self.stats, self.outcomes,
            self.hospital.status.value, self.hospital.enter_time,
            self.hospital.recovery_needed, self.hospital.recovery_done,
            self.action_count, self.total_hospital_visits,
            self._feeding_scores, self._healthcare_scores,
            self._emotional_scores, self._rest_scores
        )

    def _apply_time_decay(self):
        """Apply time-based stat changes, synced to child's daily schedule."""
        now = time.time()
        elapsed = now - self.last_update
        self.last_update = now
        minutes = elapsed / 60.0

        # Cap decay to prevent huge jumps if server was off
        minutes = min(minutes, 30)

        time_info = get_current_time_info()
        sleep_status = get_sleep_status(time_info['hour'])

        # ── Hunger (builds faster at meal times) ──────────────
        hunger_rate = 0.15 * time_info['hunger_multiplier']
        self.stats['hunger'] = min(100, self.stats['hunger'] + minutes * hunger_rate)

        # ── Energy (drains during day, recovers during sleep) ─
        energy_mult = time_info['energy_multiplier']
        if energy_mult < 0:
            # Sleep recovery
            self.stats['energy'] = min(100, self.stats['energy'] + minutes * abs(energy_mult))
        else:
            self.stats['energy'] = max(0, self.stats['energy'] - minutes * energy_mult)

        # ── Mood (affected by needs and time) ─────────────────
        mood_pressure = 0
        if self.stats['hunger'] > 60:
            mood_pressure += 1.0
        if self.stats['energy'] < 25:
            mood_pressure += 0.8
        if self.stats['health'] < 30:
            mood_pressure += 1.5

        # Time-of-day mood shift
        mood_shift = time_info['mood_modifier'] * 2  # Can be positive
        self.stats['mood'] = np.clip(
            self.stats['mood'] - minutes * mood_pressure + minutes * mood_shift,
            0, 100
        )

        # ── Health (degrades from neglect) ────────────────────
        health_pressure = 0
        if self.stats['hunger'] > 80:
            health_pressure += 0.8
        if self.stats['energy'] < 10:
            health_pressure += 0.5
        if self.stats['mood'] < 15:
            health_pressure += 0.3

        # Recovering pets have slower health drain
        if self.hospital.status == HospitalStatus.RECOVERING:
            health_pressure *= 0.5

        self.stats['health'] = max(0, self.stats['health'] - minutes * health_pressure)

        # ── Hospital check ────────────────────────────────────
        transition = self.hospital.check_status(self.stats)
        if transition:
            self.last_message = transition.get('message', self.last_message)
            if transition.get('transition') == 'hospitalized':
                self.total_hospital_visits += 1
                reason = transition.get('reason', 'unknown')
                db.log_hospital_visit(self.pet_id, reason, self.hospital.recovery_needed)
                db.log_neglect(self.pet_id, reason, 8, f"Hospitalized: {reason}")

        # ── Periodic snapshots & neglect checks ───────────────
        if now - self._last_snapshot > self._snapshot_interval:
            self._last_snapshot = now
            db.log_stats_snapshot(self.pet_id, time_info['hour'], self.stats, self.outcomes)

        if now - self._last_neglect_check > 600:  # Every 10 min
            self._last_neglect_check = now
            self._check_neglect(time_info)

    def _check_neglect(self, time_info):
        """Check for neglect patterns and log them."""
        # Missed meal check
        if time_info['is_meal_time'] and self.stats['hunger'] > 70:
            meal = time_info.get('current_meal', 'meal')
            db.log_neglect(self.pet_id, 'missed_meal', 5, f"Hungry during {meal} time")

        # Sleep deprivation
        if time_info['is_sleep_time'] and self.stats['energy'] < 20:
            db.log_neglect(self.pet_id, 'sleep_deprivation', 4, "Low energy during sleep hours")

        # Emotional neglect
        if self.stats['mood'] < 20:
            db.log_neglect(self.pet_id, 'emotional_neglect', 6, f"Mood critically low: {self.stats['mood']:.0f}")

    def _compute_action_quality(self, action, time_info):
        """Compute how good an action is given current state + time context."""
        base_quality = 0.0

        if action == 'feed':
            base_quality = min(1.0, self.stats['hunger'] / 80.0)
        elif action == 'heal':
            base_quality = min(1.0, (100 - self.stats['health']) / 60.0)
        elif action == 'play':
            mood_need = (100 - self.stats['mood']) / 80.0
            energy_ok = self.stats['energy'] / 100.0
            base_quality = min(1.0, mood_need * 0.7 + energy_ok * 0.3)
        elif action == 'rest':
            base_quality = min(1.0, (100 - self.stats['energy']) / 70.0)

        # Timeliness bonus
        timeliness = is_action_timely(action, time_info)
        return min(1.0, base_quality + timeliness)

    def _update_expression(self):
        """Determine the dino's visual expression."""
        if self.hospital.status == HospitalStatus.HOSPITALIZED:
            self.expression = 'hospital'
        elif self.hospital.status == HospitalStatus.CRITICAL:
            self.expression = 'sick'
        elif self.hospital.status == HospitalStatus.RECOVERING:
            self.expression = 'recovering'
        elif self.stats['health'] < 25:
            self.expression = 'sick'
        elif self.stats['hunger'] > 75:
            self.expression = 'hungry'
        elif self.stats['energy'] < 20:
            self.expression = 'sleepy'
        elif self.stats['hunger'] < 15 and self.stats['health'] < 90:
            self.expression = 'nauseous'
        elif self.stats['mood'] > 70:
            self.expression = 'happy'
        elif self.stats['mood'] > 40:
            self.expression = 'neutral'
        else:
            self.expression = 'sad'

        # Override with sleep if it's bedtime and pet has energy
        time_info = get_current_time_info()
        sleep = get_sleep_status(time_info['hour'])
        if sleep['phase'] == 'deep_sleep' and self.hospital.status == HospitalStatus.HEALTHY:
            self.expression = 'sleeping'

    def _update_outcomes(self, time_info, overfed=False):
        """Run Bayesian inference to update character-building outcomes."""
        def avg(lst, default=0.5):
            return sum(lst[-10:]) / len(lst[-10:]) if lst else default

        action_scores = {
            'feeding_quality': avg(self._feeding_scores),
            'healthcare_quality': avg(self._healthcare_scores),
            'emotional_quality': avg(self._emotional_scores),
            'rest_quality': avg(self._rest_scores),
        }

        results = self.model.compute_outcomes(action_scores, time_info, overfed=overfed)

        blend = 0.3
        for key in self.outcomes:
            if key in results:
                self.outcomes[key] = self.outcomes[key] * (1 - blend) + results[key] * blend

    def perform_action(self, action):
        """Process a player action. Returns updated state dict."""
        self._apply_time_decay()
        time_info = get_current_time_info()

        # Can't perform normal actions while hospitalized
        if self.hospital.status == HospitalStatus.HOSPITALIZED and action != 'visit':
            return self.get_state()

        # Hospital visit action
        if action == 'visit' and self.hospital.status == HospitalStatus.HOSPITALIZED:
            result = self.hospital.record_visit()
            self.stats['health'] = min(100, self.stats['health'] + result['health_delta'])
            self.stats['mood'] = min(100, self.stats['mood'] + 5)
            self.last_message = result['message']
            self.last_action = 'visit'
            self._emotional_scores.append(0.8)  # Visiting shows empathy

            if result['discharged']:
                db.discharge_hospital(self.pet_id)

            self.action_count += 1
            self._update_outcomes(time_info)
            self._update_expression()
            self._save()
            return self.get_state()

        # Sleep check — limited interaction during deep sleep
        sleep = get_sleep_status(time_info['hour'])
        if sleep['phase'] == 'deep_sleep' and action in ('play',):
            self.last_message = "Rex is sleeping... let him rest! 🌙💤"
            return self.get_state()

        self.action_count += 1
        stats_before = dict(self.stats)
        quality = self._compute_action_quality(action, time_info)

        # ── Apply action effects ──────────────────────────────
        if action == 'feed':
            if self.stats['hunger'] < 20:
                # Overfeeding!
                self.stats['hunger'] = 0
                self.stats['health'] = max(0, self.stats['health'] - 10)
                self.stats['mood'] = max(0, self.stats['mood'] - 10)
                self.last_message = "Rex ate too much... he looks sick... 🤢"
                self._feeding_scores.append(0.1) # Poor quality feed
                quality = 0.0 # For Bayesian update
            else:
                reduction = 25 + quality * 15
                self.stats['hunger'] = max(0, self.stats['hunger'] - reduction)
                self.stats['mood'] = min(100, self.stats['mood'] + 5)
                self._feeding_scores.append(quality)

                if time_info['is_meal_time']:
                    meal = time_info.get('current_meal', 'meal')
                    if quality > 0.6:
                        self.last_message = f"Perfect {meal} time! Rex gobbles it up! 🍖✨"
                    else:
                        self.last_message = f"Rex eats his {meal}! 🍖"
                elif quality > 0.6:
                    self.last_message = "Rex gobbles up the food! Perfect timing! 🍖✨"
                elif quality > 0.3:
                    self.last_message = "Rex munches happily! 🍖"
                else:
                    self.last_message = "Rex nibbles a little... not very hungry right now 🍖"

        elif action == 'play':
            self.stats['mood'] = min(100, self.stats['mood'] + 20 + quality * 10)
            self.stats['energy'] = max(0, self.stats['energy'] - 12)
            self.stats['hunger'] = min(100, self.stats['hunger'] + 5)
            self._emotional_scores.append(quality)

            if self.stats['energy'] < 20:
                self.last_message = "Rex tries to play but yawns... maybe rest first? 😴"
            elif quality > 0.5:
                self.last_message = "Rex ROARS with joy! What a great time! 🎮🦕"
            else:
                self.last_message = "Rex plays around happily! 🎮"

        elif action == 'rest':
            recovery = 20 + quality * 15
            self.stats['energy'] = min(100, self.stats['energy'] + recovery)
            self.stats['mood'] = min(100, self.stats['mood'] + 3)
            self._rest_scores.append(quality)

            if time_info['period'] in ('wind_down', 'night'):
                self.last_message = "Good night Rex! Sweet dreams! 😴🌙✨"
            elif quality > 0.6:
                self.last_message = "Rex needed that nap! Feeling refreshed! 😴💤✨"
            else:
                self.last_message = "Rex takes a little rest... 😴"

        elif action == 'heal':
            self.stats['health'] = min(100, self.stats['health'] + 20 + quality * 15)
            self.stats['mood'] = min(100, self.stats['mood'] + 5)
            self._healthcare_scores.append(quality)

            if quality > 0.5:
                self.last_message = "Great care! Rex is feeling much better! 💊💚"
            else:
                self.last_message = "Rex appreciates the checkup! 💊"

        self.last_action = action

        # Log action
        db.log_action(self.pet_id, action, quality, time_info['hour'],
                       stats_before, dict(self.stats))

        # Update Bayesian outcomes
        is_overfed = (action == 'feed' and stats_before['hunger'] < 20)
        self._update_outcomes(time_info, overfed=is_overfed)

        # Check hospital transitions
        transition = self.hospital.check_status(self.stats)
        if transition:
            self.last_message = transition.get('message', self.last_message)
            if transition.get('transition') == 'hospitalized':
                self.total_hospital_visits += 1
                reason = transition.get('reason', 'unknown')
                db.log_hospital_visit(self.pet_id, reason, self.hospital.recovery_needed)
                
                # ── MCP Memory: Store hospital visit as core memory ──
                try:
                    from mcp_manager import mcp_manager
                    if mcp_manager and mcp_manager.client:
                        mcp_manager.call_tool_sync('memory', 'create_entities', {
                            'entities': [{
                                'name': f'hospital_visit_{self.total_hospital_visits}_{int(time.time())}',
                                'entityType': 'event',
                                'observations': [
                                    f'Rex was hospitalized on {datetime.now().strftime("%Y-%m-%d %H:%M")}',
                                    f'Reason: {reason}',
                                    f'Recovery hours needed: {self.hospital.recovery_needed}',
                                    f'Total hospital visits: {self.total_hospital_visits}',
                                    f'Stats at admission - Health: {stats_before["health"]:.0f}, Mood: {stats_before["mood"]:.0f}'
                                ]
                            }]
                        })
                except Exception as e:
                    # MCP optional - don't break game if unavailable
                    print(f"Memory MCP unavailable: {e}")


        self._update_expression()
        self._save()
        return self.get_state()

    def get_state(self):
        """Return the full current state as JSON-serializable dict."""
        self._apply_time_decay()
        self._update_expression()

        time_info = get_current_time_info()
        sleep = get_sleep_status(time_info['hour'])
        hospital_state = self.hospital.get_state()
        hospital_msg = self.hospital.get_hospital_message()

        # Determine available actions
        if hospital_state['is_hospitalized']:
            available_actions = ['visit']
        elif sleep['phase'] == 'deep_sleep':
            available_actions = ['feed', 'rest', 'heal']  # No play during deep sleep
        else:
            available_actions = ['feed', 'play', 'rest', 'heal']

        return {
            'pet_name': self.pet_name,
            'stats': {k: round(v, 1) for k, v in self.stats.items()},
            'outcomes': {k: round(v, 1) for k, v in self.outcomes.items()},
            'expression': self.expression,
            'last_action': self.last_action,
            'last_message': hospital_msg or self.last_message,
            'action_count': self.action_count,
            'age_minutes': round((time.time() - self.created_at) / 60, 1),
            'hospital': hospital_state,
            'time': {
                'hour': time_info['hour'],
                'period': time_info['period'],
                'is_sleep_time': time_info['is_sleep_time'],
                'is_meal_time': time_info['is_meal_time'],
                'current_meal': time_info.get('current_meal'),
                'activity_type': time_info['activity_type'],
                'sleep_phase': sleep['phase'],
            },
            'available_actions': available_actions,
            'total_hospital_visits': self.total_hospital_visits,
        }
