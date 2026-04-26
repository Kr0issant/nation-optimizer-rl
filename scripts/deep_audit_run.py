"""High-fidelity trial run with final state reporting on failure."""

from server.environment import NationEnvironment
from server.models import ParliamentaryAction
from agents.rule_based.conservative import ConservativeAdapter
from schemas.actions import VoteChoice, ActionType
from schemas.phases import Phase
import sys

def run_labeled_trial(rounds=10):
    env = NationEnvironment(seed=1337)
    obs, _ = env.reset()
    adapter = ConservativeAdapter()
    departments = list(env.departments)
    
    step_count = 0
    print(f"=== STARTING {rounds}-ROUND TRIAL RUN (RETRY LABELED) ===", flush=True)

    prev_obs = None
    while obs.round <= rounds:
        current_round_num = obs.round
        
        # 0. Log new events from the ledger
        prev_ledger_len = len(prev_obs.event_ledger) if prev_obs else 0
        if len(obs.event_ledger) > prev_ledger_len:
            print(f"\n--- EVENTS REVEALED FOR ROUND {obs.round} ---")
            for i in range(prev_ledger_len, len(obs.event_ledger)):
                event = obs.event_ledger[i]
                print(f"  [!] {event.get('name')}: {event.get('narrative')} (Severity: {event.get('severity')})")
            print("------------------------------------------")

        prev_obs = obs
        # 1. Determine Action
        agent_id = obs.current_agent or "System"
        action = adapter.act(obs, obs.valid_actions, agent_id)
        
        # --- Chaos Mode: Force NO votes in Round 1, Retry 0 ---
        if obs.round == 1 and obs.retry_count == 0 and action.type == ActionType.VOTE:
            from schemas.actions import VoteAction
            action = VoteAction(type=ActionType.VOTE, proposal_id=action.proposal_id, vote=VoteChoice.NO)

        # 2. Log Step with Retry Label
        phase_label = f"{obs.phase_name} (Retry {obs.retry_count})" if obs.retry_count > 0 else obs.phase_name
        print(f"  [Step {step_count}] Round {obs.round} Phase {phase_label} Agent {agent_id}", flush=True)
        
        # 3. Execute Step
        action_dict = action.to_dict()
        paction = ParliamentaryAction(agent_id=agent_id, **action_dict)
        obs, reward, done, _, info = env.step(paction)
        step_count += 1

        # 4. Handle Debate Advance
        if not done and obs.phase_name == "DEBATE" and step_count % len(departments) == 0:
            phase_label = f"DEBATE (Retry {obs.retry_count})" if obs.retry_count > 0 else "DEBATE"
            print(f"  [Step {step_count}] Round {obs.round} Phase {phase_label} -> ADVANCE", flush=True)
            paction = ParliamentaryAction(agent_id=agent_id, type="DEBATE", message="")
            obs, reward, done, _, info = env.step(paction)
            step_count += 1

        # 5. Round Summary (Trigger on round increment OR on simulation end)
        if obs.round > current_round_num or done:
            print(f"\n--- ROUND {current_round_num} SUMMARY ---")
            print(f"  Final Treasury: {obs.treasury:.2f} | Population: {obs.population}")
            print(f"  Requests from Round {current_round_num}:")
            # Pull from previous proposals if they were just cleared by a round increment
            source_proposals = prev_obs.proposals if obs.round > current_round_num else obs.proposals
            for p in source_proposals:
                status_str = f" [{p.status.upper()}]" if hasattr(p, 'status') else ""
                print(f"    - {p.department}: ${p.amount:.2f}{status_str}")
            print(f"  Round Reward: {reward:.4f}")
            print("---------------------------\n", flush=True)

        if done:
            if info.get("termination_reason") == "BANKRUPTCY":
                print("ROOT CAUSE ANALYSIS (treasury could not cover mandatory spend):")
                for name, sector in env.game.sectors.items():
                    crit_val = sector.critical(obs.population)
                    demand_val = float(sector.demand)
                    if sector.allocation < crit_val:
                        print(
                            f"  [!] Sector '{name}' below critical: "
                            f"Allocation ${sector.allocation:.2f} < Critical ${crit_val:.2f}"
                        )
                    elif sector.allocation < demand_val:
                        print(
                            f"  [-] Sector '{name}' under-funded: "
                            f"Allocation ${sector.allocation:.2f} < Demand ${demand_val:.2f}"
                        )
            print(f"\nSIMULATION ENDED. Reason: {info.get('termination_reason')}")
            break

    print(f"\n=== TRIAL COMPLETE ===")

if __name__ == "__main__":
    run_labeled_trial(rounds=10)
