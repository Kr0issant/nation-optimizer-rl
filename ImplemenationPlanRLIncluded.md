# 30-Hour Implementation Plan: MARL Nation Simulator

**Constraint:** 3 People, 30 Hours.  
**Core Architecture:** Pure deterministic Python core, wrapped in OpenEnv, driven by a two-phase LLM orchestrator (Debate -> Vote) trained via HuggingFace `trl` (PPO).

---

## Phase 1: The Core Engine (Hours 0-10)
**Owner:** Person 1 (The Math/Physics Engineer)  
**Goal:** Build the `core/` directory. It must run offline with standard Python dictionaries. No LLMs, no OpenEnv yet.

### 1. Data Structures (`core/sectors.json`, `core/events.json`)
* **`sectors.json`:** Define the 6 sectors.
  ```json
  {"Military": {"base_dc": 10, "base_d": 30, "base_ds": 60}}
  ```
* **`events.json`:** Define the modifiers.
  ```json
  {"Pandemic": {"target": "Healthcare", "dc_mult": 2.5, "severity": 4}}
  ```

### 2. Math Modules (`core/revenue.py`, `core/treasury.py`)
* **`revenue.py`:** Write `revenue_factor(alloc, dc, d, ds)`.
  * **Logic:** If `alloc < dc`: return `None` (Fatal). If `alloc < d`: scale 0.5 to 1.0. If `alloc <= ds`: scale 1.0 to 1.8. If `alloc > ds`: `1.8 * exp(-k(alloc - ds))`.
* **`treasury.py`:** Write the `Treasury` class. Track total pool. Add `debit()` and `credit()`.

### 3. Dynamics Modules (`core/productivity.py`, `core/population.py`)
* **`productivity.py`:** Write `update(sector_multipliers)`. 
  * **Formula:** `clip(mean(multipliers) * previous_prod, 0.1, 2.0)`.
* **`population.py`:** Write `update(productivity)`. 
  * **Formula:** `pop += pop * (base_birth_rate * productivity)`. Keep `base_birth_rate` very small (e.g., 0.01).

### 4. The Orchestrator (`core/game.py`)
* Write the `NationGame` class.
* **`step(allocations: dict)`:** The master loop.
  1. Process allocations -> get revenue multipliers.
  2. If any multiplier is `None` (Critical Failure): Trigger curriculum bailout or game over.
  3. Calculate revenues, update Treasury.
  4. Update Productivity and Population.
  5. Calculate step Reward = $\Delta$ GDP Per Capita.
  6. Return `{"treasury": x, "reward": y, "done": z, "info": {...}}`

---

## Phase 2: OpenEnv & Baselines (Hours 5-15)
**Owner:** Person 2 (The Systems Integrator)  
**Goal:** Wrap the core in the OpenEnv API and build dummy agents to prove the math doesn't explode.

### 1. Pydantic Models (`server/models.py`)
* Define `NationState` (Treasury, Pop, Prod, Event List).
* Define `NationAction` (List of 6 floats).

### 2. The OpenEnv Wrapper (`server/environment.py`)
* Write `NationEnvironment(MCPEnvironment)`.
* **CRITICAL - The Softmax Boundary:** Inside `step()`, before calling `game.step()`, catch the LLM's raw output array and normalize it to the treasury:
  ```python
  # Softmax allocation
  exp_a = np.exp(raw_action)
  percentages = exp_a / np.sum(exp_a)
  allocations_dict = {sector: percentages[i] * state.treasury for i, sector in enumerate(sectors)}
  
  # Call the game engine
  self.game.step(allocations_dict)
  ```

### 3. Baseline Agents (`agents/random_agent.py`, `agents/conservative_agent.py`)
* Build a `RandomAgent` that spits out 6 random floats.
* Run `scripts/benchmark_baselines.py`. Let it run for 1000 steps.
* **Validation Check:** Does the Treasury go to infinity? Does float overflow occur? If yes, tell Person 1 to lower the 1.8x max multiplier or the population scalar.

---

## Phase 3: The LLM-MARL Pipeline (Hours 5-20)
**Owner:** Person 3 (The Machine Learning Engineer)  
**Goal:** Build the two-phase LLM system and write the PPO training loop.

### 1. The Orchestrator (`agents/orchestrator.py`)
* Write the function `run_two_phase_turn(state)`.
  * **Phase 1 (Debate):** Loop through the 6 sector prompts. Use `model.generate()` (fast, no gradients). Concatenate outputs into `transcript_string`.
  * **Phase 2 (Vote):** Prompt the 6 models again, appending `transcript_string`. Force them to output JSON: `{"bid": 5.2}`. (These bids are the raw numbers that will hit the Softmax in the env).

### 2. The Training Loop (`scripts/train_ppo.py`)
* Initialize `AutoModelForCausalLMWithValueHead` (Llama-3-8B) and a LoRA config (rank 16).
* Initialize `trl.PPOTrainer`.
* Write the epoch loop:
  1. Call `run_two_phase_turn()` to get the 6 JSON output tensors.
  2. Pass the parsed values to `env.step()`.
  3. Get the scalar reward (GDP change).
  4. Create `reward_tensors = [torch.tensor(reward)] * 6`.
  5. Call `ppo_trainer.step(query_tensors, response_tensors, reward_tensors)`.
  6. Log loss.

---

## Phase 4: Integration, Tuning & Rescue (Hours 20-30)
**Owner:** All Hands  
**Goal:** Wire it all together and train.

### 1. System Merge (Hour 20)
* Connect `train_ppo.py` to `server/environment.py`. Run a 1-epoch test to ensure tensors flow cleanly from the LLM, through the Softmax, into the Game Engine, and back as gradients.

### 2. The Curriculum Bailout (Hours 21-23)
* If the LLM randomly starves a sector on Step 1, the reward will be `-1000` and `done=True`.
* Implement the bailout: For the first 50 epochs, if `alloc < dc`, intercept the `done=True` in `server/environment.py`. Return a penalty of `-100`, but inject emergency cash and let the episode continue.

### 3. Let it Train (Hours 23-30)
* Run `python scripts/train_ppo.py`.
* Monitor the loss. You are looking for the global reward (GDP Per Capita) to slowly trend upward, meaning the 6 personas learned to balance their Softmax bids to stay in the 1.0x - 1.8x profit zones without bankrupting each other.