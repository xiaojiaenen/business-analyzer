# CodeGraph 使用指南

CodeGraph 是 Rust 内核的代码知识图谱（tree-sitter 解析 + SQLite 存储），将每个符号、调用边、文件预先索引。本 skill 在 Phase 1/2 大量使用它进行业务分析。

> 仓库：https://github.com/colbymchenry/codegraph  
> 官网文档：https://colbymchenry.github.io/codegraph/

---

## 安装与初始化

### 安装 CLI（用户执行，agent 不能代劳）

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh

# Windows (PowerShell)
irm https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.ps1 | iex

# 或者 npm（已有 Node 时）
npm i -g @colbymchenry/codegraph
```

CLI 自带了 Node 运行时，不需要本机装 Node.js。

### 连接 Agent

```bash
codegraph install
```

这个交互式安装器会**自动探测已安装的 Agent（Claude Code / Cursor / Codex / opencode / Hermes / Gemini / Antigravity / Kiro）**，写入 MCP 配置 + 指令文件 + 权限。**这一步只配置不索引**，索引在下一步。

非交互式：
```bash
codegraph install --yes                          # 自动探测，全局安装
codegraph install --target=claude,cursor --yes   # 指定目标
codegraph install --location=local               # 项目本地配置
```

### 初始化项目

```bash
cd your-project
codegraph init
```

**一个命令 = 创建 `.codegraph/` + 构建全图**。之后文件监听器自动保持索引同步（FSEvents/inotify/ReadDirectoryChangesW），零配置，不需要手动 `codegraph sync`。

### 升级

```bash
codegraph upgrade          # 升级到最新
codegraph upgrade --check  # 只看不升
```

---

## 工具速查（MCP 模式）

**默认只暴露一个工具**：`codegraph_explore`。CodeGraph 设计哲学是"一个强工具比多个窄工具更能引导 agent 走对路"。

| 工具 | MCP 默认 | 用途 | 本 skill 主要用在哪 |
|------|---------|------|-------------------|
| `codegraph_explore` | ✅ 暴露 | **几乎所有问题的首选** — 一次返回相关符号的源码 + 调用路径 + blast-radius | Phase 2 全程 |
| `codegraph_node` | ❌ 需启用 | 单个符号详情 + 源码 + 调用者 | 深入关键符号 |
| `codegraph_search` | ❌ 需启用 | 按名称搜符号 | 找特定实体 |
| `codegraph_files` | ❌ 需启用 | 文件树，比 Glob 快 100 倍 | Phase 1 了解结构 |
| `codegraph_callers` | ❌ 需启用 | 谁调用了这个符号 | 追踪调用链上游 |
| `codegraph_callees` | ❌ 需启用 | 这个符号调用了谁 | 追踪调用链下游 |
| `codegraph_impact` | ❌ 需启用 | 改了它会影响什么 | Phase 2.5 领域划分 |
| `codegraph_status` | ❌ 需启用 | 索引统计 | Phase 1 确认索引可用 |

**如何启用更多工具**：在 MCP server 环境变量中设置：
```
CODEGRAPH_MCP_TOOLS=explore,node,search,callers,callees,impact,files,status
```

**即使 MCP 不暴露，CLI 永远可用**：
```bash
codegraph query "Order"          # codegraph_search 的 CLI 等价
codegraph explore "order flow"   # codegraph_explore 的 CLI 等价
codegraph node "OrderService"    # codegraph_node 的 CLI 等价
codegraph files                  # codegraph_files 的 CLI 等价
codegraph callers "createOrder"  # codegraph_callers 的 CLI 等价
codegraph callees "createOrder"  # codegraph_callees 的 CLI 等价
codegraph impact "Order.status"  # codegraph_impact 的 CLI 等价
codegraph status                 # codegraph_status 的 CLI 等价
```

---

## 核心使用原则

### Principle #1：`codegraph_explore` 几乎永远是首选

一次调用返回：入口符号的源码 + 调用链 + 相关符号 + blast-radius 摘要。对于"X 是怎么工作的"、"追踪从 A 到 B 的链路"、"扫描一个区域"这三类问题，`codegraph_explore` 一次就够了。

**错误做法**（4 次工具调用）：
```
codegraph_search "Order" → 找到符号
codegraph_node "OrderService" → 看定义
codegraph_callers "OrderService" → 看谁调
codegraph_callees "OrderService" → 看调了谁
```

**正确做法**（1 次）：
```
codegraph_explore "订单创建流程从 Controller 到数据库"
```

### Principle #2：相信结果，不要 grep 验证

CodeGraph 返回的是 AST 级别的精确结果。用 `grep` 去"验证"它等于用文本匹配挑战 AST 解析——后者更准确。

### Principle #3：信任 staleness banner

文件编辑后索引有 debounce（默认 2 秒）。如果在此期间查询，MCP 响应会带 `⚠️` banner 告诉你哪个文件还未同步，并建议直接 `Read`。Agent 看到 banner 就读文件。

---

## Phase 1 · 项目扫描

```bash
# 确认索引状态
codegraph status
# → 索引文件数、符号数、边数、是否有待同步文件

# 看项目骨架
codegraph files --max-depth 2
# → 树形结构，含语言和符号数

# 按语言分组
codegraph files --format grouped

# 只看特定目录
codegraph files --path src/services
```

---

## Phase 2 · 业务分析的 4 种查询模式

### 模式 1：从业务概念出发

```
用户问："这个系统怎么处理退款的？"
→ codegraph_explore "refund flow from API to database"
→ 一次返回 RefundService 源码 + 调用链 + 谁调用了退款 + 退款状态机
→ agent 翻译为业务流程
```

### 模式 2：从 API 路由出发

```
→ codegraph_explore "POST /api/orders 的完整处理链路"
→ 返回 Controller → Service → Repository 的完整源码 + 调用图
```

CodeGraph 能识别 17 种框架的路由定义（Express, Flask, FastAPI, Django, Spring, Gin, Rails, Laravel, ASP.NET, NestJS, Axum, Rocket, Vapor, React Router, SvelteKit, Vue/Nuxt, Astro），自动生成 `route` 节点连接 URL 到 handler。

### 模式 3：从数据库表出发

```
analyze-schema.py 给出了 orders 表
→ codegraph_explore "orders table ORM model and all code that writes to it"
→ 找到所有读写 orders 的代码
→ 反向还原谁在什么时候改了什么字段
```

### 模式 4：从定时任务出发

```
→ codegraph_explore "scheduled tasks and cron jobs"
→ 找到所有 @Scheduled / cron / setInterval
→ 得到定时触发的业务流程
```

---

## 框架感知路由（17 种框架）

CodeGraph 自动识别 Web 框架的路由文件并生成 `route` 节点。对业务分析来说这极其重要——**查询一个 handler 的调用者就能看到绑定的 URL**。

| 框架 | 识别 |
|------|------|
| Express | `app.get(...)`, `router.post(...)` |
| Flask | `@app.route(...)` |
| FastAPI | `@app.get(...)`, `@router.post(...)` |
| Django | `path()`, `url()` in `urls.py` |
| Spring | `@GetMapping`, `@PostMapping` |
| NestJS | `@Controller` + `@Get/@Post`, GraphQL `@Resolver`, `@MessagePattern` |
| Gin / chi / gorilla / mux | `r.GET(...)`, `router.HandleFunc(...)` |
| Axum / actix / Rocket | `.route("/x", get(handler))` |
| Laravel | `Route::get()`, `Route::resource()` |
| Rails | `get '/x', to: 'users#index'` |
| ASP.NET | `[HttpGet("/x")]` |
| Vapor | `app.get("x", use: handler)` |
| React Router / SvelteKit | Route component nodes |
| Vue / Nuxt | `pages/` file-based routes |
| Astro | `src/pages/` file-based routes |

---

## 什么时候不用 CodeGraph

| 场景 | 为什么 | 用什么 |
|------|--------|------|
| 搜索**字符串字面量**（错误消息、UI 文案、日志文本） | CodeGraph 索引的是符号和结构，不是字面量 | `grep -r` |
| 搜索**注释** | 注释不在符号索引中 | `grep -r` |
| 搜索**配置文件**（YAML/JSON/TOML 内的业务参数） | CodeGraph 对这些文件的支持参差不齐 | `grep` 或 `Read` |
| 项目 < 20 个文件 | CodeGraph 的索引开销 > 直接读取 | Glob + Read |
| 刚写完文件立即查询 | 有 ~2 秒 debounce | 直接 `Read` 刚写的文件，或等 debounce 结束查看 staleness banner |

---

## 微服务多仓库

CodeGraph 是单仓库索引。多仓库场景：

```bash
# 每个仓库单独 init
cd order-service && codegraph init
cd inventory-service && codegraph init

# MCP 工具查询时传 projectPath
codegraph_explore "order flow" --projectPath ../order-service
```

同一个 session 里可以查询多个已索引的项目，没索引的路径会返回干净的降级提示。

---

## 配置（可选）

项目根目录的 `codegraph.json`：

```json
{
  "extensions": { ".dota_lua": "lua", ".tpl": "php" },
  "exclude": ["static/vendor/theme/"],
  "include": ["Tools/local/"]
}
```

- `extensions`：映射非标准后缀到已知语言
- `exclude`：额外排除目录（gitignore 之外的）
- `include`：强制纳入被 gitignore 排除的源码

---

## 卸载

```bash
codegraph uninstall          # 从所有 Agent 移除 + 卸载 CLI
codegraph uninstall --keep-cli  # 只移除 Agent 配置，保留 CLI
codegraph uninit              # 删项目的 .codegraph/（需要确认）
```

---

## 核心提醒

- **`codegraph_explore` 是第一公民**：几乎所有问题都用它，不要手动串 search+node+callers+callees
- **CodeGraph 是预建索引，不是搜索引擎**：返回 AST 级精确结果
- **相信 CodeGraph 的结果**：不要用 grep 验证
- **注意 staleness banner**：编辑后 2 秒内查询会有提醒，收到就 Read 文件
- **MCP 工具默认只有 `explore`**：需要其他工具时用 CLI 等价命令或设 `CODEGRAPH_MCP_TOOLS`
- **`codegraph affected`**：从 git diff 出发，追踪哪些测试文件受影响的变更影响——CI/PR 场景很实用
