"""Comprehensive test script: Retry Loop + Multi-Round Stability."""

from server.environment import NationEnvironment
from server.models import ParliamentaryAction
from schemas.phases import Phase

def run_combined_test():
    env = NationEnvironment(seed=42)
    obs, _ = env.reset()
    departments = env.departments
    
    print("=== STARTING COMPREHENSIVE SIMULATION TEST ===")
    
    # --- ROUND 1: THE RETRY SCENARIO ---
    print(f"\n[ROUND {obs.round}] Starting Phase: {obs.phase_name}")
    
    # 1. Debate
    obs, _, _, _, _ = env.step(ParliamentaryAction(agent_id=departments[0], type="DEBATE", message="Crisis debate"))
    obs, _, _, _, _ = env.step(ParliamentaryAction(agent_id=departments[0], type="DEBATE", message="")) # End debate
    
    # 2. Proposals
    for dept in departments:
        obs, _, _, _, _ = env.step(ParliamentaryAction(
            agent_id=dept, type="PROPOSE_BUDGET", department=dept, amount=150.0, justification="Greedy request"
        ))
    
    # 3. Voting (VOTE NO to trigger retry)
    print(f"Current Phase: {obs.phase_name}. Agents voting NO...")
    while obs.phase_name == "VOTING":
        dept = obs.current_agent
        target = next((p for p in obs.proposals if dept != p.agent_id and dept not in p.votes), None)
        if target:
            obs, _, _, _, _ = env.step(ParliamentaryAction(agent_id=dept, type="VOTE", proposal_id=target.proposal_id, vote="NO"))
        else: break
        
    print(f"Transitioned to: {obs.phase_name} (Retry Count: {obs.retry_count})")
    if obs.retry_count == 1:
        print("SUCCESS: Retry loop triggered correctly.")
    else:
        print("FAILURE: Retry loop did not trigger.")
        return

    # 4. Re-Proposal (Retry Round)
    print(f"Submiting safer proposals for Retry {obs.retry_count}...")
    for dept in departments:
        obs, _, _, _, _ = env.step(ParliamentaryAction(
            agent_id=dept, type="PROPOSE_BUDGET", department=dept, amount=60.0, justification="Safe request"
        ))
        
    # 5. Voting (VOTE YES to finish round)
    print("Agents voting YES on retry proposals...")
    while obs.phase_name == "VOTING":
        dept = obs.current_agent
        target = next((p for p in obs.proposals if dept != p.agent_id and dept not in p.votes), None)
        if target:
            obs, reward, done, _, info = env.step(ParliamentaryAction(agent_id=dept, type="VOTE", proposal_id=target.proposal_id, vote="YES"))
        else: break

    print(f"Round 1 Complete! Reward: {reward:.4f} | Treasury: {obs.treasury:.2f}")
    
    # --- ROUND 2: NORMAL STABILITY ---
    print(f"\n[ROUND {obs.round}] Phase: {obs.phase_name}")
    
    # Skip debate
    obs, _, _, _, _ = env.step(ParliamentaryAction(agent_id=departments[0], type="DEBATE", message=""))
    
    # Propose
    for dept in departments:
        obs, _, _, _, _ = env.step(ParliamentaryAction(
            agent_id=dept, type="PROPOSE_BUDGET", department=dept, amount=70.0, justification="Normal request"
        ))
        
    # Vote YES
    while obs.phase_name == "VOTING":
        dept = obs.current_agent
        target = next((p for p in obs.proposals if dept != p.agent_id and dept not in p.votes), None)
        if target:
            obs, reward, done, _, info = env.step(ParliamentaryAction(agent_id=dept, type="VOTE", proposal_id=target.proposal_id, vote="YES"))
        else: break

    print(f"Round 2 Complete! Reward: {reward:.4f} | Treasury: {obs.treasury:.2f} | Pop: {obs.population}")
    print("\n=== COMPREHENSIVE TEST FINISHED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_combined_test()
