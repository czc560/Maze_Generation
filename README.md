# 迷宫探险者 Maze Explorer

当前维护中的主实现是完整的 Pygame 游戏：入口为 `python main.py`，主代码位于
`game/`。`solve_maze.py` 是验收 CLI，`train_dqn.py` 是可选的 DQN 训练入口。
`tools/build_ui_assets.py` 是可选的素材重建工具。仓库仅保留当前 Pygame
实现及其验收、训练、测试和素材构建入口。

详细的模块、素材和测试边界见 [`docs/architecture.md`](docs/architecture.md)。

算法课程设计 — 迷宫生成与最优资源收集路径。

## 项目结构

```
Maze_Generation/
├── main.py                 # 游戏入口
├── solve_maze.py           # 验收 CLI（求解 + 生成迷宫）
├── train_dqn.py            # DQN 训练脚本
├── game/
│   ├── engine.py           # GameEngine — 主循环、显示、时钟
│   ├── scene_manager.py    # 场景栈管理器
│   ├── constants.py        # 全局常量、颜色、事件
│   ├── visibility.py       # 战争迷雾（3×3 视野）
│   ├── maze/
│   │   ├── generator.py    # Maze 类：4种生成算法（Prim/DFS/分治/分支限界）
│   │   ├── optimal_path.py # 最优资源收集路径（树形 DP + JSON I/O）
│   │   ├── strategies.py   # 金币/陷阱放置策略、正态分布校准
│   │   ├── pathfinding.py  # BFS 寻路、距离图
│   │   ├── node.py         # MazeNode 数据结构
│   │   └── symbols.py      # 符号表、方法名规范化
│   ├── scenes/             # 场景：菜单、配置、游戏、Boss战、暂停、结算、策略设置
│   ├── entities/           # 精灵：玩家、迷宫砖、拾取物、标记、动画
│   ├── ai/                 # AI：SimpleGreedy、MemoryGreedy、DQN
│   ├── battle/             # Boss 战规则、最优技能序列 DP
│   ├── ui/                 # UI 组件：按钮、标签、滑块、下拉框、文本框
│   └── assets/             # 资源管理、字体、占位图生成
├── tools/build_ui_assets.py  # 可选素材构建工具
└── tests/                  # 回归、CLI 字节快照和 Pygame 冒烟测试
```

## 游戏功能

- **4 种迷宫生成算法**：最小生成树 Prim、回溯法 DFS、分治法、分支限界法
- **战争迷雾**：3×3 视野，已探索区域灰色、未探索黑色
- **AI 寻路**：SimpleGreedy / MemoryGreedy（带记忆） / DQN（深度强化学习）
- **Boss 战**：回合制，未知 HP 时最大化伤害，已知 HP 时 DP 求最优技能序列
- **最优路径覆盖**：按 `O` 键显示理论最优资源收集路径（金色格子 + 方向箭头）

### 运行

```bash
pip install .
python main.py
```

DQN 功能单独安装：

```bash
pip install ".[dqn]"
```

操作：方向键/WASD 移动、TAB 切换 AI、O 切换最优路径、Esc 暂停。

## 验收 CLI — `solve_maze.py`

### 求解迷宫

```bash
python solve_maze.py maze.json                  # 求解并打印路径
python solve_maze.py maze.json --out result.json # 同时导出 JSON
python solve_maze.py test1.json test2.json --out-dir results/  # 批量
```

输出标准 JSON 格式：
```json
{
  "max_resource": 370,
  "coins_collected": 11,
  "traps_triggered": 6,
  "path_length_steps": 94,
  "path_rc": [[0, 11], [1, 11], ...],
  "visited_cells_rc": [[0, 11], [1, 2], ...],
  "annotated_maze": ["###########S###", "# GTG# *****  #", ...],
  "is_global_optimal": true
}
```

### 生成迷宫

```bash
python solve_maze.py --generate 15 15 --seed 42 --out maze.json
#   --k 4.0 --method mst|backtracking|divide_conquer|branch_bound
```

生成格式（字符串行，兼容评估系统）：
```json
{
  "maze": [
    "###############",
    "# G     #   #G#",
    "### # # # ### #",
    ...
  ]
}
```

符号：`#` 墙 ` ` 路 `S` 起点 `E` 终点 `B` Boss `G` 金币 `T` 陷阱

### Boss 战技能序列验证

检查给定的技能使用序列是否为击败所有 Boss 的**最少回合最优序列**。

```bash
python solve_maze.py --check-sequence input.json                  # 检查并打印结果
python solve_maze.py --check-sequence input.json --out result.json # 同时导出 JSON
```

**输入格式**（`input.json`）：
```json
{
  "B": [20, 35],
  "PlayerSkills": [[5, 0], [10, 2]],
  "SkillSequence": [0, 1, 0, 0, 1]
}
```

| 字段 | 说明 |
|------|------|
| `B` | Boss 血量列表，按顺序击败 |
| `PlayerSkills` | 每项 `[伤害, 冷却时间]`，冷却 C 表示使用后需等待 C 回合 |
| `SkillSequence` | 每回合使用的技能下标，`-1` 表示空过（等待） |

**冷却规则**：每回合开始时所有冷却 -1；使用技能后该技能冷却 = 原始冷却值；**Boss 间冷却不重置**（连续累积）。

**输出格式**：
```json
{
  "legal": true,
  "is_optimal": true,
  "turns_used": 8,
  "optimal_turns": 8,
  "total_damage_dealt": 55,
  "bosses_defeated": 2,
  "bosses_total": 2,
  "errors": [],
  "boss_details": [
    {"boss_index": 0, "hp": 20, "turns": 3, "optimal_turns": 3, "defeated": true},
    {"boss_index": 1, "hp": 35, "turns": 5, "optimal_turns": 5, "defeated": true}
  ],
  "optimal_sequence": [0, 1, 0, 0, 1, 0, 0, 1]
}
```

| 字段 | 说明 |
|------|------|
| `legal` | 序列是否合法（无冷却违规、击败所有 Boss） |
| `is_optimal` | 是否为最少回合最优序列 |
| `turns_used` | 实际消耗回合数 |
| `optimal_turns` | 理论最少回合数（连续 DP 求解） |
| `optimal_sequence` | 参考最优技能序列（含 `-1` 等待） |

**退出码**：最优 → 0，非最优/不合法 → 1。

### 生成最优技能序列

只给定 Boss 血量和玩家技能，直接输出最优 SkillSequence（不做比对）。

```bash
python solve_maze.py --optimal-sequence input.json                  # 自动生成 output_optimal.json
python solve_maze.py --optimal-sequence input.json --out output.json # 指定输出路径
```

**输入格式**（`input.json`）：
```json
{
  "B": [20, 35],
  "PlayerSkills": [[5, 0], [10, 2]]
}
```

输出即在输入基础上补充 `SkillSequence` 字段：
```json
{"B": [20, 35], "PlayerSkills": [[5, 0], [10, 2]], "SkillSequence": [0, 1, 0, 0, 1, 0, 0, 1]}
```

## 算法

### 最优资源收集路径 — 树形 DP

完美迷宫的可走格构成一棵树。问题等价于求 **包含 S 与 E 的最大权连通子树**。

```
best(u) = value(u) + Σ max(0, best(child))
```

- 主干 S→E 必选；分支仅当 `best > 0` 纳入（正确处理"陷阱守卫金币"）
- 时间复杂度 **O(V)**：一次 BFS 建树 + 一遍 DP + 一次 DFS 重建游走
- 非树迷宫自动降级到 BFS 生成树近似解

### Boss 战最优技能序列 — 连续状态 DP

多 Boss 连续挑战，冷却不重置。问题等价于在联合状态空间上求最短路径。

```
solve(boss_idx, hp_left, cds) → (min_turns, best_action)

转移（每回合）：
  1. cds ← tick(cds)                    # 所有冷却 -1
  2. 尝试每个可用技能 i（cds[i] == 0）
     hp' ← hp_left - damage[i]
     cds' ← ticked, cds'[i] ← cd[i] + 1
     if hp' ≤ 0 → advance to next boss   # 冷却累积
  3. 否则等待（只能在没有可用技能时）
```

- 状态空间 `(boss_idx, hp_left, cds_tuple)`，使用 `@lru_cache` 记忆化
- 冷却跨 Boss 累积，保证结果与验收系统的连续冷却规则一致
- 时间复杂度最坏 `O(ΣHP × C^K)`，其中 C 为最大冷却值，K 为技能数；实际可达状态远小于上界

## 依赖

- Python ≥ 3.11
- pygame ≥ 2.5
- numpy ≥ 1.24（仅 DQN 需要）
- torch ≥ 2.0（仅 DQN 需要，普通 Pygame 游戏不强制安装）
- Pillow ≥ 9.0（仅素材构建脚本需要）

开发环境可执行 `pip install -e ".[dev,dqn,assets]"`；只构建素材时可执行
`pip install ".[assets]"`。全部依赖以 `pyproject.toml` 为唯一配置来源。

## 最佳防守迷宫筛选逻辑

本项目提交的 `best_maze_design_林士清.json` 按迷宫设计方的防守目标筛选：迷宫不是为了让玩家收益最高，而是为了提高通关难度，并尽量让模拟玩家的失败率接近 50%。

筛选流程如下：

1. 使用项目自带生成器自然生成候选迷宫，不手动移动起点、终点或 BOSS。
2. 遍历多组生成参数，包括生成算法、随机种子和资源参数 `k`。
3. 对每个候选迷宫运行 19 个模拟玩家，玩家激进程度从 `0.0` 到 `1.0` 均匀取样。
4. 统计每个候选的失败人数和失败率，优先选择失败率最接近 50% 的迷宫。
5. 如果多个候选失败率接近，则按防守指标继续排序：
   - 模拟玩家平均得分更低；
   - BOSS 战前资源值更低；
   - 到达 BOSS 的步数更长；
   - 陷阱压力更高。
6. 对入选迷宫重新运行 `solve_maze.py --require-end`，确认文件格式、起点终点、连通性和最优路径回放合法。
7. 基准结果写入 `docs/maze_baseline.md`，其中“BOSS 战后最终剩余资源价值”按 Boss 战返回后的资源值统计，而不是简单复用 BOSS 战前资源。

当前提交迷宫的筛选结果：

| 指标 | 数值 |
| --- | ---: |
| 生成算法 | `backtracking` |
| 随机种子 | `642` |
| 资源参数 | `k = 2.2` |
| 模拟玩家失败数 | `8 / 19` |
| 失败率 | `42.11%` |
| BOSS 战前资源值 | `430` |
| BOSS 战后最终剩余资源价值 | `430` |
| 步数 | `102` |
| 最终剩余资源价值 / 步数 | `4.215686` |
