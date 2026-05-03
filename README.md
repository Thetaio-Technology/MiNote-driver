# minote-driver

`minote-driver` 是一个面向工程集成的本地执行层，对小米云笔记待办页提供可复用的自动化能力。

当前范围聚焦于 `https://i.mi.com/note/#/` 中的待办页面，而不是完整笔记系统。

上层面向 agent 的封装位于 `minote-skill`。

## 定位

- 本地自动化 driver（支持 HTTP 直连和浏览器模拟两种模式）
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

## 驱动模式

minote-driver 支持两种驱动模式，通过 `minote.toml` 配置切换：

| 模式 | 配置值 | 原理 | 依赖 |
|------|--------|------|------|
| **HTTP（默认）** | `http` | 直接调用小米云笔记 REST API | `requests`, `pycryptodome` |
| **Selenium** | `selenium` | 浏览器 DOM 自动化 | `selenium`, Chrome, chromedriver |

HTTP 模式无需启动浏览器，速度更快、资源占用更低，推荐作为默认选择。Selenium 模式作为兼容方案保留。

配置文件 `minote.toml`（项目根目录）：

```toml
[driver]
mode = "http"    # "http"（默认，轻量）或 "selenium"（浏览器模拟）
```

两种模式对外的 Python API 和 CLI 接口完全一致，上层调用者无需感知底层实现。

## 工作原理

### HTTP 模式（默认）

直接调用小米云笔记的 REST API（`https://i.mi.com/`），无需启动浏览器：

- 从 `chrome_profile/` 读取 Chrome 本地 Cookie（AES-GCM 解密）
- 使用 `requests.Session` 发送 HTTP 请求
- 认证方式：Cookie + request body 中的 `serviceToken`

首次使用仍需通过浏览器登录一次以保存登录态。登录后 Chrome 可关闭，后续操作完全无浏览器。

### Selenium 模式

通过 Selenium 驱动本地 Chrome，并复用项目目录中的独立浏览器配置：

- Chrome 用户数据目录：`chrome_profile/`
- 驱动路径：`bin/chromedriver.exe`

### 共同基础

两种模式共享同一份 `chrome_profile/` 登录态：

- 不污染系统默认浏览器环境
- 登录态保存在项目本地
- 后续脚本直接复用同一份登录状态

执行路径分为三层：

- `src/minote/`：底层客户端和命令执行器
- `scripts/cli/`：工程入口脚本
- `skills/`：给上层 agent 使用的 skill 包装说明

## 快速开始

### 1. 准备依赖

要求：

- Windows
- 已安装 Google Chrome
- Python 3.11+
- 已安装依赖包

安装依赖：

```bash
# HTTP 模式（默认，推荐）
pip install requests pycryptodome

# Selenium 模式（可选，仅在 mode=selenium 时需要）
pip install selenium

# 全部安装
pip install requests pycryptodome pywin32 selenium
```

> HTTP 模式下不需要 `chromedriver`，也不需要 Chrome 在运行。Selenium 模式需要自行放置与本机 Chrome 匹配的 `bin/chromedriver.exe`。

推荐使用独立虚拟环境。

### 2. 初始化本地登录态

首次使用前，先运行：

```bash
python scripts/cli/open_mi_cloud.py
```

这个脚本会：

- 启动 Chrome（使用项目内的 `chrome_profile/`）
- 打开小米云笔记页面

首次使用时，你需要在这个浏览器里手动登录一次小米账号。

登录成功后关闭浏览器即可。后续 HTTP 模式会直接从 `chrome_profile/` 读取登录态，无需再次打开浏览器。

> `serviceToken` 会过期。过期后 API 返回 401，此时重新运行 `open_mi_cloud.py` 登录一次即可。

### 3. 验证基础能力

```bash
# HTTP 模式验证（默认）
python scripts/verify/verify_http_crud.py

# Selenium 模式验证
python scripts/verify/verify_todo_crud.py
python scripts/verify/verify_commands.py
```

## 常用命令

命令入口文件：`scripts/cli/mi_note_commands.py`

统一 skill 入口文件：`scripts/cli/run_skill.py`

推荐顺序：

- 直接调试底层能力时，用 `mi_note_commands.py`
- 给上层调度层或 agent 对接时，用 `run_skill.py`

以下命令在 HTTP 和 Selenium 模式下完全一致：

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

## Python 调用方式

### 命令执行器（推荐，模式无关）

```python
from minote import execute_command

# 自动根据 minote.toml 配置选择 HTTP 或 Selenium 模式
result = execute_command("create", title="测试待办")
print(result)
```

### HTTP 客户端（直接使用）

```python
from minote import MiNoteHttpClient, SECTION_PENDING

client = MiNoteHttpClient()
items = client.read_todos(SECTION_PENDING)
for item in items:
    print(item.title)
```

### Selenium 客户端（传统方式）

```python
from minote import MiNoteClient, SECTION_PENDING

with MiNoteClient(headless=True) as client:
    items = client.read_todos(SECTION_PENDING)
    for item in items:
        print(item.title)
```

## 项目文件说明

- `minote.toml`
  用途：驱动模式配置文件

- `src/minote/http_client.py`
  用途：HTTP/slim 模式客户端，直接调用 REST API，无需浏览器

- `src/minote/_cookies.py`
  用途：Chrome Cookie 提取与解密（DPAPI + AES-GCM）

- `src/minote/_types.py`
  用途：共享 Protocol 接口、数据模型、常量

- `src/minote/client.py`
  用途：Selenium 模式客户端，浏览器自动化

- `src/minote/commands.py`
  用途：命令执行层，根据配置分发到对应客户端

- `src/minote/config.py`
  用途：路径常量、TOML 配置加载

- `scripts/cli/open_mi_cloud.py`
  用途：启动带项目本地 profile 的 Chrome，首次登录用

- `scripts/cli/mi_note_commands.py`
  用途：命令执行层和 CLI 入口

- `scripts/verify/verify_http_crud.py`
  用途：验证 HTTP 模式 CRUD 是否真实可用

- `scripts/verify/verify_todo_crud.py`
  用途：验证 Selenium 模式 CRUD 是否真实可用

- `scripts/verify/verify_commands.py`
  用途：验证命令层是否真实可用

- `scripts/debug/`
  用途：调试、API 抓包、一次性验证脚本收纳目录

- `docs/mi-note-api.md`
  用途：小米云笔记 REST API 逆向文档

- `API.md`
  用途：更详细的接口文档

## 工程接口

推荐的集成接口如下：

- Python API：`minote.execute_command`（模式无关）
- HTTP 客户端：`minote.MiNoteHttpClient`
- Selenium 客户端：`minote.MiNoteClient`
- 命令行入口：`scripts/cli/mi_note_commands.py`
- 统一 skill 入口：`scripts/cli/run_skill.py`

如果你是在写脚本或服务，优先使用 Python API。

如果你是在接 agent/tool runner，优先使用 `run_skill.py`。

## 限制与说明

- HTTP 模式：`list_sidebar_items`、`open_section`、`get_search_placeholder` 等 UI 专属操作不可用
- Selenium 模式：依赖小米云笔记现有网页 DOM 结构，页面改版后可能需要重新适配选择器
- 搜索为前端本地过滤，两种模式均通过内存匹配实现
- 私密笔记目前明确排除，不做读取和搜索支持

## 适用场景

适合：

- 本地自动化脚本
- agent tool backend
- 面向固定任务的待办操作服务
- 对速度和资源有要求的批量操作（HTTP 模式）

不适合：

- 无人值守长期稳定生产运行承诺
- 绕过登录验证或风控
- 把网页自动化误当成官方稳定 API

## 接口文档

详细接口说明见：`API.md`

API 逆向分析详见：`docs/mi-note-api.md`

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
