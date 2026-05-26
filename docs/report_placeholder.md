# 项目报告占位模板

## 1. 项目背景

本项目实现 AI 竞技迷宫设计与 AI 玩家挑战系统，包括迷宫生成、验证、资源路径、BOSS 战、AI 玩家和可视化界面。

## 2. 系统架构

核心模块：

- `src/maze/`：迷宫生成、验证、资源放置、最佳迷宫；
- `src/resource/`：最优资源路径；
- `src/boss/`：BOSS 战分支限界；
- `src/ai/`：AI 策略；
- `src/game/`：游戏逻辑；
- `src/ui/`：pygame UI 与素材/动画/音频接口；
- `src/visualization/`：matplotlib 可视化；
- `tests/`：自动测试。

## 3. 实验结果

可运行：

```bash
python run.py --all --size 15 --seed 42
```

然后查看：

```text
outputs/logs/result_summary.json
outputs/figures/
outputs/generated_mazes/
outputs/ai_runs/
```
