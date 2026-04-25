"""Demo script: run parliamentary episodes with rule-based adapters."""

import argparse
from collections.abc import Iterable

from agents.rule_based import (
    GreedyAdapter,
    EqualSplitAdapter,
    ConservativeAdapter,
    OptimalZoneAdapter,
)
from agents.base import PolicyAdapter
from schemas.actions import ActionType
from schemas.observations import Observation as SpecObservation, OwnDepartmentObservation, ProposalObservation
from schemas.phases import Phase
from server.environment import NationEnvironment
from server.models import ParliamentaryAction, ParliamentaryObservation


def obs_to_spec(obs: ParliamentaryObservation, agent_id: str) -> SpecObservation:
    """Convert ParliamentaryObservation to the schemas.observations.Observation
    format that rule-based adapters expect."""
    own_dept = OwnDepartmentObservation(
        name=agent_id,
        allocated_budget=obs.own_department.allocated_budget if obs.own_department else None,
        consumption=obs.own_department.consumption if obs.own_department else None,
        surplus=obs.own_department.surplus if obs.own_department else None,
        efficiency_rating=obs.own_department.efficiency_rating if obs.own_department else None,
    )

    proposals = tuple(
        ProposalObservation(
            proposal_id=p.proposal_id,
            department=p.department,
            amount=p.amount,
            status=p.status,
        )
        for p in obs.proposals
    )

    return SpecObservation(
        round=obs.round,
        phase=Phase(obs.phase),
        treasury=obs.treasury,
        own_department=own_dept,
        event_ledger=tuple(obs.event_ledger),
        proposals=proposals,
        votes=tuple(),
        debate_messages=tuple(obs.debate_messages),
        termination=obs.termination,
    )


def wrap_action(action, agent_id: str) -> ParliamentaryAction:
    """Convert a schemas.actions.Action to a ParliamentaryAction."""
    d = action.to_dict()
    return ParliamentaryAction(
        agent_id=agent_id,
        type=d["type"],
        message=d.get("message"),
        department=d.get("department"),
        amount=d.get("amount"),
        justification=d.get("justification"),
        proposal_id=d.get("proposal_id"),
        vote=d.get("vote"),
    )


def end_debate_action(agent_id: str) -> ParliamentaryAction:
    """Create a no-op action to signal end of debate for this agent."""
    return ParliamentaryAction(
        agent_id=agent_id,
        type="DEBATE",
        message=f"{agent_id} has nothing further to add.",
    )


def run_episode(
    adapter_class: type[PolicyAdapter],
    seed: int,
    max_steps: int = 500,
) -> dict:
    """Run one full parliamentary episode."""
    env = NationEnvironment(seed=seed)
    departments = list(env.departments)

    # Create one adapter per department
    adapters = {dept: adapter_class() for dept in departments}

    obs, info = env.reset(seed=seed)
    done = False
    total_reward = 0.0
    step_count = 0
    round_num = 1

    while not done and step_count < max_steps:
        phase = obs.phase
        valid_actions = obs.valid_actions

        if Phase(phase) == Phase.DEBATE:
            # Each agent sends one debate message, then we pass
            for dept in departments:
                print(f"  [Step {step_count}] Round {obs.round} Phase DEBATE Agent {dept}", flush=True)
                spec_obs = obs_to_spec(obs, dept)
                action = adapters[dept].act(spec_obs, valid_actions, dept)
                paction = wrap_action(action, dept)
                obs, reward, done, truncated, info = env.step(paction)
                total_reward += reward
                step_count += 1
                if done: break
            
            if not done and obs.phase == Phase.DEBATE:
                print(f"  [Step {step_count}] Round {obs.round} Phase DEBATE -> ADVANCE", flush=True)
                paction = ParliamentaryAction(agent_id=departments[0], type="DEBATE", message="")
                obs, reward, done, truncated, info = env.step(paction)
                total_reward += reward
                step_count += 1

        elif Phase(phase) == Phase.PROPOSAL:
            while not done and obs.phase == Phase.PROPOSAL:
                dept = obs.current_agent or departments[0]
                print(f"  [Step {step_count}] Round {obs.round} Phase PROPOSAL Agent {dept}", flush=True)
                spec_obs = obs_to_spec(obs, dept)
                action = adapters[dept].act(spec_obs, valid_actions, dept)
                paction = wrap_action(action, dept)
                obs, reward, done, truncated, info = env.step(paction)
                total_reward += reward
                step_count += 1

        elif Phase(phase) == Phase.VOTING:
            while not done and obs.phase == Phase.VOTING:
                dept = obs.current_agent or departments[0]
                pending = [p for p in obs.proposals if p.status == "pending"]
                if not pending: break
                
                target = None
                for p in pending:
                    # Must be eligible (not proposer) AND not already voted
                    is_eligible = (dept != p.agent_id and dept != p.department)
                    # Check if dept has already voted on this proposal
                    # ProposalObservation in spec doesn't have votes, but our ParliamentaryObservation does.
                    # Wait, our obs.proposals are ProposalModel which HAS votes.
                    has_voted = dept in getattr(p, 'votes', {})
                    
                    if is_eligible and not has_voted:
                        target = p
                        break
                
                if target:
                    print(f"  [Step {step_count}] Round {obs.round} Phase VOTING Agent {dept} on {target.department} ({target.proposal_id})", flush=True)
                    from schemas.actions import VoteAction, VoteChoice
                    vote_act = VoteAction(type=ActionType.VOTE, proposal_id=target.proposal_id, vote=VoteChoice.YES)
                    paction = wrap_action(vote_act, dept)
                else:
                    print(f"  [Step {step_count}] Round {obs.round} Phase VOTING Agent {dept} -> NO ELIGIBLE/PENDING VOTES", flush=True)
                    break

                obs, reward, done, truncated, info = env.step(paction)
                total_reward += reward
                step_count += 1

        else:
            # System phase or unknown — just step with no action if needed
            # (Though env.step handles system phases automatically)
            break

        if not done:
            round_num = obs.round

        else:
            # System phase or unexpected state — try to advance
            obs, reward, done, truncated, info = env._run_system_phases(departments[0])
            total_reward += reward
            step_count += 1

    return {
        "seed": seed,
        "steps": step_count,
        "rounds": round_num,
        "final_treasury": obs.treasury,
        "final_population": obs.population,
        "total_reward": total_reward,
        "termination_reason": info.get("termination_reason"),
        "done": done,
    }


def main():
    parser = argparse.ArgumentParser(description="Parliamentary Benchmark")
    parser.add_argument("--episodes", type=int, default=3)
    parser.add_argument("--adapter", type=str, default="conservative",
                        choices=["greedy", "equal_split", "conservative", "optimal_zone"])
    args = parser.parse_args()

    adapter_map = {
        "greedy": GreedyAdapter,
        "equal_split": EqualSplitAdapter,
        "conservative": ConservativeAdapter,
        "optimal_zone": OptimalZoneAdapter,
    }

    adapter_cls = adapter_map[args.adapter]
    print(f"Running {args.episodes} parliamentary episodes with {args.adapter} adapter...")

    for i in range(args.episodes):
        result = run_episode(adapter_cls, seed=42 + i)
        print(
            f"Episode {i+1}: "
            f"Rounds={result['rounds']} | "
            f"Steps={result['steps']} | "
            f"Treasury={result['final_treasury']:.2f} | "
            f"Pop={result['final_population']} | "
            f"Reward={result['total_reward']:.2f} | "
            f"Reason={result['termination_reason']}"
        )


if __name__ == "__main__":
    main()
