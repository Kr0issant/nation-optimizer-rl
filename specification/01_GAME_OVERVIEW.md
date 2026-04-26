# Game Overview

## Concept

The RL Parliament Environment is a centralized planning simulation with parliamentary narrative where an LLM learns resource allocation through structured reasoning.

- Agents are **ministers** with distinct departmental portfolios (Health, Defense, Education, Infrastructure, etc.)
- Each round, ministers propose budget allocations, debate, and vote on spending bills
- The parliament operates under a **no-debt, no-corruption** principle: collective reward is shared, not individual
- Success is measured by **prosperity** (GDP per capita growth) sustained over time
- Failure occurs when the treasury reaches zero (bankruptcy)

## Inspiration

The environment draws ideological inspiration from Marxist doctrine.

- Core principle: **"From each according to his ability, to each according to his need"**
  - Ministers with productive departments contribute more to the common treasury
  - Ministers facing critical needs (war, famine, epidemic) receive priority allocation
- The system enforces **collective reward**: no individual minister optimizes alone, all succeed or fail together
- Stochastic events (war, breakthrough, famine) create dynamic pressure that demands cooperative, not competitive, behavior

## Goals

The environment exists to:

- **Train long-horizon planning** through structured reasoning (parliamentary debate + voting)
- **Explore sequential voting dynamics** where budget proposals pass through multiple stages of debate and approval
- **Model hidden-information scenarios** where event costs are known only to the environment, forcing agents to reason under uncertainty
- **Benchmark structured reasoning** against direct planning (parliamentary vs. dictator baseline)
- **Generate interpretable episodes** where agent reasoning and parliamentary deliberation are observable
- **Time scale**: Each round represents 3 months (quarterly budgeting). A full episode spans 12.5 years (50 quarters)
- **Piecewise revenue model**: The profit zone (Demand to Surplus) rewards moderate over-investment; agents must balance staying above Demand (for revenue factor > 1.0) against avoiding Wastage (beyond which revenue factor falls below 1.0)

## Target Audience

This specification targets:

- **Hackathon participants** building on Meta's OpenEnv framework with Hugging Face LLM inference
- **LLM reasoning and planning researchers** interested in interpretable resource allocation under partial information
- **LLM reasoning researchers** exploring how language models navigate sequential negotiation and collective utility

## Non-Goals

This system is NOT:

- A competitive zero-sum game where agents fight over scarce resources
- A single-agent optimization problem with one dominant strategy
- A mechanism for training adversarial or deceptive agent behaviors
- A realistic political simulation with inter-ministry private communication
- A tool for exploring agent self-interest or profit-maximization
- A simulation with private sector or market competition

## Core Mechanics Summary

The environment operates as follows:

- **Variable agent count**: Parliaments contain 4, 6, 8, or any even number of ministers (configurable per episode)
- **Central treasury**: All revenue pools here; baseline tax income plus productivity bonuses from prior rounds
- **Sequential proposals**: Each minister proposes a budget allocation for their department
- **Collective voting**: All ministers vote on each proposal; abstention is allowed but must be explicit
- **Stochastic events**: Hidden-impact events (war, famine, breakthrough, virus) alter treasury and departmental priorities
- **Treasury-level surplus**: Unspent budget returns to the central treasury, incentivizing efficient allocation across all departments
- **Collective reward**: All agents receive the same prosperity-based reward at each step; no individual bonuses

## Environment Architecture

The system comprises:

- **RL Environment** (Meta OpenEnv compatible): Encodes game state, action space, observation space
- **LLM Agents** (Hugging Face inference): Each agent receives prompts describing their role, the current state, and available actions
- **Event Engine**: Generates stochastic events with hidden cost impact
- **Treasury Controller**: Manages revenue collection, allocation execution, surplus tracking
- **Voting Arbiter**: Validates proposals, conducts voting rounds, resolves ties
- **Prosperity Calculator**: Computes reward signal (GDP per capita) at each step

## Reward Model

- Reward is **global and collective**: every agent receives identical reward at every step
- Reward = prosperity (GDP per capita) minus penalties for over/under-allocation
- No agent may claim individual credit; the parliament succeeds or fails together
- Bankruptcy (treasury reaches zero) triggers episode termination with zero reward for all subsequent steps

## Key Constraints

- **No debt**: Treasury cannot go negative; any allocation causing negative treasury is rejected
- **No private communication**: All debate and proposals are public to all ministers
- **No mid-episode agent replacement**: Minister roster stays fixed throughout an episode
- **No borrowing**: Inter-department credit transfer is not permitted