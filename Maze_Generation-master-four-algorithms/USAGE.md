# 使用说明

本项目将素材与逻辑分离：素材位于 `assets`，核心逻辑位于 `scripts`。支持迷宫生成、可视化、AI 探测模拟，以及导出 JSON。

本版本新增 4 种迷宫生成算法：

- `divide_conquer`：分治法 / 递归分割
- `backtracking`：回溯法 / 随机 DFS
- `branch_bound`：分支限界法 / 带路径长度下界的主路径搜索
- `mst`：最小生成树算法 / 随机 Prim

## 运行环境

- Python 3.10+
- Windows 下可直接运行（默认 Tkinter 可用）

## 目录结构

- `assets`：素材与配置（颜色/符号/数值）
- `scripts`：迷宫生成、策略、AI、导出与 UI
- `k_centered_maze_puzzle.py`：主入口

## 常用命令

### 1) 启动 UI（可在界面选择算法）

```bash
python k_centered_maze_puzzle.py 21 21 --ui
```

### 2) 使用最小生成树算法生成迷宫

```bash
python k_centered_maze_puzzle.py 21 21 --method mst
```

### 3) 使用回溯法生成迷宫

```bash
python k_centered_maze_puzzle.py 21 21 --method backtracking
```

### 4) 使用分治法生成迷宫

```bash
python k_centered_maze_puzzle.py 21 21 --method divide_conquer
```

### 5) 使用分支限界法生成迷宫

```bash
python k_centered_maze_puzzle.py 21 21 --method branch_bound
```

### 6) 跳过校准（更快，但分布更不稳定）

```bash
python k_centered_maze_puzzle.py 21 21 --method backtracking --no-calibrate
```

### 7) 导出 JSON

```bash
python k_centered_maze_puzzle.py 21 21 --method mst --export out.json
```

### 8) 评估一组玩家的平均分

```bash
python k_centered_maze_puzzle.py 21 21 --method branch_bound --eval
```

## 参数说明

- 迷宫尺寸：直接传入两个数字，如 `21 21`
- 随机种子：`--seed 42`
- 目标分数中心：`--k 4.0`
- 迷宫算法：`--method mst | backtracking | divide_conquer | branch_bound`
- 可视化：`--ui`
- 评估分布：`--eval`
- 导出 JSON：`--export out.json`
- 关闭校准：`--no-calibrate`

示例（带种子、目标分数与算法）：

```bash
python k_centered_maze_puzzle.py 25 25 --seed 123 --k 4.2 --method divide_conquer --ui
```
