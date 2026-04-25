import argparse
from agents.random_agent import RandomAgent
from server.environment import NationEnvironment

def run_episode(seed: int) -> dict:
    env = NationEnvironment(seed=seed)
    agent = RandomAgent(seed=seed)
    
    state, info = env.reset()
    done = False
    step_count = 0
    total_reward = 0.0
    
    while not done:
        action = agent.act(state)
        state, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        total_reward += reward
        step_count += 1
        
    return {
        "seed": seed,
        "steps": step_count,
        "final_treasury": state.treasury,
        "final_population": state.population,
        "final_productivity": state.productivity,
        "termination_reason": info["termination_reason"],
        "total_reward": total_reward
    }

def main():
    parser = argparse.ArgumentParser(description="Benchmark Baseline Agents")
    parser.add_argument("--episodes", type=int, default=5, help="Number of episodes to run")
    args = parser.parse_args()
    
    print(f"Running {args.episodes} random agent episodes...")
    for i in range(args.episodes):
        result = run_episode(seed=42 + i)
        print(f"Episode {i+1}: Survived {result['steps']} steps | "
              f"Treasury: {result['final_treasury']:.2f} | "
              f"Pop: {result['final_population']} | "
              f"Reward: {result['total_reward']:.2f} | "
              f"Reason: {result['termination_reason']}")

if __name__ == "__main__":
    main()
