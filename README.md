# MaaLK

MaaLK 是一个基于 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 的《洛克王国：世界》自动化学习项目。

本 fork 目前只保留少量自用/学习性质任务，重点用于研究 MaaFramework Pipeline、自定义 Agent、图像识别和 Windows 输入模拟。

## 仅供学习声明

本项目仅用于学习、研究和技术交流，内容包括自动化流程编排、图像识别、MaaFramework 插件式开发、Windows 输入模拟等方向。

请勿将本项目用于商业用途、破坏游戏公平性、影响他人体验或违反相关服务条款的场景。使用者应自行承担运行脚本、安装驱动、连接游戏窗口和修改系统输入组件带来的风险。

《洛克王国：世界》及相关素材、名称、商标归其权利方所有。本项目与游戏官方无关。

## 功能

当前只保留以下任务：

| 任务 | 说明 |
| --- | --- |
| 刷向阳花 | 从原 AHK 脚本迁移而来，支持完整前置和只鞠躬循环两种模式 |
| 随机连点器 | 从原 AHK 连点脚本迁移而来，在当前鼠标位置执行随机间隔左键点击 |
| 自动聚能 | 识别聚能图标后点击，或按配置改为按 `x` |
| 战斗脱离 | 识别战斗脱离入口，点击或按 `Esc` 后确认退出 |
| 传说精灵 | 按技能顺序执行普通战斗，可选使用印记 |
| 精灵首领 | 支持普通阶段、特殊阶段技能顺序，以及奖励阶段印记处理 |
| 稀兽花种 | 按技能顺序战斗，检测到捕捉提示后执行捕捉和领奖流程 |

## 技能顺序语法

传说精灵、精灵首领、稀兽花种使用同一套技能顺序语法。

| 字符 | 含义 |
| --- | --- |
| `1`-`4` | 使用对应技能；在背包段中表示使用对应物品 |
| `x` / `X` | 聚能 |
| `q` / `Q` | 打开背包 |
| `r` / `R` | 关闭背包并回到技能界面 |

重复语法：

| 写法 | 含义 | 示例 |
| --- | --- | --- |
| `|操作|次数` | 重复指定次数 | `|1x|3` 展开为 `1x1x1x` |
| `||操作` | 近似无限循环 | `||1x` 会反复执行 `1x` |
| `|操作|a` | 近似无限循环 | `|1x|a` 会反复执行 `1x` |

常用示例：

| 输入 | 含义 |
| --- | --- |
| `||1x` | 每轮使用技能 1 后聚能 |
| `||q2rx` | 打开背包使用 2 号物品，关闭背包后聚能 |
| `3x4x||1x` | 先执行技能 3/4 与聚能，再循环技能 1 + 聚能 |

## 安装流程

### 1. 下载安装包

推荐从 GitHub Actions 下载最新构建产物：

1. 打开仓库的 `Actions` 页面。
2. 进入 `install` 工作流。
3. 选择最新一次成功运行。
4. 在 `Artifacts` 中下载 `MaaLK-win-x86_64`。
5. 解压到一个固定目录，例如 `D:\Apps\MaaLK`。

如果使用正式 tag 发布，也可以从 `Releases` 页面下载对应的 zip 包。

### 2. 运行依赖说明

从 GitHub Actions 下载的 `MaaLK-win-x86_64` 已经内置以下内容，普通使用者不需要额外安装：

- MFAAvalonia 图形界面。
- MaaFramework 运行库。
- Windows x64 Python 运行时。
- Agent 所需 Python 依赖。
- `interception.dll` 用户态库。

仍然需要手动安装的是 Interception 驱动本体。它是 Windows 内核驱动，必须由使用者在本机安装一次并重启，不能只靠正式包内置 DLL 完成。

正式包保留了 `agent/bootstrap.py` 和日志输出。若 Agent 启动失败，可以查看：

```powershell
Get-Content .\agent\logs\bootstrap_*.log -Tail 200
Get-Content .\agent\logs\agent_*.log -Tail 200
```

如果你是从源码运行，而不是使用 Actions 产物，需要自己准备 Python 环境并安装 Agent 依赖：

```powershell
python -m pip install -r .\agent\requirements.txt
```

### 3. 安装 Interception 驱动

本项目的游戏内输入依赖 Interception 驱动。正式包已经内置 `interception.dll`，但首次使用前仍需要安装驱动本体，并重启电脑。

1. 下载 [Interception](https://github.com/oblitum/Interception)。
2. 解压后，以管理员身份打开 PowerShell 或 CMD。
3. 进入 `command line installer` 目录。
4. 执行：

```powershell
.\install-interception.exe /install
```

5. 重启电脑。

卸载驱动时使用：

```powershell
.\install-interception.exe /uninstall
```

然后同样需要重启。

### 4. 启动 MaaLK

1. 打开解压目录中的 `MFAAvalonia.exe`。
2. 资源类型选择 `桌面`。
3. 控制器类型选择 `桌面端`。
4. 当前控制器选择《洛克王国：世界》窗口。
5. 勾选需要执行的任务。
6. 建议先在 MFA 里设置全局启动/停止快捷键，然后切回游戏窗口后用快捷键启动任务。

Interception 发送的是真实键鼠输入，通常需要游戏窗口处于前台或能够被激活。若任务开始后游戏内没有动作，先确认：

- 已安装驱动并重启。
- 游戏窗口标题能被识别。
- MFA 日志中没有 Agent 启动失败。
- 当前控制器选中的是游戏窗口。
- 以管理员权限启动 MFA 后再试一次。

## 本地开发

```powershell
git clone https://github.com/missht0/lkwg.git
cd lkwg
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r tools\requirements.txt
.\.venv\Scripts\python.exe -m pip install -r agent\requirements.txt
npm ci
```

常用校验：

```powershell
.\.venv\Scripts\python.exe -m py_compile agent\custom\action\*.py agent\custom\reco\*.py agent\custom\interception_controller.py
.\.venv\Scripts\python.exe tools\validate_schema.py --schema-dir deps\tools --resource-dirs assets\resource\base\pipeline --interface-files assets\interface.json --task-dirs assets\resource\tasks
npx @nekosu/maa-tools check
```

本地打包需要先准备 MaaFramework 和 MFAAvalonia 依赖；正式包还会在 GitHub Actions 中自动打入 Windows Python 运行时、Agent 依赖和 `interception.dll`。普通使用者建议直接下载 GitHub Actions 产物。

## 项目结构

| 路径 | 说明 |
| --- | --- |
| `assets/interface.json` | 项目入口配置，声明控制器、资源和任务导入 |
| `assets/resource/tasks` | 任务入口和 UI 配置 |
| `assets/resource/base/pipeline` | MaaFramework Pipeline 流程 |
| `agent/main.py` | Agent 子进程入口 |
| `agent/custom/action` | 自定义动作 |
| `agent/custom/interception_controller.py` | Interception 输入控制封装 |
| `.github/workflows/install.yml` | GitHub Actions 打包流程 |

## 鸣谢

- [krendluck/lkwg](https://github.com/krendluck/lkwg)：原项目参考来源。
- [MaaFramework](https://github.com/MaaXYZ/MaaFramework)：核心自动化框架。
- [MFAAvalonia](https://github.com/SweetSmellFox/MFAAvalonia)：图形化任务管理器。
- [M9A](https://github.com/MAA1999/M9A)：Maa 项目组织方式和实践参考。
- [Interception](https://github.com/oblitum/Interception)：底层键鼠输入驱动与用户态 DLL。
- 原 AHK 脚本：`luoke_mode2.ahk` 与 `luoke_clicker.ahk` 为向阳花和连点器迁移提供了基础流程。

## License

本项目沿用仓库中的 [MIT License](./LICENSE)。
