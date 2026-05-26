# AI 竞技迷宫设计与 AI 玩家挑战系统

这是一个面向课程提交和展示的完整 Python 项目。项目身份是“迷宫设计组”，同时实现 AI 玩家系统。系统支持多种迷宫生成算法、迷宫合法性验证、资源放置、最优资源路径、BOSS 战分支限界求解、AI 玩家策略、pygame 可视化游戏界面、matplotlib 静态输出、命令行运行和 pytest 测试。

## 1. 功能列表

- 五种迷宫算法：DFS 回溯、Prim、Kruskal、递归分割、BFS/分支限界优化。
- 迷宫验证：尺寸、起点、终点、BOSS、连通性、可达性、完美迷宫、墙数、通路数、分支、死胡同。
- 资源放置：金币 `G`、陷阱 `T`、BOSS `B`，保证特殊格子可达。
- 最优资源路径：从 `S` 到 `E`，在不重复计算资源的前提下最大化收益。
- BOSS 战：兼容新旧配置格式，支持技能名称、伤害、冷却、金币消耗和 BOSS 能力接口。
- AI 玩家：贪婪策略、PPO 简化策略、Q-learning 策略、自定义策略加载。
- 游戏核心：移动、碰墙、金币、陷阱、BOSS、终点、暂停、继续、重开、日志、得分。
- pygame UI：开始画面、算法生成回放、开始路径闪烁、游戏内 HUD、BOSS 画面接口、金币/陷阱动画接口。
- 素材接口：图片、精灵图切帧、动画、音乐与音效接口，缺少素材不会崩溃。
- 输出：迷宫 JSON、最佳迷宫 JSON、AI 运行结果、算法对比图、资源路径图、BOSS 时间线、结果摘要。
- 测试：生成器、验证器、资源路径、BOSS、AI、游戏引擎、JSON。

## 2. 迷宫符号说明

| 符号 | 含义 |
|---|---|
| `#` | 墙 |
| `.` | 普通道路 |
| `S` | 起点 |
| `E` | 终点 |
| `G` | 金币，资源值 +50 |
| `T` | 陷阱，资源值 -30 |
| `B` | BOSS |

## 3. 五种迷宫算法

统一入口：

```python
from src.maze.maze_factory import generate_maze
maze = generate_maze(size=15, algorithm="dfs", seed=42)
```

支持：

```text
dfs
prim
kruskal
division
bfs_optimize
```

如果 `size` 小于 5，会自动改为 5；如果是偶数，会自动转换为 `size + 1`。DFS、Prim、Kruskal 生成完美迷宫；递归分割法保证连通但不强制完美；`bfs_optimize` 在 DFS 基础上尝试打开局部墙体来增加分支和挑战性。

## 4. AI 玩家策略

内置策略：

- `greedy`：优先寻找最近金币，尽量避开陷阱，没有金币后前往 BOSS 或终点。
- `ppo`：使用 numpy 实现的轻量 PPO 风格策略，提供策略网络、缓存、训练、保存和加载接口。
- `qlearning`：Q-learning 策略，支持 epsilon-greedy、训练更新、保存和加载 Q 表。
- `custom`：加载自定义策略文件。

自定义策略示例：

```python
from src.ai.base_strategy import BaseAIStrategy

class MyStrategy(BaseAIStrategy):
    name = "my_strategy"

    def choose_action(self, maze, player_state):
        return "RIGHT"

def create_strategy():
    return MyStrategy()
```

运行：

```bash
python run.py --ai custom --maze data/best_maze.json --custom-strategy path/to/strategy.py
```

## 5. 安装依赖

```bash
pip install -r requirements.txt
```

依赖保持轻量：

```text
numpy
matplotlib
pygame
pytest
```

## 6. 命令行运行方式

生成不同算法迷宫：

```bash
python run.py --algorithm dfs --size 15 --seed 42
python run.py --algorithm prim --size 15 --seed 42
python run.py --algorithm kruskal --size 15 --seed 42
python run.py --algorithm division --size 15 --seed 42
python run.py --algorithm bfs_optimize --size 15 --seed 42
```

算法对比：

```bash
python run.py --compare --size 15 --seed 42
```

资源路径优化：

```bash
python run.py --resource data/best_maze.json
```

BOSS 战求解：

```bash
python run.py --boss data/boss_config.json
```

生成最佳迷宫：

```bash
python run.py --best --size 15 --seed 42
```

运行 AI：

```bash
python run.py --ai greedy --maze data/best_maze.json
python run.py --ai ppo --maze data/best_maze.json
python run.py --ai qlearning --maze data/best_maze.json
```

启动 pygame 游戏：

```bash
python run.py --game
python run.py --play --ai greedy
```

一键完整流程：

```bash
python run.py --all --size 15 --seed 42
```

## 7. 修改迷宫尺寸、金币、陷阱数量

命令行可直接修改：

```bash
python run.py --algorithm dfs --size 21 --seed 7 --coins 12 --traps 10
```

代码中可使用：

```python
from src.maze.resource_placer import place_resources
maze = place_resources(maze, coin_count=10, trap_count=8, place_boss=True, seed=42)
```

## 8. BOSS 与玩家技能接口

新格式：

```json
{
  "B": [11, 13, 9, 15],
  "BossAbilities": [
    {"name": "重击", "damage": 8, "cooldown": 3},
    {"name": "护盾", "shield": 5, "cooldown": 4}
  ],
  "PlayerSkills": [
    {"name": "普通攻击", "damage": 2, "cooldown": 0, "cost": 0},
    {"name": "火球术", "damage": 8, "cooldown": 4, "cost": 2}
  ],
  "minRouds": 20,
  "CoinConsumption": 5
}
```

旧格式也兼容：

```json
{
  "B": [11, 13, 9, 15],
  "PlayerSkills": [[8, 4], [2, 0], [4, 2], [6, 3]],
  "minRouds": 20,
  "CoinConsumption": 5
}
```

## 9. 图片素材命名规则

玩家支持两种方式：

第一种：自动切 4×4 精灵图。

```text
assets/images/player/player_spritesheet.png
```

第二种：手动帧目录。

```text
assets/images/player/idle/player_idle_0.png
assets/images/player/idle/player_idle_1.png
assets/images/player/idle/player_idle_2.png
assets/images/player/idle/player_idle_3.png
assets/images/player/move/player_move_down_0.png
...
assets/images/player/frames/player_00.png
...
assets/images/player/frames/player_15.png
```

BOSS 待机动画：

```text
assets/images/boss/idle/boss_idle_0.png
assets/images/boss/idle/boss_idle_1.png
assets/images/boss/idle/boss_idle_2.png
assets/images/boss/idle/boss_idle_3.png
```

地图、UI、特效、背景目录已经预留。缺少图片时，`AssetManager` 会使用默认占位图，不会让程序崩溃。

## 10. 音乐和音效接口

`AudioManager` 支持：

```python
load_bgm(name, path)
play_bgm(name, loop=True)
stop_bgm()
load_sfx(name, path)
play_sfx(name)
set_volume(volume)
```

推荐音效名称：

```text
button_click
maze_loading
start_game
coin_collect
trap_trigger
player_move
boss_appear
skill_cast
boss_hurt
game_win
game_lose
```

音频目录：

```text
assets/audio/bgm/
assets/audio/sfx/
assets/audio/boss/
```

## 11. 输出文件说明

生成迷宫：

```text
outputs/generated_mazes/maze_dfs_15_seed42.json
outputs/generated_mazes/maze_prim_15_seed42.json
outputs/generated_mazes/maze_kruskal_15_seed42.json
outputs/generated_mazes/maze_division_15_seed42.json
outputs/generated_mazes/maze_bfs_optimize_15_seed42.json
```

最佳迷宫：

```text
data/best_maze.json
outputs/generated_mazes/best_maze.json
```

AI 结果：

```text
outputs/ai_runs/ai_greedy_result.json
outputs/ai_runs/ai_ppo_result.json
outputs/ai_runs/ai_qlearning_result.json
```

摘要：

```text
outputs/logs/result_summary.json
```

静态图片：

```text
outputs/figures/
```

## 12. 测试

```bash
pytest -q
```

测试覆盖：五种生成器、迷宫验证、资源路径、BOSS 求解、AI 策略、游戏引擎和 JSON 读写。

## 13. 项目结构

```text
maze_design_project/
├── README.md
├── requirements.txt
├── run.py
├── data/
├── assets/
├── src/
├── outputs/
├── tests/
└── docs/
```
