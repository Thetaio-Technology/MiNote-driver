# MiNote

通过浏览器自动化操作小米云笔记待办的本地项目。

当前实现重点是 `https://i.mi.com/note/#/` 里的待办能力，而不是完整笔记系统。

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

项目通过 Selenium 驱动本地 Chrome，并复用项目目录中的独立浏览器配置：

- Chrome 用户数据目录：`chrome_profile/`
- 驱动路径：`bin/chromedriver.exe`

这样做的目的是：

- 不污染系统默认浏览器环境
- 登录态可以保存在项目本地
- 后续脚本可以直接复用同一份登录状态

## 快速开始

### 1. 准备依赖

要求：

- Windows
- 已安装 Google Chrome
- 已放置与本机 Chrome 匹配的 `bin/chromedriver.exe`
- 已安装 Python
- 已安装 `selenium`

如果还没安装 Selenium：

```bash
pip install selenium
```

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

## 常用命令

命令入口文件：`scripts/cli/mi_note_commands.py`

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

## 接口文档

详细接口说明见：`API.md`

## Skill 化方向

当前阶段不做中文自然语言解析器，优先把已经验证过的底层 Selenium 能力整理成 skill。

现状是：

- 底层执行框架已经具备真实可跑的待办 CRUD
- 上层可以直接复用 `scripts/cli/mi_note_commands.py` 或 `minote.execute_command`
- `skills/minote-todo/SKILL.md` 负责描述这个能力的边界、入口和推荐调用方式

这样做的目标是先把执行层沉淀稳定，再决定后续是否需要增加意图映射或更高层的代理逻辑。
