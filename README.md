# 迷宫探险者 Maze Explorer

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
└── files (4)/              # 独立的最优路径求解器（原始交付版）
```

## 游戏功能

- **4 种迷宫生成算法**：最小生成树 Prim、回溯法 DFS、分治法、分支限界法
- **战争迷雾**：3×3 视野，已探索区域灰色、未探索黑色
- **AI 寻路**：SimpleGreedy / MemoryGreedy（带记忆） / DQN（深度强化学习）
- **Boss 战**：回合制，未知 HP 时最大化伤害，已知 HP 时 DP 求最优技能序列
- **最优路径覆盖**：按 `O` 键显示理论最优资源收集路径（金色格子 + 方向箭头）

### 运行

```bash
pip install pygame numpy
python main.py
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

## 算法

### 最优资源收集路径 — 树形 DP

完美迷宫的可走格构成一棵树。问题等价于求 **包含 S 与 E 的最大权连通子树**。

```
best(u) = value(u) + Σ max(0, best(child))
```

- 主干 S→E 必选；分支仅当 `best > 0` 纳入（正确处理"陷阱守卫金币"）
- 时间复杂度 **O(V)**：一次 BFS 建树 + 一遍 DP + 一次 DFS 重建游走
- 非树迷宫自动降级到 BFS 生成树近似解

## 依赖

- Python ≥ 3.11
- pygame ≥ 2.5
- numpy ≥ 1.24（DQN 训练需要）
- torch ≥ 2.0（DQN 训练需要，游戏可不装）
