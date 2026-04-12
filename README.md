# minote-driver

`minote-driver` 是一个面向工程集成的本地执行层，用 Selenium 驱动 Chrome，对小米云笔记待办页提供可复用的自动化能力。

当前范围聚焦于 `https://i.mi.com/note/#/` 中的待办页面，而不是完整笔记系统。

上层面向 agent 的封装位于 `minote-skill`。

## 定位

- 本地浏览器自动化 driver
- 小米云笔记待办页执行层
- 可被 Python、CLI 和上层 skill 复用的 runtime

不负责：

- 中文自然语言解析
- 通用 agent 编排
- 私密笔记能力

## 当前能力

已实现并验证：

- 读取未完成待办
- 读取已完成待办
- 创建待办
- 修改待办标题
- 标记待办为已完成
- 将已完成待办恢复为未完成
- 删除待办

暂不支持：

- 私密笔记
- 私密笔记读取
- 私密笔记搜索

## 工作原理

`minote-driver` 通过 Selenium 驱动本地 Chrome，并复用项目目录中的独立浏览器配置：

- Chrome 用户数据目录：`chrome_profile/`
- 驱动路径：`bin/chromedriver.exe`

这样做的目的是：

- 不污染系统默认浏览器环境
- 登录态可以保存在项目本地
- 后续脚本可以直接复用同一份登录状态

执行路径分为三层：

- `src/minote/`：底层客户端和命令执行器
- `scripts/cli/`：工程入口脚本
- `skills/`：给上层 agent 使用的 skill 包装说明

## 快速开始

### 1. 准备依赖

要求：

- Windows
- 已安装 Google Chrome
- 需要自行放置与本机 Chrome 匹配的 `bin/chromedriver.exe`，但该二进制文件不纳入仓库版本控制
- 已安装 Python
- 已安装 `selenium`

如果还没安装 Selenium：

```bash
pip install selenium
```

推荐使用独立虚拟环境。

### 2. 初始化本地登录态

先运行：

```bash
python scripts/cli/open_mi_cloud.py
```

这个脚本会：

- 启动 Chrome
- 使用项目内的 `chrome_profile/`
- 打开小米云笔记页面

首次使用时，你需要在这个浏览器里手动登录一次小米账号。

登录成功后，后续无头脚本会复用这份登录态。

### 3. 验证基础能力

```bash
python scripts/verify/verify_todo_crud.py
python scripts/verify/verify_commands.py
```

## 常用命令

命令入口文件：`scripts/cli/mi_note_commands.py`

统一 skill 入口文件：`scripts/cli/run_skill.py`

推荐顺序：

- 直接调试底层能力时，用 `mi_note_commands.py`
- 给上层调度层或 agent 对接时，用 `run_skill.py`

### 读取未完成待办

```bash
python scripts/cli/mi_note_commands.py read-pending
```

### 读取已完成待办

```bash
python scripts/cli/mi_note_commands.py read-completed
```

### 创建待办

```bash
python scripts/cli/mi_note_commands.py create "明天下午买咖啡豆"
```

### 修改待办标题

```bash
python scripts/cli/mi_note_commands.py update "旧标题" "新标题"
```

### 标记完成

```bash
python scripts/cli/mi_note_commands.py complete "洗衣服"
```

### 恢复为未完成

```bash
python scripts/cli/mi_note_commands.py restore "洗车"
```

### 删除待办

```bash
python scripts/cli/mi_note_commands.py delete "剪头发"
```

## 统一 Skill 调用入口

如果上层希望通过 `minote-skill` 的统一入口调用，而不是直接依赖具体命令脚本，可以使用：

```bash
python scripts/cli/run_skill.py minote-todo read-pending
python scripts/cli/run_skill.py minote-todo create --title "明天下午买咖啡豆"
python scripts/cli/run_skill.py minote-todo update --old-title "旧标题" --new-title "新标题"
python scripts/cli/run_skill.py minote-todo complete --title "洗衣服"
python scripts/cli/run_skill.py minote-todo restore --title "洗车"
python scripts/cli/run_skill.py minote-todo delete --title "剪头发"
```

这个入口的作用是把：

- skill 名
- command 名
- 参数

统一收口到一个稳定 CLI，便于后续 agent 或调度层直接调用。

这不是自然语言入口，而是结构化命令入口。

## Python 调用方式

如果你想从 Python 里直接调用命令执行器：

```python
from minote import execute_command

result = execute_command("create", title="测试待办")
print(result)
```

如果你想直接调用底层客户端：

```python
from minote import MiNoteClient, SECTION_PENDING

with MiNoteClient(headless=True) as client:
    items = client.read_todos(SECTION_PENDING)
    for item in items:
        print(item.title)
```

## 项目文件说明

- `scripts/cli/open_mi_cloud.py`
用途：启动带项目本地 profile 的 Chrome，并打开小米云笔记页面

- `src/minote/client.py`
用途：底层浏览器自动化客户端，提供待办 CRUD 能力

- `scripts/cli/mi_note_commands.py`
用途：命令执行层和 CLI 入口

- `API.md`
用途：更详细的接口文档

- `scripts/verify/verify_todo_crud.py`
用途：验证客户端层 CRUD 是否真实可用

- `scripts/verify/verify_commands.py`
用途：验证命令层是否真实可用

- `scripts/debug/`
用途：调试、DOM 探查、一次性验证脚本收纳目录

- `skills/minote-todo/SKILL.md`
用途：把当前待办自动化能力整理成可复用的 skill 定义，方便后续上层编排直接调用

## 工程接口

推荐的集成接口如下：

- Python API：`minote.execute_command`
- 底层客户端：`minote.MiNoteClient`
- 命令行入口：`scripts/cli/mi_note_commands.py`
- 统一 skill 入口：`scripts/cli/run_skill.py`

如果你是在写脚本或服务，优先使用 Python API。

如果你是在接 agent/tool runner，优先使用 `run_skill.py`。

## 已验证行为

目前已经对真实页面跑通过完整待办链路：

1. 创建待办
2. 修改标题
3. 标记完成
4. 恢复到未完成
5. 删除待办

其中删除路径依赖真实 UI 交互：

1. 对待办项右键
2. 点击 `删除`
3. 在确认弹窗中再次点击 `删除`

## 限制与说明

- 当前实现依赖小米云笔记现有网页 DOM 结构
- 页面改版后可能需要重新适配选择器
- 搜索入口已经探明，但搜索结果行为验证还不如待办 CRUD 完整
- 私密笔记目前明确排除，不做读取和搜索支持

## 适用场景

适合：

- 本地自动化脚本
- agent tool backend
- 面向固定任务的待办操作服务

不适合：

- 无人值守长期稳定生产运行承诺
- 绕过登录验证或风控
- 把网页自动化误当成官方稳定 API

## 接口文档

详细接口说明见：`API.md`

## 与 minote-skill 的关系

当前策略是分层维护：

- `minote-driver`：执行层、CLI、验证脚本、运行时约束
- `minote-skill`：skill 定义、调用协议、上层能力包装

driver 负责把动作做成，skill 负责把动作变成可调用能力。

## 仓库边界

当前仓库以 `minote-driver` 为主，包含运行时、CLI 和本地 skill 定义。

发布到公开 git 仓库时遵循以下边界：

- 不提交 `chrome_profile/`
- 不提交 `bin/chromedriver.exe`
- 不提交本地演示目录 `readme-demo/`

如果后续按双仓库拆分：

- `minote-driver` 仓库保留底层执行层和 CLI
- `minote-skill` 仓库保留 skill 定义、调用约定和面向 agent 的封装
