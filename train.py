import sys
from training.train_grpo import main

if __name__ == "__main__":
    # This ensures that when hf jobs uv run uploads the project,
    # it recognizes 'training' as a package.
    sys.exit(main())
