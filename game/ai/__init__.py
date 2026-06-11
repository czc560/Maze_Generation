"""AI players for maze navigation."""
from game.ai.greedy import SimpleGreedy, MemoryGreedy, GreedyAI, ProbeAI, ProbeState

try:
    from game.ai.dqn import DQNAI, train_dqn
except (ImportError, AttributeError):
    DQNAI = None      # type: ignore[assignment]
    train_dqn = None   # type: ignore[assignment]
