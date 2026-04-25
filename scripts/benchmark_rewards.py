import matplotlib.pyplot as plt
import numpy as np
from core.revenue import revenue_factor
from training.reward_fn import (
    PROPOSE_BASE_REWARD,
    PROPOSE_FACTOR_WEIGHT,
    ILLEGAL_ACTION_REWARD,
)

def simulate_rewards():
    # Setup standard sector thresholds
    demand = 100.0
    critical = 40.0
    surplus = 150.0
    wastage = 250.0 # Engine uses demand * 2.5
    
    allocations = np.linspace(0, 300, 500)
    rewards = []
    revenue_factors = []

    for x in allocations:
        rf = revenue_factor(x, critical, demand, surplus, wastage)
        
        if rf is None:
            # Critical failure
            reward = ILLEGAL_ACTION_REWARD
            rf_val = 0.0
        else:
            # Match training/reward_fn.py logic
            reward = PROPOSE_BASE_REWARD + PROPOSE_FACTOR_WEIGHT * (rf - 1.0)
            rf_val = rf
            
        rewards.append(reward)
        revenue_factors.append(rf_val)

    # Plotting
    fig, ax1 = plt.subplots(figsize=(12, 7))

    color = 'tab:blue'
    ax1.set_xlabel('Allocation Amount (Demand = 100)')
    ax1.set_ylabel('Revenue Factor (Efficiency)', color=color)
    ax1.plot(allocations, revenue_factors, color=color, linewidth=2, label='Revenue Factor')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('GRPO Reward (Training Signal)', color=color)
    ax2.plot(allocations, rewards, color=color, linewidth=3, linestyle='--', label='RL Reward')
    ax2.tick_params(axis='y', labelcolor=color)

    # Annotate key points
    ax1.axvline(x=critical, color='black', linestyle=':', label='Critical Threshold')
    ax1.axvline(x=demand, color='green', linestyle=':', label='Demand')
    ax1.axvline(x=surplus, color='purple', linestyle=':', label='Surplus (Peak)')

    plt.title('Reward Landscape: How the RL Agent sees the Economy')
    fig.tight_layout()
    
    output_path = "assets/results/reward_landscape.png"
    plt.savefig(output_path)
    print(f"Graph saved to {output_path}")

    # Benchmark Summary
    print("\n=== REWARD BENCHMARK SUMMARY ===")
    print(f"{'Approach':<20} | {'Average Reward':<15}")
    print("-" * 40)
    
    # 1. Random Approach (0 to 250)
    random_rewards = [r for r in rewards if r > ILLEGAL_ACTION_REWARD]
    print(f"{'Random Agent':<20} | {np.mean(random_rewards):.4f}")
    
    # 2. Under-allocator (fails critical)
    print(f"{'Panic Under-alloc':<20} | {ILLEGAL_ACTION_REWARD:.4f}")
    
    # 3. Demand-Only Agent
    rf_demand = revenue_factor(100, critical, demand, surplus, wastage)
    reward_demand = PROPOSE_BASE_REWARD + PROPOSE_FACTOR_WEIGHT * (rf_demand - 1.0)
    print(f"{'Safe Agent (Demand)':<20} | {reward_demand:.4f}")
    
    # 4. Optimal Agent (Surplus)
    rf_surplus = revenue_factor(150, critical, demand, surplus, wastage)
    reward_surplus = PROPOSE_BASE_REWARD + PROPOSE_FACTOR_WEIGHT * (rf_surplus - 1.0)
    print(f"{'Optimal Agent':<20} | {reward_surplus:.4f}")

if __name__ == "__main__":
    simulate_rewards()
