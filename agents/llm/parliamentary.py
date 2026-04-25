"""Parliamentary LLM adapter with strict parsing and rollout telemetry."""

from __future__ import annotations

from collections.abc import Iterable

from agents.base import PolicyAdapter
from agents.llm.common import (
    LLMActionError,
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


class ParliamentaryLLMAdapter(PolicyAdapter):
    """One LLM-backed minister that suggests exactly one structured action.

    The prompt contains public observation fields plus the acting department
    name, but not private departmental metrics or unresolved event costs. If
    strict structural parsing fails, the adapter emits a documented safe
    fallback only when that fallback action type is present in ``valid_actions``.
    """

    def __init__(
        self,
        client: TextGenerationClient,
        *,
        logger: EpisodeLogger | None = None,
        model: str | None = None,
    ) -> None:
        self.client = client
        self.logger = logger
        self.model = model

    def act(
        self,
        observation: Observation,
        valid_actions: Iterable[str],
        agent_id: str,
    ) -> Action:
        if not agent_id.strip():
            raise ValueError("agent_id must be non-empty.")
        valid_action_set = set(valid_actions)
        prompt = render_action_prompt(
            observation,
            agent_id,
            valid_action_set,
            role="parliamentary minister",
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


__all__ = ["LLMActionError", "ParliamentaryLLMAdapter"]
