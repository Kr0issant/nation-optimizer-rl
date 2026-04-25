"""Central-planner LLM adapter using the same structured action boundary."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from agents.base import PolicyAdapter
from agents.llm.common import (
    log_llm_call,
    parse_allowed_action,
    parse_generation_result,
    safe_fallback_action,
)
from agents.llm.hf_client import TextGenerationClient
from agents.prompts import render_action_prompt
from schemas.actions import Action
from schemas.observations import Observation
from telemetry import EpisodeLogger


class DictatorLLMAdapter(PolicyAdapter):
    """Single-model central planner that suggests environment actions.

    The current adapter API returns one ``Action`` per ``agent_id`` rather than
    an all-minister allocation vector. ``act_for_agents`` is the smallest shim:
    it calls the same model once per acting minister and returns per-agent
    structured actions without changing collective rewards or core validation.

    ``oracle=False`` is the deployable default and uses only legal observation
    fields. ``oracle=True`` is reserved for research upper-bound experiments and
    should be gated in tests or benchmarks that explicitly opt in.
    """

    def __init__(
        self,
        client: TextGenerationClient,
        *,
        logger: EpisodeLogger | None = None,
        model: str | None = None,
        oracle: bool = False,
    ) -> None:
        self.client = client
        self.logger = logger
        self.model = model
        self.oracle = oracle

    def act(
        self,
        observation: Observation,
        valid_actions: Iterable[str],
        agent_id: str,
    ) -> Action:
        valid_action_set = set(valid_actions)
        prompt = render_action_prompt(
            observation,
            agent_id,
            valid_action_set,
            role="central planning dictator",
            oracle=self.oracle,
        )
        generation = parse_generation_result(self.client.generate(prompt))

        try:
            action = parse_allowed_action(
                generation.completion,
                observation=observation,
                valid_actions=valid_action_set,
                agent_id=agent_id,
            )
        except Exception as exc:
            fallback = safe_fallback_action(observation, valid_action_set)
            log_llm_call(
                self.logger,
                observation=observation,
                agent_id=agent_id,
                prompt=prompt,
                generation=generation,
                parse_ok=False,
                parse_error=str(exc),
                fallback_action=fallback,
                model=self.model,
            )
            return fallback

        log_llm_call(
            self.logger,
            observation=observation,
            agent_id=agent_id,
            prompt=prompt,
            generation=generation,
            parse_ok=True,
            parsed_action=action,
            model=self.model,
        )
        return action

    def act_for_agents(
        self,
        observations: Mapping[str, Observation],
        valid_actions_by_agent: Mapping[str, Iterable[str]],
    ) -> dict[str, Action]:
        """Return one structured action per agent without bypassing validation."""
        return {
            agent_id: self.act(
                observation=observation,
                valid_actions=valid_actions_by_agent.get(agent_id, ()),
                agent_id=agent_id,
            )
            for agent_id, observation in observations.items()
        }


__all__ = ["DictatorLLMAdapter"]
