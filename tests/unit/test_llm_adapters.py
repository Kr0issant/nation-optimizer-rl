from agents.llm import DictatorLLMAdapter, ParliamentaryLLMAdapter, TextGenerationResult
from schemas.actions import ActionType, VoteChoice
from schemas.observations import (
    Observation,
    OwnDepartmentObservation,
    ProposalObservation,
)
from schemas.phases import Phase
from telemetry import EpisodeLogger


class MockTextGenerationClient:
    def __init__(self, completions):
        self.completions = list(completions)
        self.prompts: list[str] = []

    def generate(self, prompt: str):
        self.prompts.append(prompt)
        return self.completions.pop(0)


def test_parliamentary_adapter_parses_budget_action_and_logs_llm_call() -> None:
    logger = EpisodeLogger(episode_id="episode-1")
    client = MockTextGenerationClient(
        [
            TextGenerationResult(
                completion=(
                    '{"type":"PROPOSE_BUDGET","department":"Health",'
                    '"amount":90,"justification":"Maintain clinics."}'
                ),
                prompt_tokens=12,
                completion_tokens=9,
            )
        ]
    )
    observation = _proposal_observation()

    action = ParliamentaryLLMAdapter(
        client,
        logger=logger,
        model="mock-model",
    ).act(observation, {"PROPOSE_BUDGET", "ABSTAIN_FROM_PROPOSAL"}, "health-minister")

    assert action.type is ActionType.PROPOSE_BUDGET
    assert action.department == "Health"
    assert action.amount == 90.0
    event = logger.events[-1]
    assert event.event_type == "llm_call"
    assert event.payload["parse_ok"] is True
    assert event.payload["prompt_tokens"] == 12
    assert event.payload["completion_tokens"] == 9
    assert event.payload["parsed_action"]["type"] == "PROPOSE_BUDGET"
    assert "777" not in client.prompts[0]
    assert "0.42" not in client.prompts[0]
    assert "9999" not in client.prompts[0]


def test_parliamentary_adapter_falls_back_to_allowed_abstain_on_parse_failure() -> None:
    logger = EpisodeLogger(episode_id="episode-1")
    client = MockTextGenerationClient(["I want more money, not JSON."])
    observation = _proposal_observation()

    action = ParliamentaryLLMAdapter(client, logger=logger).act(
        observation,
        {"PROPOSE_BUDGET", "ABSTAIN_FROM_PROPOSAL"},
        "health-minister",
    )

    assert action.type is ActionType.ABSTAIN_FROM_PROPOSAL
    event = logger.events[-1]
    assert event.event_type == "llm_call"
    assert event.payload["parse_ok"] is False
    assert event.payload["completion"] == "I want more money, not JSON."
    assert event.payload["fallback_action"]["type"] == "ABSTAIN_FROM_PROPOSAL"
    assert "parse_error" in event.payload


def test_dictator_adapter_parses_vote_action_and_logs_llm_call() -> None:
    logger = EpisodeLogger(episode_id="episode-1")
    client = MockTextGenerationClient(
        ['{"type":"VOTE","proposal_id":"proposal-1","vote":"YES"}']
    )
    observation = _voting_observation()

    action = DictatorLLMAdapter(client, logger=logger).act(
        observation,
        {"VOTE"},
        "health-minister",
    )

    assert action.type is ActionType.VOTE
    assert action.proposal_id == "proposal-1"
    assert action.vote is VoteChoice.YES
    assert logger.events[-1].payload["parse_ok"] is True


def test_dictator_adapter_shim_returns_one_action_per_agent() -> None:
    client = MockTextGenerationClient(
        [
            '{"type":"DEBATE","message":"Prioritize health resilience."}',
            '{"type":"DEBATE","message":"Protect food supply."}',
        ]
    )
    adapter = DictatorLLMAdapter(client)
    observations = {
        "health-minister": _debate_observation("Health"),
        "agriculture-minister": _debate_observation("Agriculture"),
    }

    actions = adapter.act_for_agents(
        observations,
        {
            "health-minister": {"DEBATE"},
            "agriculture-minister": {"DEBATE"},
        },
    )

    assert set(actions) == {"health-minister", "agriculture-minister"}
    assert actions["health-minister"].message == "Prioritize health resilience."
    assert actions["agriculture-minister"].message == "Protect food supply."
    assert len(client.prompts) == 2


def test_dictator_adapter_falls_back_to_abstain_vote_on_parse_failure() -> None:
    logger = EpisodeLogger(episode_id="episode-1")
    client = MockTextGenerationClient(["not-json"])

    action = DictatorLLMAdapter(client, logger=logger).act(
        _voting_observation(),
        {"VOTE"},
        "health-minister",
    )

    assert action.type is ActionType.VOTE
    assert action.vote is VoteChoice.ABSTAIN
    assert logger.events[-1].payload["parse_ok"] is False
    assert logger.events[-1].payload["fallback_action"]["vote"] == "ABSTAIN"


def _proposal_observation() -> Observation:
    return Observation(
        round=2,
        phase=Phase.PROPOSAL,
        treasury=500.0,
        own_department=OwnDepartmentObservation(
            name="Health",
            allocated_budget=777.0,
            consumption=111.0,
            surplus=22.0,
            efficiency_rating=0.42,
        ),
        event_ledger=(
            {
                "name": "Virus Outbreak",
                "severity": 3,
                "narrative": "Hospitals are under pressure.",
                "cost": 9999,
            },
        ),
    )


def _voting_observation() -> Observation:
    return Observation(
        round=2,
        phase=Phase.VOTING,
        treasury=500.0,
        own_department=OwnDepartmentObservation(name="Health"),
        proposals=(
            ProposalObservation(
                proposal_id="proposal-1",
                department="Agriculture",
                amount=70.0,
            ),
        ),
    )


def _debate_observation(department: str) -> Observation:
    return Observation(
        round=2,
        phase=Phase.DEBATE,
        treasury=500.0,
        own_department=OwnDepartmentObservation(name=department),
    )
