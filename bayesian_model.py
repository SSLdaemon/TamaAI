"""
TamaAI Bayesian Network v2 — Full CPD implementation with time awareness.

Faithfully replicates the original pgmpy network structure:
  Environmental factors → Pet internal states → Child responses →
  Character-building outcomes → Pet well-being

Enhanced with time-of-day conditioning for realistic child schedule sync.
"""

import numpy as np
from time_sync import get_current_time_info


class BayesianPetModel:
    """
    Full Bayesian network for TamaAI with proper conditional probability tables.
    Uses numpy for efficient computation without heavy ML dependencies.
    """

    def __init__(self):
        self._build_cpds()

    def _build_cpds(self):
        """Build all Conditional Probability Distribution tables."""

        # ═══════════════════════════════════════════════════════════
        # LAYER 1: Environmental Factor Priors
        # ═══════════════════════════════════════════════════════════

        # Temperature: [cold, mild, hot]
        self.p_temperature = np.array([0.3, 0.4, 0.3])

        # Light: [dark, bright]
        self.p_light = np.array([0.5, 0.5])

        # Seasonal Changes: [spring, summer, autumn, winter]
        self.p_seasonal = np.array([0.25, 0.25, 0.25, 0.25])

        # ═══════════════════════════════════════════════════════════
        # LAYER 2: Pet Internal States (conditioned on environment)
        # ═══════════════════════════════════════════════════════════

        # Hunger | Temperature
        # Rows: [not_hungry, hungry], Cols: [cold, mild, hot]
        self.cpd_hunger = np.array([
            [0.3, 0.7, 0.5],   # P(not_hungry | temp)
            [0.7, 0.3, 0.5],   # P(hungry | temp)
        ])

        # Illness: [healthy, sick] — prior, modified by care history
        self.p_illness_base = np.array([0.8, 0.2])

        # Mood | Seasonal Changes
        # Rows: [happy, neutral, sad], Cols: [spring, summer, autumn, winter]
        self.cpd_mood = np.array([
            [0.6, 0.4, 0.7, 0.6],   # P(happy | season)
            [0.1, 0.2, 0.1, 0.1],   # P(neutral | season)
            [0.3, 0.4, 0.2, 0.3],   # P(sad | season)
        ])

        # Tiredness | Light
        # Rows: [rested, tired], Cols: [dark, bright]
        self.cpd_tiredness = np.array([
            [0.4, 0.6],   # P(rested | light)
            [0.6, 0.4],   # P(tired | light)
        ])

        # ═══════════════════════════════════════════════════════════
        # LAYER 3: Child Response Quality CPDs
        # ═══════════════════════════════════════════════════════════

        # Feeding Response | Hunger
        # Rows: [good, adequate, poor], Cols: [not_hungry, hungry]
        self.cpd_feeding_response = np.array([
            [0.7, 0.3],    # P(good_feed | hunger)
            [0.2, 0.7],    # P(adequate_feed | hunger)
            [0.1, 0.0],    # P(poor_feed | hunger)
        ])

        # Health Care Response | Illness
        # Rows: [good, adequate, poor], Cols: [healthy, sick]
        self.cpd_healthcare_response = np.array([
            [0.8, 0.2],
            [0.15, 0.8],
            [0.05, 0.0],
        ])

        # Emotional Response | Mood
        # Rows: [good, adequate, poor], Cols: [happy, neutral, sad]
        self.cpd_emotional_response = np.array([
            [0.6, 0.4, 0.6],
            [0.3, 0.6, 0.4],
            [0.1, 0.0, 0.0],
        ])

        # Rest Actions | Tiredness
        # Rows: [good, adequate, poor], Cols: [rested, tired]
        self.cpd_rest_actions = np.array([
            [0.7, 0.2],
            [0.2, 0.5],
            [0.1, 0.3],
        ])

        # ═══════════════════════════════════════════════════════════
        # LAYER 4: Character-Building Outcomes
        # ═══════════════════════════════════════════════════════════

        # Punctuality | Feeding Response × Health Care × Rest Actions
        # Simplified: weighted combination of response quality indices
        self.punctuality_weights = {
            'feeding': 0.4,
            'healthcare': 0.3,
            'rest': 0.3,
        }

        # Empathy | Emotional Response
        self.empathy_weights = {
            'emotional': 0.7,
            'feeding': 0.15,
            'healthcare': 0.15,
        }

        # Responsibility | All responses
        self.responsibility_weights = {
            'feeding': 0.3,
            'healthcare': 0.25,
            'rest': 0.25,
            'emotional': 0.2,
        }

        # Well-being | Punctuality × Empathy × Responsibility
        self.wellbeing_weights = {
            'punctuality': 0.35,
            'empathy': 0.35,
            'responsibility': 0.30,
        }

    # ═══════════════════════════════════════════════════════════════
    # INFERENCE METHODS
    # ═══════════════════════════════════════════════════════════════

    def compute_pet_states(self, time_info=None):
        """
        Compute pet internal state probabilities given environmental factors.

        Args:
            time_info: dict from time_sync.get_time_info() or None to marginalize
        """
        if time_info:
            temp_idx = time_info.get('temperature_idx', 1)
            p_hunger = self.cpd_hunger[:, temp_idx]

            light_idx = time_info.get('light_idx', 1)
            p_tiredness = self.cpd_tiredness[:, light_idx]

            seasonal_idx = time_info.get('seasonal_idx', 0)
            p_mood = self.cpd_mood[:, seasonal_idx]

            # Adjust mood by time-of-day modifier
            mood_mod = time_info.get('mood_modifier', 0)
            p_mood = np.array([
                np.clip(p_mood[0] + mood_mod, 0.05, 0.95),
                p_mood[1],
                np.clip(p_mood[2] - mood_mod, 0.05, 0.95),
            ])
            p_mood = p_mood / p_mood.sum()  # Renormalize

            # During sleep, tiredness shifts strongly toward tired (natural)
            if time_info.get('is_sleep_time'):
                p_tiredness = np.array([0.2, 0.8])
        else:
            p_hunger = self.cpd_hunger @ self.p_temperature
            p_tiredness = self.cpd_tiredness @ self.p_light
            p_mood = self.cpd_mood @ self.p_seasonal

        return {
            'hunger': p_hunger,
            'illness': self.p_illness_base.copy(),
            'mood': p_mood,
            'tiredness': p_tiredness,
        }

    def compute_response_quality(self, pet_states, action_scores):
        """
        Given pet states and action quality scores (0-1 per action type),
        compute the expected response quality distributions.
        """
        # Map action scores to response distribution indices
        # Higher action quality → more weight on "good" response
        def score_to_response_dist(score):
            """Convert 0-1 quality score to [good, adequate, poor] distribution."""
            good = np.clip(score * 0.8 + 0.1, 0, 1)
            poor = np.clip((1 - score) * 0.3, 0, 0.5)
            adequate = 1.0 - good - poor
            return np.array([good, max(0, adequate), poor])

        feeding_dist = score_to_response_dist(action_scores.get('feeding_quality', 0.5))
        healthcare_dist = score_to_response_dist(action_scores.get('healthcare_quality', 0.5))
        emotional_dist = score_to_response_dist(action_scores.get('emotional_quality', 0.5))
        rest_dist = score_to_response_dist(action_scores.get('rest_quality', 0.5))

        return {
            'feeding': feeding_dist,
            'healthcare': healthcare_dist,
            'emotional': emotional_dist,
            'rest': rest_dist,
        }

    def compute_outcomes(self, action_scores, time_info=None, overfed=False):
        """
        Full Bayesian inference through all network layers.

        Args:
            action_scores: dict with feeding_quality, healthcare_quality,
                          emotional_quality, rest_quality (each 0-1)
            time_info: optional time context for environmental conditioning
            overfed: boolean, true if recent action was overfeeding
        Returns:
            dict of character outcomes (0-100 scale)
        """
        pet_states = self.compute_pet_states(time_info)
        responses = self.compute_response_quality(pet_states, action_scores)

        # Compute expected quality index for each response (0=good, 1=adequate, 2=poor)
        # Map to 0-1 scale where 1 = best
        quality_values = np.array([1.0, 0.5, 0.0])  # good=1, adequate=0.5, poor=0

        feed_q = np.dot(responses['feeding'], quality_values)
        health_q = np.dot(responses['healthcare'], quality_values)
        emotional_q = np.dot(responses['emotional'], quality_values)
        rest_q = np.dot(responses['rest'], quality_values)

        # ── Character-Building Outcomes ───────────────────────────

        punctuality = (
            self.punctuality_weights['feeding'] * feed_q +
            self.punctuality_weights['healthcare'] * health_q +
            self.punctuality_weights['rest'] * rest_q
        )

        empathy = (
            self.empathy_weights['emotional'] * emotional_q +
            self.empathy_weights['feeding'] * feed_q +
            self.empathy_weights['healthcare'] * health_q
        )

        responsibility = (
            self.responsibility_weights['feeding'] * feed_q +
            self.responsibility_weights['healthcare'] * health_q +
            self.responsibility_weights['rest'] * rest_q +
            self.responsibility_weights['emotional'] * emotional_q
        )

        # ── Pet Well-being (final node) ──────────────────────────
        wellbeing = (
            self.wellbeing_weights['punctuality'] * punctuality +
            self.wellbeing_weights['empathy'] * empathy +
            self.wellbeing_weights['responsibility'] * responsibility
        )

        # Apply timeliness bonus: caring at the right time boosts outcomes
        timeliness_bonus = 0
        if time_info and time_info.get('is_meal_time'):
            timeliness_bonus += 0.05 * action_scores.get('feeding_quality', 0)
        if time_info and time_info.get('period') == 'wind_down':
            timeliness_bonus += 0.03 * action_scores.get('rest_quality', 0)

        # Overfeeding penalty
        if overfed:
            responsibility *= 0.8
            wellbeing *= 0.9

        return {
            'punctuality': float(np.clip((punctuality + timeliness_bonus) * 100, 0, 100)),
            'empathy': float(np.clip(empathy * 100, 0, 100)),
            'responsibility': float(np.clip((responsibility + timeliness_bonus * 0.5) * 100, 0, 100)),
            'wellbeing': float(np.clip((wellbeing + timeliness_bonus) * 100, 0, 100)),
        }

    def get_illness_probability(self, healthcare_quality, consecutive_neglect_hours=0):
        """
        Compute illness probability based on care quality and neglect duration.
        Returns probability of being sick (0-1).
        """
        base_sick = self.p_illness_base[1]  # 0.2 base
        care_factor = (1 - healthcare_quality) * 0.3  # Poor care increases illness
        neglect_factor = min(0.4, consecutive_neglect_hours * 0.02)  # Neglect builds up
        return float(np.clip(base_sick + care_factor + neglect_factor, 0, 0.9))
