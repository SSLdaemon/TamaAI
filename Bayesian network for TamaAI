import networkx as nx
import matplotlib.pyplot as plt
from pgmpy.models import BayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.inference import VariableElimination

# Define the Bayesian Network structure
model = BayesianNetwork([
    ('Temperature', 'Hunger'), ('Light', 'Tiredness'), ('Seasonal Changes', 'Mood'),
    ('Hunger', 'Feeding Response'), ('Illness', 'Health Care Response'),
    ('Mood', 'Emotional Response'), ('Tiredness', 'Rest Actions'),
    ('Feeding Response', 'Punctuality'), ('Health Care Response', 'Punctuality'),
    ('Rest Actions', 'Punctuality'), ('Emotional Response', 'Empathy'),
    ('Feeding Response', 'Responsibility'), ('Health Care Response', 'Responsibility'),
    ('Rest Actions', 'Responsibility'), ('Emotional Response', 'Responsibility'),
    ('Punctuality', 'Pet’s Well-being'), ('Empathy', 'Pet’s Well-being'),
    ('Responsibility', 'Pet’s Well-being')
])

# Define CPDs for Environmental Factors
cpd_temperature = TabularCPD(variable='Temperature', variable_card=3, values=[[0.3], [0.4], [0.3]])
cpd_light = TabularCPD(variable='Light', variable_card=2, values=[[0.5], [0.5]])
cpd_seasonal_changes = TabularCPD(variable='Seasonal Changes', variable_card=4, values=[[0.25], [0.25], [0.25], [0.25]])

# Define CPDs for AI Pet Actions
cpd_hunger = TabularCPD(variable='Hunger', variable_card=2,
                        values=[[0.3, 0.7, 0.5], [0.7, 0.3, 0.5]],
                        evidence=['Temperature'], evidence_card=[3])
cpd_illness = TabularCPD(variable='Illness', variable_card=2, values=[[0.2], [0.8]])
cpd_mood = TabularCPD(variable='Mood', variable_card=3,
                      values=[[0.6, 0.4, 0.7, 0.6], [0.1, 0.2, 0.1, 0.1], [0.3, 0.4, 0.2, 0.3]],
                      evidence=['Seasonal Changes'], evidence_card=[4])
cpd_tiredness = TabularCPD(variable='Tiredness', variable_card=2,
                           values=[[0.4, 0.6], [0.6, 0.4]],
                           evidence=['Light'], evidence_card=[2])

# Define CPDs for Children's Responses
cpd_feeding_response = TabularCPD(variable='Feeding Response', variable_card=3,
                                  values=[[0.7, 0.3], [0.2, 0.7], [0.1, 0.0]],
                                  evidence=['Hunger'], evidence_card=[2])
cpd_health_care_response = TabularCPD(variable='Health Care Response', variable_card=3,
                                      values=[[0.8, 0.2], [0.15, 0.8], [0.05, 0.0]],
                                      evidence=['Illness'], evidence_card=[2])
cpd_emotional_response = TabularCPD(variable='Emotional Response', variable_card=3,
                                    values=[[0.6, 0.4, 0.6], [0.3, 0.6, 0.4], [0.1, 0.0, 0.0]],
                                    evidence=['Mood'], evidence_card=[3])
cpd_rest_actions = TabularCPD(variable='Rest Actions', variable_card=3,
                              values=[[0.7, 0.2],  # Adjusted probabilities
                                      [0.2, 0.5],
                                      [0.1, 0.3]],
                              evidence=['Tiredness'], evidence_card=[2])
# Define CPDs for Character-Building Outcomes
cpd_punctuality = TabularCPD(variable='Punctuality', variable_card=3,
                             values=[
                                 # Probabilities for High Punctuality
                                 [0.9, 0.8, 0.8, 0.7, 0.6, 0.6, 0.5, 0.4, 0.4] * 3,
                                 # Probabilities for Medium Punctuality
                                 [0.1, 0.2, 0.2, 0.3, 0.4, 0.4, 0.5, 0.6, 0.6] * 3,
                                 # Probabilities for Low Punctuality
                                 [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0] * 3
                             ],
                             evidence=['Feeding Response', 'Health Care Response', 'Rest Actions'],
                             evidence_card=[3, 3, 3])
cpd_empathy = TabularCPD(variable='Empathy', variable_card=3,
                         values=[[0.7, 0.4, 0.2], [0.2, 0.4, 0.3], [0.1, 0.2, 0.5]],
                         evidence=['Emotional Response'], evidence_card=[3])
cpd_responsibility = TabularCPD(variable='Responsibility', variable_card=3,
                                values=[
                                    # High Responsibility probabilities
                                    [0.8, 0.7, 0.6] * 27,  # Repeating pattern for simplicity
                                    # Medium Responsibility probabilities
                                    [0.15, 0.2, 0.25] * 27,
                                    # Low Responsibility probabilities
                                    [0.05, 0.1, 0.15] * 27
                                ],
                                evidence=['Feeding Response', 'Health Care Response', 'Rest Actions', 'Emotional Response'],
                                evidence_card=[3, 3, 3, 3])
# Define CPD for Feedback Mechanism
cpd_pet_wellbeing = TabularCPD(variable='Pet’s Well-being', variable_card=3,
                               values=[
                                   # High Well-being probabilities
                                   [0.9, 0.85, 0.8] * 9,  # Repeating pattern for simplicity
                                   # Medium Well-being probabilities
                                   [0.1, 0.15, 0.2] * 9,
                                   # Low Well-being probabilities
                                   [0.0, 0.0, 0.0] * 9
                               ],
                               evidence=['Punctuality', 'Empathy', 'Responsibility'],
                               evidence_card=[3, 3, 3])
# Add CPDs to the model
model.add_cpds(cpd_temperature, cpd_light, cpd_seasonal_changes, cpd_hunger, cpd_illness, cpd_mood, cpd_tiredness,
               cpd_feeding_response, cpd_health_care_response, cpd_emotional_response, cpd_rest_actions,
               cpd_punctuality, cpd_empathy, cpd_responsibility, cpd_pet_wellbeing)

# Validate the model
assert model.check_model()

# Create an empty networkx graph
nx_graph = nx.DiGraph()

# Add nodes and edges from the Bayesian Network model
for node in model.nodes():
    nx_graph.add_node(node)

for edge in model.edges():
    nx_graph.add_edge(*edge)

# Draw the graph
plt.figure(figsize=(12, 8))
nx.draw(nx_graph, with_labels=True, node_size=2000, node_color="lightblue", font_size=10, font_weight="bold")
plt.show()
