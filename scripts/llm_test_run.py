"""
Test script to run the NationEnvironment with the Parliamentary LLM Adapter.
Make sure to fill in your .env file with HF_TOKEN and HF_MODEL_ID.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from server.environment import NationEnvironment
from llm_integration.hf_client import HuggingFaceTextGenerationClient
from llm_integration.adapters.parliamentary import ParliamentaryLLMAdapter
from schemas.phases import valid_action_types_for_phase

def run_llm_test():
    print("=== STARTING LLM PARLIAMENTARY TEST ===")
    
    token = os.environ.get("HF_TOKEN")
    model_id = os.environ.get("HF_MODEL_ID")
    
    if not token or not model_id:
        print("ERROR: HF_TOKEN or HF_MODEL_ID not found in environment.")
        print("Please copy .env.example to .env and fill in your credentials.")
        return
        
    print(f"Connecting to HuggingFace using model: {model_id}")
    
    try:
        # Initialize client and environment
        client = HuggingFaceTextGenerationClient(model=model_id, token=token)
        adapter = ParliamentaryLLMAdapter(client=client, model=model_id)
        
        env = NationEnvironment(seed=42)
        obs, info = env.reset()
        
        print(f"\n[Round {obs.round} Started]")
        print("-" * 40)
        
        # We will just run for a few steps to see if the LLM can generate valid actions
        # Increase steps to see more agents participate
        max_steps = 20
        step_count = 0
        
        while not env.game.done and step_count < max_steps:
            current_agent = obs.current_agent
            current_phase = obs.phase_name
            
            print(f"Step {step_count + 1}: Agent '{current_agent}' acting in Phase '{current_phase}'")
            
            # Use the adapter to get an action from the LLM
            valid_actions = valid_action_types_for_phase(obs.phase)
            
            print(f"  Valid Actions: {list(valid_actions)}")
            print("  Waiting for LLM response...")
            
            try:
                action = adapter.act(
                    observation=obs,
                    valid_actions=valid_actions,
                    agent_id=current_agent
                )
                print(f"  LLM Action Generated: {action}")
            except Exception as e:
                import traceback
                print(f"  [ERROR] LLM failed to generate valid action:")
                traceback.print_exc()
                break
                
            from server.models import ParliamentaryAction
            
            # Convert internal Action to ParliamentaryAction
            action_dict = action.to_dict()
            action_dict["agent_id"] = current_agent
            p_action = ParliamentaryAction(**action_dict)
                
            # Step the environment
            obs, reward, terminated, truncated, info = env.step(p_action)
            step_count += 1
            print("-" * 40)
            
    except Exception as e:
        print(f"Initialization Error: {e}")
        
    print("\n=== TEST RUN COMPLETE ===")

if __name__ == "__main__":
    run_llm_test()
