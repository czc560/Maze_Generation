"""DQNAI — Deep Q-Network maze agent + training utilities."""

from __future__ import annotations

import os
import random
from collections import deque
from dataclasses import dataclass
from typing import Any, Optional

from game.maze.symbols import SYMBOLS, COIN_VALUE, TRAP_VALUE

try:
    import numpy as np
    import torch
    import torch.nn as nn
    import torch.optim as optim
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    np: Any = None  # type: ignore[no-redef]
    torch: Any = None  # type: ignore[no-redef]
    nn: Any = None  # type: ignore[no-redef]
    optim: Any = None  # type: ignore[no-redef]

_NNModuleBase = nn.Module if HAS_TORCH else object

_DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
_CELL_ENCODING = {"#": 0, ".": 1, "S": 2, "E": 3, "B": 4, "C": 5, "T": 6}


def _valid_moves(maze, pos):
    moves = []
    for i, (dr, dc) in enumerate(_DIRECTIONS):
        nr, nc = pos[0] + dr, pos[1] + dc
        if 0 <= nr < maze.rows and 0 <= nc < maze.cols and maze.grid[nr][nc].walkable:
            moves.append(i)
    return moves


def _step_position(pos, action):
    dr, dc = _DIRECTIONS[action]
    return (pos[0] + dr, pos[1] + dc)


# ============================================================================
#  Q-Network
# ============================================================================

class _QNetwork(_NNModuleBase):
    def __init__(self, input_dim=31, hidden_dim=128, num_actions=4):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim // 2), nn.ReLU(),
            nn.Linear(hidden_dim // 2, num_actions),
        )

    def forward(self, x):
        return self.net(x)


# ============================================================================
#  Replay Buffer
# ============================================================================

class ReplayBuffer:
    def __init__(self, capacity=50000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        batch = random.sample(self.buffer, min(batch_size, len(self.buffer)))
        states, actions, rewards, next_states, dones = zip(*batch)
        return (torch.FloatTensor(np.array(states)),
                torch.LongTensor(actions),
                torch.FloatTensor(rewards),
                torch.FloatTensor(np.array(next_states)),
                torch.FloatTensor(dones))

    def __len__(self):
        return len(self.buffer)


# ============================================================================
#  DQNAI agent
# ============================================================================

@dataclass
class ProbeState:
    position: tuple[int, int]
    steps: int
    resources: int


class DQNAI:
    INPUT_DIM = 31
    NUM_ACTIONS = 4

    def __init__(self, maze, model_path=None, epsilon=0.05, seed=None):
        if not HAS_TORCH:
            raise ImportError("DQNAI requires torch. Install: pip install torch")
        if maze.start is None or maze.end is None:
            raise ValueError("Maze must have start and end")

        self.maze = maze
        self.epsilon = epsilon
        self.rng = random.Random(seed)
        self.position = maze.start
        self.steps = 0
        self.resources = 0
        self.collected_coins: set = set()
        self.triggered_traps: set = set()
        self._max_steps = maze.rows * maze.cols * 3

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.q_net = _QNetwork(self.INPUT_DIM, 128, self.NUM_ACTIONS).to(self.device)
        self.q_net.eval()
        if model_path and os.path.isfile(model_path):
            self.q_net.load_state_dict(torch.load(model_path, map_location=self.device, weights_only=True))

    def is_finished(self):
        return self.position == self.maze.end or self.steps >= self._max_steps

    def step(self):
        if self.is_finished():
            return ProbeState(self.position, self.steps, self.resources)
        valid = _valid_moves(self.maze, self.position)
        if not valid:
            self.steps += 1
            return ProbeState(self.position, self.steps, self.resources)
        if self.rng.random() < self.epsilon:
            action = self.rng.choice(valid)
        else:
            state_t = torch.FloatTensor(self._build_state(self.position)).unsqueeze(0).to(self.device)
            with torch.no_grad():
                q_vals = self.q_net(state_t).cpu().numpy().flatten()
            action = max(valid, key=lambda a: q_vals[a])
        self.position = _step_position(self.position, action)
        self.steps += 1
        self._collect_cell(self.position)
        return ProbeState(self.position, self.steps, self.resources)

    def _build_state(self, pos):
        features = []
        r, c = pos
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.maze.rows and 0 <= nc < self.maze.cols:
                    features.append(float(_CELL_ENCODING.get(self.maze.grid[nr][nc].content, 0)))
                else:
                    features.append(-1.0)
                features.append(1.0 if (0 <= nr < self.maze.rows and 0 <= nc < self.maze.cols
                                        and self.maze.grid[nr][nc].content == SYMBOLS["coin"]
                                        and (nr, nc) not in self.collected_coins) else 0.0)
                features.append(1.0 if (0 <= nr < self.maze.rows and 0 <= nc < self.maze.cols
                                        and self.maze.grid[nr][nc].content == SYMBOLS["trap"]
                                        and (nr, nc) not in self.triggered_traps) else 0.0)
        features.append(0.0)
        features.append(self.resources / max(1, abs(self.resources) + 50))
        features.append(min(1.0, self.steps / max(1, self._max_steps)))
        features.append(1.0)
        return np.array(features, dtype=np.float32)

    def _collect_cell(self, cell):
        ct = self.maze.grid[cell[0]][cell[1]].content
        if ct == SYMBOLS["coin"] and cell not in self.collected_coins:
            self.resources += COIN_VALUE; self.collected_coins.add(cell)
        elif ct == SYMBOLS["trap"] and cell not in self.triggered_traps:
            self.resources += TRAP_VALUE; self.triggered_traps.add(cell)


# ============================================================================
#  Training
# ============================================================================

def _build_state_global(maze, pos, collected, triggered, steps, resources, max_steps):
    features = []
    r, c = pos
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            nr, nc = r + dr, c + dc
            if 0 <= nr < maze.rows and 0 <= nc < maze.cols:
                features.append(float(_CELL_ENCODING.get(maze.grid[nr][nc].content, 0)))
            else:
                features.append(-1.0)
            features.append(1.0 if (0 <= nr < maze.rows and 0 <= nc < maze.cols
                                    and maze.grid[nr][nc].content == SYMBOLS["coin"]
                                    and (nr, nc) not in collected) else 0.0)
            features.append(1.0 if (0 <= nr < maze.rows and 0 <= nc < maze.cols
                                    and maze.grid[nr][nc].content == SYMBOLS["trap"]
                                    and (nr, nc) not in triggered) else 0.0)
    features.append(0.0)
    features.append(resources / max(1, abs(resources) + 50))
    features.append(min(1.0, steps / max(1, max_steps)))
    features.append(1.0)
    return np.array(features, dtype=np.float32)


def train_dqn(
    maze_rows=15, maze_cols=15, num_episodes=5000, batch_size=64,
    gamma=0.95, lr=1e-3, epsilon_start=1.0, epsilon_end=0.05,
    epsilon_decay=0.997, target_update_freq=100, buffer_capacity=50000,
    hidden_dim=128, save_path="models/dqn_maze.pth", seed=42, verbose=True,
):
    if not HAS_TORCH:
        raise ImportError("Training requires torch. Install: pip install torch")

    from game.maze.generator import Maze
    from game.maze.strategies import make_normalized_strategies

    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    q_net = _QNetwork(DQNAI.INPUT_DIM, hidden_dim, DQNAI.NUM_ACTIONS).to(device)
    target_net = _QNetwork(DQNAI.INPUT_DIM, hidden_dim, DQNAI.NUM_ACTIONS).to(device)
    target_net.load_state_dict(q_net.state_dict()); target_net.eval()
    optimizer = optim.Adam(q_net.parameters(), lr=lr)
    replay = ReplayBuffer(buffer_capacity)
    loss_fn = nn.SmoothL1Loss()

    epsilon = epsilon_start
    episode_rewards, episode_steps = [], []
    best_avg = float("-inf")
    os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)

    for ep in range(num_episodes):
        cs, ts = make_normalized_strategies(4.0, 1.2)
        maze = Maze.generate(rows=maze_rows, cols=maze_cols, seed=seed + ep + 10000,
                             generation_method="mst", coin_strategy=cs, trap_strategy=ts)
        pos = maze.start
        collected, triggered = set(), set()
        max_s = maze_rows * maze_cols * 3
        steps, resources, total_r = 0, 0, 0.0

        while pos != maze.end and steps < max_s:
            state = _build_state_global(maze, pos, collected, triggered,
                                        steps, resources, max_s)
            valid = _valid_moves(maze, pos)
            if not valid:
                break
            if random.random() < epsilon:
                action = random.choice(valid)
            else:
                st = torch.FloatTensor(state).unsqueeze(0).to(device)
                with torch.no_grad():
                    qv = q_net(st).cpu().numpy().flatten()
                action = max(valid, key=lambda a: qv[a])

            npos = _step_position(pos, action)
            steps += 1; reward = 0.0
            ct = maze.grid[npos[0]][npos[1]].content
            if ct == SYMBOLS["coin"] and npos not in collected:
                reward += COIN_VALUE; resources += COIN_VALUE; collected.add(npos)
            elif ct == SYMBOLS["trap"] and npos not in triggered:
                reward += TRAP_VALUE; resources += TRAP_VALUE; triggered.add(npos)
            reward -= 0.1
            done = (npos == maze.end)
            if done:
                reward += 100.0
            ns = _build_state_global(maze, npos, collected, triggered,
                                     steps, resources, max_s)
            replay.push(state, action, reward, ns, float(done))
            total_r += reward; pos = npos

            if len(replay) >= batch_size:
                sb, ab, rb, nsb, db = replay.sample(batch_size)
                sb, ab, rb, nsb, db = sb.to(device), ab.to(device), rb.to(device), nsb.to(device), db.to(device)
                with torch.no_grad():
                    nq = target_net(nsb).max(dim=1).values
                    target = rb + gamma * nq * (1 - db)
                cq = q_net(sb).gather(1, ab.unsqueeze(1)).squeeze(1)
                loss = loss_fn(cq, target)
                optimizer.zero_grad(); loss.backward()
                torch.nn.utils.clip_grad_norm_(q_net.parameters(), 10.0)
                optimizer.step()
            if done:
                break

        epsilon = max(epsilon_end, epsilon * epsilon_decay)
        if ep % target_update_freq == 0:
            target_net.load_state_dict(q_net.state_dict())
        episode_rewards.append(total_r); episode_steps.append(steps)

        if verbose and ep % 200 == 0:
            ar = np.mean(episode_rewards[-100:]) if len(episode_rewards) >= 100 else np.mean(episode_rewards)
            as_ = np.mean(episode_steps[-100:]) if len(episode_steps) >= 100 else np.mean(episode_steps)
            print(f"[Ep {ep:5d}/{num_episodes}]  ε={epsilon:.3f}  "
                  f"avg_reward={ar:8.1f}  avg_steps={as_:6.1f}  buffer={len(replay):6d}")
            if ar > best_avg:
                best_avg = ar
                torch.save(q_net.state_dict(), save_path)
                if verbose:
                    print(f"  → best saved: {save_path}")

    torch.save(q_net.state_dict(), save_path)
    if verbose:
        print(f"Training done. Model → {save_path}")
    return {
        "episodes": num_episodes,
        "final_avg_reward_100": (np.mean(episode_rewards[-100:]) if len(episode_rewards) >= 100
                                 else float(np.mean(episode_rewards))),
        "final_avg_steps_100": (np.mean(episode_steps[-100:]) if len(episode_steps) >= 100
                                else float(np.mean(episode_steps))),
        "best_avg_reward": float(best_avg), "model_path": save_path,
    }
