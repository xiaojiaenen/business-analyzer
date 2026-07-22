# CodeGraph 使用指南

CodeGraph 是 tree-sitter 驱动的代码知识图谱，将项目中的每个符号、文件、调用关系预先索引到 SQLite。本 skill 在 Phase 1、Phase 2 中大量使用 CodeGraph 进行业务分析。本文档是 CodeGraph 在 business-analyzer 场景下的最佳实践。

> CodeGraph 仓库：https://github.com/colbymchenry/codegraph  
> 初始化：`codegraph init -i`（在项目根目录执行，约 30 秒-2 分钟，视项目大小）

---

## 工具速查

| 工具 | 一句话 | 本 skill 主要用在哪 |
|------|--------|-------------------|
| `codegraph_status` | 索引状态（健康？多大？） | Phase 1 — 确认索引可用 |
| `codegraph_files` | 文件树，比 Glob 快 100 倍 | Phase 1 — 了解项目结构 |
| `codegraph_search` | 按名称搜符号 | Phase 2 — 找特定实体/函数 |
| `codegraph_context` | **最常用** — 搜索+节点+调用者+被调用者 合一 | Phase 2 — 理解业务概念 |
| `codegraph_explore` | 批量查看多个符号的源码 | Phase 2 — 扫一批相关实体 |
| `codegraph_node` | 单个符号的详情（位置+签名+源码） | Phase 2 — 深入一个关键符号 |
| `codegraph_callers` | 谁调用了这个符号 | Phase 2.2 — 追踪调用链上游 |
| `codegraph_callees` | 这个符号调用了谁 | Phase 2.2 — 追踪调用链下游 |
| `codegraph_impact` | 改了这符号会影响什么 | Phase 2.5 — 理解模块边界 |

---

## 初始化

```bash
# 在项目根目录执行
codegraph init -i
```

**什么时候建议初始化**：
- 项目文件 > 50 个 → 强烈建议（Grep 效率开始下降）
- 项目文件 > 200 个 → 几乎必须（Grep 遍历已经太慢）
- 微服务架构 → 每个服务单独 init（在不同目录分别执行）

**什么时候不强制**：
- 项目 < 20 个文件 → Grep/Glob 够用
- 用户明确说不要 → 尊重

---

## Phase 1 · 项目扫描

### 判断项目结构

```bash
# 确认索引状态
codegraph_status
# → 输出: 文件数、符号数、边数、最后索引时间

# 查看顶层目录（了解项目骨架）
codegraph_files --maxDepth 2
# → 树形结构，每个文件标注语言和符号数

# 按语言分组查看
codegraph_files --format grouped
# → "TypeScript: 120 files / Go: 45 files / Rust: 30 files"
```

### 定位业务相关目录

```bash
# 只查看特定目录
codegraph_files --path src/services
codegraph_files --path apps
# → 快速了解哪些目录是业务代码（vs 工具库/测试/文档）
```

---

## Phase 2 · 业务分析（CodeGraph 最密集使用的阶段）

### Principle #1：用 `codegraph_context`，不要串行搜索

**错误做法**（3 次工具调用）：
```
codegraph_search "Order" → 找到 OrderService, OrderController
codegraph_node "OrderService" → 看签名
codegraph_callers "OrderService" → 看谁调它
```

**正确做法**（1 次工具调用）：
```
codegraph_context "订单创建流程"
```
一次返回：OrderService 定义 + createOrder 源码 + 调用者列表 + 被调用列表 + 相关符号。

### 寻找业务实体（Phase 2.1）

```bash
# 搜索 model/entity 相关符号
codegraph_search "model" --kind class
codegraph_search "entity" --kind class
codegraph_search "schema" --kind type

# 批量查看实体源码（一次看多个，不要逐个 node）
codegraph_explore "Order User Product Payment Inventory"
# → 按文件分组返回所有源码，带调用关系图

# 深入单个复杂实体
codegraph_node "Order" --includeCode true
# → 返回 Order 类的完整定义、所有字段、方法签名
```

### 反向还原业务流程（Phase 2.2）

```bash
# 从 API 路由出发追踪一条链路
codegraph_context "create order flow from api to database"
# → 返回路由→Controller→Service→Repository 的完整路径

# 想了解调用链的下游
codegraph_callees "OrderService.createOrder"
# → createOrder 内部调了哪些函数（库存检查？支付？通知？）

# 想了解调用链的上游
codegraph_callers "InventoryService.reserveStock"
# → 哪些地方调用了库存锁定（只有 OrderService？还是还有管理后台？）
```

### 分析影响范围（Phase 2.5 领域划分）

```bash
# 改了订单状态会炸到哪些模块
codegraph_impact "Order.status" --depth 2
# → 第一层: 谁直接读了 order.status
# → 第二层: 这些读的人又被谁依赖
# → 用这个判断"订单"相关的领域边界在哪
```

---

## 业务分析专用查询模式

### 模式 1：从业务概念出发

```
用户问："这个系统怎么处理退款的？"
→ codegraph_context "refund flow" 
→ 返回 RefundService、退款状态机、谁调用了退款、退款调用了谁
→ agent 翻译为业务流程
```

### 模式 2：从 API 路由出发

```
用户没问具体问题，要做全面分析
→ codegraph_search "Router" --kind function
→ 找到所有路由定义
→ 逐条 codegraph_context "POST /api/orders 的完整处理链路"
```

### 模式 3：从数据库表出发

```
analyze-schema.py 给出了 orders 表
→ codegraph_search "orders" --kind type
→ codegraph_context "orders 表对应的 ORM model"
→ 找到所有读写 orders 表的代码
→ 反向还原谁在什么时候改了 order.status
```

### 模式 4：从定时任务出发

```
codegraph_search "@Scheduled" --kind function
codegraph_search "cron" --kind function
→ 找到所有定时任务
→ 逐个 codegraph_context
→ 得到定时触发的业务流程
```

---

## 灰色地带：什么时候不用 CodeGraph

| 场景 | 为什么不用 | 用什么 |
|------|-----------|--------|
| 搜索**字符串内容**（错误消息、日志文本、UI 文案） | CodeGraph 索引的是符号和结构，不是字面量 | `grep -r "支付失败" --include="*.ts"` |
| 搜索**注释** | 注释不在索引中 | `grep -r "TODO\|FIXME\|HACK"` |
| 搜索**配置文件**（YAML/JSON/TOML） | CodeGraph 支持有限 | `grep` 或直接 `Read` |
| 项目文件 < 20 个 | 启动 CodeGraph 的开销比直接读更大 | Glob + Read |
| 刚改了文件立即查询 | 索引有 ~500ms 延迟 | 等半秒，或直接用 Read 看刚改的文件 |

---

## 微服务场景

CodeGraph 是**单仓库**索引——如果微服务是 monorepo（一个仓库包含所有服务），一个 `codegraph init -i` 即可。如果是多仓库：

```
# 每个仓库单独 init
cd order-service && codegraph init -i
cd inventory-service && codegraph init -i
# 查询时用 --projectPath 切换
codegraph_context "order flow" --projectPath ../order-service
```

---

## 性能提示

- `codegraph_context` 通常是最优选择——一次调用完成 3-4 次其他调用的工作
- `codegraph_explore` 用于批量查看（5-15 个符号），比逐个 `codegraph_node` 省 3-5 倍 token
- `codegraph_files` 比 `ls`/`tree`/`Glob` 快得多，而且带了语言和符号数元数据
- 如果 CodeGraph 返回"not initialized"，问用户一句要不要 `codegraph init -i`，不要静默跳过

---

## 核心提醒

- **CodeGraph 是预建索引，不是搜索引擎**：返回的是 AST 级别的精确结果，不是模糊匹配
- **相信 CodeGraph 的结果**：不要用 `grep` 去验证它——grep 是文本匹配，CodeGraph 是 AST 解析，后者更准确
- **一次 `codegraph_context` > 四次单独调用**：不要手动串联 search + node + callers + callees
- **指数延迟 ~500ms**：写完文件后等半秒再查
