# 项目结构与维护边界

## 入口

- `main.py`：Pygame 游戏入口。
- `solve_maze.py`：迷宫生成、路径求解和 Boss 技能序列验收 CLI。
- `train_dqn.py`：可选 DQN 训练入口。

## 主实现

`game/` 是唯一维护中的游戏实现：

- `maze/`：迷宫生成、寻路和最优资源路径。
- `battle/`：Boss 规则、模拟和最优技能序列。
- `scenes/`：Pygame 场景协调。
- `entities/`：玩家、地图块、拾取物和标记。
- `ui/`：UI 组件与共享主题参数。
- `assets/`：素材加载、运行时素材和素材源文件。

## 素材约定

- `game/assets/sprites/`：游戏运行时直接加载并随 wheel 打包的成品图片。
- `game/assets/sounds/`：游戏运行时声音素材。
- `game/assets/source/`：只供素材构建工具使用的原始图片，不随 wheel 打包。
- `tools/build_ui_assets.py`：从源文件生成或更新成品 UI 素材。

## 测试约定

- `tests/`：单元、场景和 CLI 回归测试。
- `tests/golden/`：CLI stdout、stderr、退出码和 JSON 的逐字节黄金快照。
- `input.json` 与 `best_maze_design_林士清.json` 保留在根目录，以保持既有 CLI 示例命令兼容。
