"""Test script to demonstrate the parliamentary retry loop."""

import sys
from server.environment import NationEnvironment
from server.models import ParliamentaryAction
from schemas.phases import Phase
from schemas.actions import ActionType

def test_retry_loop():
    print("Initializing environment...", flush=True)
    env = NationEnvironment(seed=42)
    obs, info = env.reset()
    departments = env.departments
    done = False
    
    print("--- STARTING RETRY LOOP TEST ---", flush=True)
    
    # Phase 2: Debate (just pass)
    print("Step: Skipping Debate...", flush=True)
    paction = ParliamentaryAction(agent_id=departments[0], type="DEBATE", message="")
    obs, _, _, _, _ = env.step(paction)
    
    # Phase 3: Proposals
    print("Step: Submitting Proposals...", flush=True)
    for dept in departments:
        print(f"  Proposing for {dept}...", flush=True)
        paction = ParliamentaryAction(
            agent_id=dept,
            type="PROPOSE_BUDGET",
            department=dept,
            amount=100.0,
            justification="I need money"
        )
        obs, _, _, _, _ = env.step(paction)
        
    print(f"Current Phase: {obs.phase_name}", flush=True)
    
    # Phase 4: Voting (VOTE NO on everything to trigger retry)
    print("\n!!! AGENTS VOTING 'NO' TO TRIGGER RETRY !!!", flush=True)
    max_steps = 100
    steps = 0
    while obs.phase_name == "VOTING" and steps < max_steps:
        steps += 1
        dept = obs.current_agent
        pending = [p for p in obs.proposals if p.status == "pending"]
        
        if not pending:
            print("  No more pending proposals.", flush=True)
            break
        
        # Find a proposal this agent can vote on AND hasn't voted on yet
        target = None
        for p in pending:
            # Must not be the proposer
            is_eligible = (dept != p.agent_id and dept != p.department)
            # Check if dept has already voted on this proposal (p is a ProposalModel)
            has_voted = dept in p.votes
            
            if is_eligible and not has_voted:
                target = p
                break
        
        if target:
            print(f"  Agent {dept} voting NO on {target.department}...", flush=True)
            paction = ParliamentaryAction(
                agent_id=dept,
                type="VOTE",
                proposal_id=target.proposal_id,
                vote="NO"
            )
            obs, reward, done, truncated, info = env.step(paction)
            
            # Check for transition
            if obs.phase_name == "PROPOSAL" and obs.retry_count > 0:
                print(f"\nSUCCESS: Environment looped back to {obs.phase_name} phase!", flush=True)
                print(f"Retry Count: {obs.retry_count}", flush=True)
                print(f"Rejected Departments: {obs.rejected_departments}", flush=True)
                return
        else:
            print(f"  Agent {dept} has no eligible votes left. Sending dummy action...", flush=True)
            # This shouldn't happen if the environment rotation is correct, 
            # but we'll send a NO-OP or similar if needed.
            # Actually, let's just break and see where we are.
            break

    print(f"Failed to trigger retry loop. Final Phase: {obs.phase_name}, Retry Count: {obs.retry_count}", flush=True)

if __name__ == "__main__":
    test_retry_loop()
