# 使用说明

本项目将素材与逻辑分离：素材位于 assets，核心逻辑位于 scripts。支持迷宫生成、可视化、AI 探测模拟，以及导出 JSON。

## 运行环境

- Python 3.10+
- Windows 下可直接运行（默认 Tkinter 可用）

## 目录结构

- assets：素材与配置（颜色/符号/数值）
- scripts：迷宫生成、策略、AI、导出与 UI
- k_centered_maze_puzzle.py：主入口

## 常用命令

以下命令均可直接复制粘贴执行：

### 1) 启动 UI（含 AI 运行/单步/重置）

```bash
python k_centered_maze_puzzle.py 21 21 --ui
```

### 2) 仅生成并打印迷宫（默认含“正态分布”校准）

```bash
python k_centered_maze_puzzle.py 21 21
```

### 3) 跳过校准（更快，但分布更不稳定）

```bash
python k_centered_maze_puzzle.py 21 21 --no-calibrate
```

### 4) 导出 JSON

```bash
python k_centered_maze_puzzle.py 21 21 --export out.json
```

### 5) 评估一组玩家的平均分

```bash
python k_centered_maze_puzzle.py 21 21 --eval
```

## 参数说明

- 迷宫尺寸：直接传入两个数字，如 21 21
- 随机种子：--seed 42
- 目标分数中心：--k 4.0
- 可视化：--ui
- 评估分布：--eval
- 导出 JSON：--export out.json
- 关闭校准：--no-calibrate

示例（带种子与目标分数）：

```bash
python k_centered_maze_puzzle.py 25 25 --seed 123 --k 4.2 --ui
```
