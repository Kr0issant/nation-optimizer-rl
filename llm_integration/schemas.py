"""
Pydantic schemas for LLM structured output parsing.
These match the environment's internal Action types but are optimized for LLM generation.
"""

from typing import Literal, Union
from pydantic import BaseModel, Field

class LLMDebateAction(BaseModel):
    """Schema for a debate message."""
    type: Literal["DEBATE"] = Field(description="The action type. Must be 'DEBATE'.")
    message: str = Field(description="The public message to broadcast to the parliament.")

class LLMProposeBudgetAction(BaseModel):
    """Schema for proposing a budget."""
    type: Literal["PROPOSE_BUDGET"] = Field(description="The action type. Must be 'PROPOSE_BUDGET'.")
    department: str = Field(description="Your department name.")
    amount: float = Field(description="The amount of funds requested from the treasury.")
    justification: str = Field(description="A public justification for the requested amount.")

class LLMVoteAction(BaseModel):
    """Schema for casting a vote on a budget proposal."""
    type: Literal["VOTE"] = Field(description="The action type. Must be 'VOTE'.")
    proposal_id: str = Field(description="The ID of the proposal you are voting on.")
    vote: Literal["YES", "NO", "ABSTAIN"] = Field(description="Your vote choice.")

class LLMAbstainAction(BaseModel):
    """Schema for abstaining from proposing a budget."""
    type: Literal["ABSTAIN_FROM_PROPOSAL"] = Field(description="The action type. Must be 'ABSTAIN_FROM_PROPOSAL'.")

class LLMFinishDebateAction(BaseModel):
    """Schema for ending the debate phase early."""
    type: Literal["FINISH_DEBATE"] = Field(description="The action type. Must be 'FINISH_DEBATE'.")
    reason: str = Field(description="Brief reason for ending the debate (e.g., 'Consensus reached').")

# Union type for parsing
LLMAction = Union[
    LLMDebateAction, 
    LLMProposeBudgetAction, 
    LLMVoteAction, 
    LLMAbstainAction,
    LLMFinishDebateAction
]
