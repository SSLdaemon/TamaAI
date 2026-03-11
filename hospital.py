"""
TamaAI Hospital Mechanic — State machine for pet hospitalization and recovery.

States: HEALTHY → CRITICAL → HOSPITALIZED → RECOVERING → HEALTHY
"""

import time
from enum import Enum


class HospitalStatus(Enum):
    HEALTHY = "healthy"
    CRITICAL = "critical"
    HOSPITALIZED = "hospitalized"
    RECOVERING = "recovering"


# Thresholds
CRITICAL_HEALTH = 20
HOSPITAL_HEALTH = 10
STARVATION_THRESHOLD = 95
EXHAUSTION_THRESHOLD = 5
EMOTIONAL_CRISIS = 10
RECOVERY_PER_VISIT = 8
DISCHARGE_HEALTH = 35
RECOVERING_DURATION = 3600  # 1 hour of good care after discharge


class HospitalManager:
    """Manages the pet's hospital state machine."""

    def __init__(self):
        self.status = HospitalStatus.HEALTHY
        self.enter_time = None
        self.discharge_time = None
        self.recovery_needed = 0
        self.recovery_done = 0
        self.current_reason = None
        self.visit_count = 0

    def load_state(self, status_str, enter_time, recovery_needed, recovery_done):
        """Load state from database."""
        try:
            self.status = HospitalStatus(status_str)
        except ValueError:
            self.status = HospitalStatus.HEALTHY
        self.enter_time = enter_time
        self.recovery_needed = recovery_needed
        self.recovery_done = recovery_done

    def check_status(self, stats):
        """
        Check if pet should transition states based on current stats.

        Args:
            stats: dict with health, hunger, mood, energy

        Returns:
            dict with status change info or None
        """
        health = stats.get('health', 100)
        hunger = stats.get('hunger', 0)
        energy = stats.get('energy', 100)
        mood = stats.get('mood', 100)

        # ── HEALTHY → CRITICAL ────────────────────────────────
        if self.status == HospitalStatus.HEALTHY:
            if health <= CRITICAL_HEALTH:
                self.status = HospitalStatus.CRITICAL
                return {'transition': 'critical', 'reason': 'low_health',
                        'message': 'Rex is not feeling well! Please take care of him! 🚨'}
            if hunger >= STARVATION_THRESHOLD:
                self.status = HospitalStatus.CRITICAL
                return {'transition': 'critical', 'reason': 'starvation',
                        'message': 'Rex is extremely hungry! Feed him now! 🚨🍖'}
            if energy <= EXHAUSTION_THRESHOLD:
                self.status = HospitalStatus.CRITICAL
                return {'transition': 'critical', 'reason': 'exhaustion',
                        'message': 'Rex is completely exhausted! Let him rest! 🚨😴'}

        # ── CRITICAL → HOSPITALIZED ───────────────────────────
        if self.status == HospitalStatus.CRITICAL:
            reason = None
            if health <= HOSPITAL_HEALTH:
                reason = 'critical_health'
            elif hunger >= 100:
                reason = 'starvation'
            elif energy <= 0:
                reason = 'exhaustion'
            elif mood <= EMOTIONAL_CRISIS and health <= CRITICAL_HEALTH:
                reason = 'emotional_crisis'

            if reason:
                return self._admit(reason)

            # CRITICAL → HEALTHY (recovered without hospitalization)
            if health > CRITICAL_HEALTH + 10 and hunger < STARVATION_THRESHOLD - 10 and energy > EXHAUSTION_THRESHOLD + 10:
                self.status = HospitalStatus.HEALTHY
                return {'transition': 'recovered', 'reason': 'care_improved',
                        'message': 'Rex is feeling better! Great care! 💚'}

        # ── HOSPITALIZED checks ───────────────────────────────
        if self.status == HospitalStatus.HOSPITALIZED:
            if self.recovery_done >= self.recovery_needed:
                return self._discharge()

        # ── RECOVERING → HEALTHY ──────────────────────────────
        if self.status == HospitalStatus.RECOVERING:
            if self.discharge_time and (time.time() - self.discharge_time) > RECOVERING_DURATION:
                if health > DISCHARGE_HEALTH:
                    self.status = HospitalStatus.HEALTHY
                    return {'transition': 'fully_recovered',
                            'message': 'Rex has fully recovered! Welcome back buddy! 🦕🎉'}

        return None

    def _admit(self, reason):
        """Admit pet to hospital."""
        self.status = HospitalStatus.HOSPITALIZED
        self.enter_time = time.time()
        self.current_reason = reason
        self.recovery_needed = 4  # Must visit 4 times
        self.recovery_done = 0
        self.visit_count += 1

        reason_messages = {
            'critical_health': 'Rex had to go to the hospital because his health got too low! 🏥',
            'starvation': 'Rex had to go to the hospital because he was starving! 🏥🍖',
            'exhaustion': 'Rex collapsed from exhaustion and is in the hospital! 🏥😴',
            'emotional_crisis': 'Rex is in the hospital — he needs love and care! 🏥💔',
        }

        return {
            'transition': 'hospitalized',
            'reason': reason,
            'message': reason_messages.get(reason, 'Rex is in the hospital! 🏥'),
            'recovery_needed': self.recovery_needed,
        }

    def record_visit(self):
        """
        Record a hospital visit (child caring for sick pet).
        Returns health recovery amount and whether discharged.
        """
        if self.status != HospitalStatus.HOSPITALIZED:
            return {'error': 'Pet is not hospitalized', 'health_delta': 0}

        self.recovery_done += 1
        health_delta = RECOVERY_PER_VISIT

        result = {
            'health_delta': health_delta,
            'recovery_done': self.recovery_done,
            'recovery_needed': self.recovery_needed,
            'discharged': False,
            'message': f'Visit {self.recovery_done}/{self.recovery_needed}: Rex appreciates your care! 💊💚',
        }

        if self.recovery_done >= self.recovery_needed:
            discharge = self._discharge()
            result['discharged'] = True
            result['message'] = discharge['message']

        return result

    def _discharge(self):
        """Discharge pet from hospital."""
        self.status = HospitalStatus.RECOVERING
        self.discharge_time = time.time()
        return {
            'transition': 'recovering',
            'message': 'Rex is leaving the hospital! Keep taking good care of him! 🏥→🏠💚',
        }

    def get_state(self):
        """Return serializable state."""
        return {
            'status': self.status.value,
            'enter_time': self.enter_time,
            'discharge_time': self.discharge_time,
            'recovery_needed': self.recovery_needed,
            'recovery_done': self.recovery_done,
            'current_reason': self.current_reason,
            'is_hospitalized': self.status == HospitalStatus.HOSPITALIZED,
            'is_critical': self.status == HospitalStatus.CRITICAL,
            'is_recovering': self.status == HospitalStatus.RECOVERING,
            'total_visits': self.visit_count,
        }

    def get_hospital_message(self):
        """Get contextual message for hospital state."""
        if self.status == HospitalStatus.HOSPITALIZED:
            remaining = self.recovery_needed - self.recovery_done
            return f"Rex is in the hospital. Visit {remaining} more time{'s' if remaining != 1 else ''} to help him recover! 🏥"
        elif self.status == HospitalStatus.CRITICAL:
            return "Rex is in critical condition! Take care of him before he needs the hospital! 🚨"
        elif self.status == HospitalStatus.RECOVERING:
            return "Rex just got out of the hospital. Be extra gentle with him! 💚"
        return None
