#!/usr/bin/env python
"""Standalone DQN training script for Maze Explorer.

Usage:
    python train_dqn.py                          # train with defaults
    python train_dqn.py --episodes 10000 --rows 21 --cols 21
    python train_dqn.py --resume models/dqn_maze.pth

Requirements:
    pip install torch numpy
"""

from __future__ import annotations

import argparse
import sys
import os

ROOT = os.path.dirname(__file__)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from game.ai.dqn import train_dqn


def parse_args():
    p = argparse.ArgumentParser(description="Train DQN agent for maze exploration")
    p.add_argument("--rows", type=int, default=15, help="Maze rows (default: 15)")
    p.add_argument("--cols", type=int, default=15, help="Maze cols (default: 15)")
    p.add_argument("--episodes", type=int, default=5000, help="Training episodes (default: 5000)")
    p.add_argument("--batch-size", type=int, default=64, help="Batch size (default: 64)")
    p.add_argument("--gamma", type=float, default=0.95, help="Discount factor (default: 0.95)")
    p.add_argument("--lr", type=float, default=1e-3, help="Learning rate (default: 1e-3)")
    p.add_argument("--epsilon-decay", type=float, default=0.997, help="Epsilon decay per episode")
    p.add_argument("--hidden-dim", type=int, default=128, help="Hidden layer size")
    p.add_argument("--buffer-capacity", type=int, default=50000, help="Replay buffer size")
    p.add_argument("--target-update", type=int, default=100, help="Target net update frequency")
    p.add_argument("--save-path", type=str, default="models/dqn_maze.pth", help="Model save path")
    p.add_argument("--seed", type=int, default=42, help="Random seed")
    p.add_argument("--quiet", action="store_true", help="Suppress per-episode logging")
    return p.parse_args()


def main():
    args = parse_args()
    print(f"Training DQN: {args.rows}×{args.cols} maze, {args.episodes} episodes")
    print(f"  γ={args.gamma}  lr={args.lr}  ε_decay={args.epsilon_decay}")
    print(f"  hidden={args.hidden_dim}  batch={args.batch_size}  buffer={args.buffer_capacity}")
    print(f"  save → {args.save_path}")
    print("-" * 60)

    stats = train_dqn(
        maze_rows=args.rows,
        maze_cols=args.cols,
        num_episodes=args.episodes,
        batch_size=args.batch_size,
        gamma=args.gamma,
        lr=args.lr,
        epsilon_decay=args.epsilon_decay,
        target_update_freq=args.target_update,
        buffer_capacity=args.buffer_capacity,
        hidden_dim=args.hidden_dim,
        save_path=args.save_path,
        seed=args.seed,
        verbose=not args.quiet,
    )

    print("-" * 60)
    print(f"Done.  final_avg_reward(100ep)={stats['final_avg_reward_100']:.1f}")
    print(f"  final_avg_steps(100ep)={stats['final_avg_steps_100']:.1f}")
    print(f"  best_avg_reward={stats['best_avg_reward']:.1f}")
    print(f"  model → {stats['model_path']}")


if __name__ == "__main__":
    main()
