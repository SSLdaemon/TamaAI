
import sys
import os
import time

# Add current directory to path
sys.path.append(os.getcwd())

from game_state import GameState

def verify_overfeeding():
    print("--- Verifying Overfeeding Logic ---")
    game = GameState()
    
    # 1. Reset state
    print("Resetting game state...")
    # game._reset_state() # Method does not exist, setting manually
    game.stats['hunger'] = 50
    game.stats['health'] = 100
    game.stats['mood'] = 50
    
    print(f"Initial State: Hunger={game.stats['hunger']}, Health={game.stats['health']}")
    
    # 2. Feed until full
    print("\nFeeding until full...")
    # Feed once (reduces by ~25-40)
    game.perform_action('feed')
    print(f"After feed 1: Hunger={game.stats['hunger']}")
    
    if game.stats['hunger'] > 20:
        game.perform_action('feed')
        print(f"After feed 2: Hunger={game.stats['hunger']}")
        
    # Ensure we are 'full' (hunger < 20)
    game.stats['hunger'] = 10
    print(f"Forced Hunger to 10 for test. State: Hunger={game.stats['hunger']}")
    
    # 3. Overfeed
    print("\nAttempting to overfeed...")
    prev_health = game.stats['health']
    print(f"Pre-overfeed: Hunger={game.stats['hunger']}, Health={game.stats['health']}")
    
    state = game.perform_action('feed')
    
    curr_health = game.stats['health']
    curr_hunger = game.stats['hunger']
    msg = game.last_message
    
    print(f"Post-Overfeed State (attr): Hunger={curr_hunger}, Health={curr_health}")
    print(f"Post-Overfeed State (returned): Hunger={state['stats']['hunger']}, Health={state['stats']['health']}")
    print(f"Message: {msg}")
    
    # Checks
    passed = True
    if curr_health < prev_health:
        print("✅ Health decreased.")
    else:
        print("❌ Health did not decrease.")
        passed = False
        
    if "sick" in msg or "too much" in msg:
        print("✅ Message indicates sickness.")
    else:
        print("❌ Message incorrect.")
        passed = False
        
    if curr_hunger < 0.1:
        print("✅ Hunger set to ~0.")
    else:
        print("❌ Hunger not ~0.")
        passed = False
        
    # Check expression logic
    print("\nChecking expression logic...")
    # Health needs to be < 90 AND hunger < 15 for nauseous
    # We just reduced health by 10 (from 100 -> 90). It needs to be < 90.
    # Let's damage health more to trigger expression
    game.stats['health'] = 80
    game.stats['hunger'] = 10
    game._update_expression()
    print(f"Expression with Health=80, Hunger=10: {game.expression}")
    
    if game.expression == 'nauseous':
        print("✅ Expression is 'nauseous'.")
    else:
        print(f"❌ Expression is '{game.expression}', expected 'nauseous'.")
        passed = False
        
    # Check outcomes penalty
    # We need to simulate the Bayesian model update
    # The 'perform_action' calls 'model.compute_outcomes' with 'overfed=True'
    # We can't easily check internal Bayesian state without inspecting return values or mocks,
    # but we can check if responsibility/wellbeing seem low or if code ran without error.
    print("\nBayesian integration ran without error.")

    if passed:
        print("\n🎉 Verification PASSED!")
    else:
        print("\n💥 Verification FAILED.")

if __name__ == "__main__":
    verify_overfeeding()
