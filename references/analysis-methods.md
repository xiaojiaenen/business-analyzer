# 业务分析方法 · 从代码到业务知识

本文档是 Phase 2 的详细操作手册——如何从代码仓库中系统地提取业务知识。

## 核心心态

**代码是化石，业务是生物。** 代码记录了"系统现在怎么做"，但你的任务是还原"业务是什么"。
关注 **what** 和 **why**，忽略 **how**。

当你读一段代码时，遵循这个翻译链：

```
代码结构 → 系统行为 → 用户动作 → 业务含义
```

例子：
```
代码: if (order.amount > 5000) { riskReview(order); }
系统行为: 金额超过 5000 的订单会触发风控审查
用户动作: 用户提交大额订单后会进入审核状态
业务含义: 为控制风险，大额交易需要人工复核。阈值设定为 5000 元。
```

---

## 2.1 业务实体识别

### 从哪里找

| 来源 | 搜索方式 | 提取什么 |
|------|---------|---------|
| 数据库 Schema | Grep `CREATE TABLE` / ORM model 文件 | 实体名、字段、注释 |
| API 类型定义 | Grep `interface`/`type`/`struct` (含 `Request`/`Response`/`DTO`) | 实体结构、必填字段 |
| 枚举/常量 | Grep `enum`/`const` (状态相关的) | 业务状态、类型分类 |
| 配置文件 | 数据源配置、业务开关 | 实体存储、业务边界 |

### codegraph 路径

如果项目已初始化 codegraph：
```bash
# 找 model/entity 相关符号
codegraph_search "model" --kind class
codegraph_search "entity" --kind class
# 批量看源码
codegraph_explore "Order User Product model entity schema"
```

### 无 codegraph 路径

```bash
# 找数据库模型
grep -rE "CREATE TABLE|@Entity|@Table|Schema|Model" --include="*.sql" --include="*.ts" --include="*.go" --include="*.java"
# 找类型定义
grep -rE "^type\s+\w+\s+struct|^export interface\s+\w+|^export type\s+\w+" --include="*.go" --include="*.ts"
```

### 产出格式

对每个实体回答：
1. **名称**：业务名（不是表名。`t_order` → "订单"）
2. **是什么**：一句话定义
3. **关键属性**：3-5 个最重要的业务属性（不是所有字段）
4. **生命周期**：从创建到结束经历了哪些状态
5. **关联实体**：和谁有关系？什么关系？

> 🔧 **全量深挖模式（模式 B）下**：第 3 项改为"全字段业务翻译"——每个字段都翻译为业务属性（字段名 → 业务含义 + 类型 + 是否必填 + 默认值 + 业务约束），不限于 3-5 个。第 4 项改为"完整状态机"——所有有 status 字段的实体都画状态机，不限核心实体。

### 核心业务概念识别（必做，借鉴 PocketFlow 核心抽象法）

实体清单容易陷入"罗列所有表"。**还要从中识别 5-10 个核心业务概念**——它们是整个业务故事的"主角"，新人理解了这几个概念就理解了系统 80%。

> 🔧 **全量深挖模式（模式 B）下**：核心概念仍要识别（用于关系网和基础性排序），但**非核心实体也要深挖**——每个实体都按上述产出格式完整分析，不能只列名字。核心概念用于"重点讲解顺序"，不是"只讲这些"的筛选器。

**识别标准**（满足 2 条以上即为核心概念）：
- 被 3+ 个业务流程引用
- 有完整状态机（状态 ≥ 3 个）
- 是业务收入的直接载体（订单、合同、账单）
- 是业务方日常对话的高频词（看 README/错误消息/注释出现频率）
- 删除它系统就不成立了

**核心概念关系图**（必产出）：

```
[核心概念 A] --[业务关系]--> [核心概念 B]

关系标签用业务动词，不用技术动词：
✅ "触发"、"依赖"、"约束"、"联动"、"生成"、"消费"
❌ "foreign key"、"join"、"reference"
```

Mermaid `flowchart LR` 画关系网，按**基础性排序**（底层概念在前，依赖它的在后）。

> 🔧 **全量深挖模式（模式 B）下**：关系图扩展为**全实体关系图**（所有实体都画），但核心概念用高亮节点区分（粗边框/不同颜色）。图可能较大，按业务域分块画。

**产出**：
- 5-10 个核心业务概念（名称 + 一句话定义 + 为什么是核心）
- 概念间关系网（from → to + 业务关系标签）
- 基础性排序（哪些是地基概念，哪些建在其上）

> 🔧 **全量深挖模式（模式 B）下**：产出扩展为"全部实体清单 + 核心概念高亮 + 全实体关系图（按域分块）"。

### 实体协作关系深化

"关联实体"太浅（只说"和谁有关"）。要挖出**业务协作关系**：

| 关系类型 | 说明 | 示例 | 怎么找 |
|---------|------|------|--------|
| **触发** | A 的变化启动 B 的流程 | 订单 paid → 触发发货 | grep 事件发布 + 状态变更 |
| **依赖** | A 的存在前提是 B 存在 | 订单依赖用户和商品 | 外键 + 业务校验 |
| **约束** | A 的状态/数量受 B 限制 | 库存不足约束下单 | 校验逻辑 if/check |
| **联动** | A 变化时 B 必须同步变 | 订单取消 → 优惠券退回 | 事务内的多表更新 |
| **枢纽** | 被多个流程依赖的实体 | 用户/商品是枢纽实体 | 统计被引用次数 |

**枢纽实体识别**（借鉴 Graphify god nodes）：统计每个实体被多少流程/其他实体引用，被引用最多的 2-3 个是枢纽实体——它们是系统的"业务脊柱"，文档要重点讲。

### 判断：实体识别够了没？

- 能不能用业务语言回答"这个系统管理哪些核心数据"？
- 能不能在不看代码的情况下画出实体-关系草图？
- **是否识别了 5-10 个核心业务概念（不是所有实体）**？
- **是否画了核心概念关系图（带业务关系标签）**？
- **是否识别了枢纽实体（业务脊柱）**？

---

## 2.2 业务流程提取

> 本节是业务分析的**核心深度区**。浅层的流程分析只是罗列"系统有哪些操作"，
> 深层的流程分析要回答"一单生意从头到尾怎么走"。
>
> 四步递进：**主线识别 → 子流程拆解 → 状态机提取 → 异常分支显式化**

### Step 0 · 端到端主线识别（必须先做）

**在追踪具体子流程之前，先识别贯穿全系统的端到端业务主线。**

主线是"业务故事"（如"从采购到付款"、"从订单到现金"），不是"技术链路"（如"OrderController→OrderService→OrderRepository"）。

📖 完整方法 → `references/end-to-end-mainline.md`

四种识别方法（可组合使用）：
1. **行业模板指纹匹配**：供应链(P2P/O2C)、金融(L2P/T2C)、SaaS(L2L/O2R) 有成熟模板
2. **外部入口反向追踪**：枚举所有 HTTP/MQ/cron/webhook 入口 → 追踪到出口
3. **主线实体生命周期串联**：选状态机最完整的实体 → 状态序列 = 主线骨架
4. **领域事件因果链**：枚举所有 `publish`/`dispatch` 调用 → 按业务因果排序

**产出**：1-3 条端到端主线，每条有：
- **业务名字**（不是"流程1"）
- **状态节点序列**（3-7 个节点）
- **匹配的行业模板**（如有）
- **子流程数**（3-7 个）

### Step 1 · 子流程拆解

每条主线拆解为 3-7 个子流程。每个子流程是一个"完整的业务段落"——有明确的开始、结束、状态变化。

**子流程的四要素**：

| 要素 | 说明 | 示例 |
|------|------|------|
| **触发条件** | 什么启动了这个子流程 | 用户点击下单 / 上一个子流程完成 / 定时触发 |
| **正常流程** | 步骤序列（含每步的参与者） | 用户选商品→系统校验库存→系统锁定库存→系统创建订单 |
| **状态变化** | 子流程结束时实体的状态迁移 | Order: [无] → pending |
| **衔接点** | 子流程的输出如何触发下一个子流程 | Order status=pending → 触发"支付"子流程 |

**追踪路径**（从前到后）：
```
用户入口（CLI命令/API端点/UI页面）
  → 输入校验（校验了什么 = 业务约束）
  → 核心逻辑（做了什么业务操作）
  → 副作用（发了通知？改了其他实体？发了事件？）
  → 输出/结果（用户得到了什么 + 实体状态变成什么）
  → 衔接（下一个子流程是什么？什么条件触发？）
```

### Step 2 · 状态机提取

每个有 `status`/`state` 字段的核心实体，提取完整状态机。状态机是业务流程最可靠的"事实骨架"——状态机比 API 路由更可靠。

📖 完整方法 → `references/state-machine-guide.md`

关键产出：
- 状态值清单（从 ENUM/常量提取）
- 状态迁移表（从状态 → 到状态 + 触发条件 + 守卫条件 + 触发者）
- Mermaid `stateDiagram-v2` 图
- 异常/取消/回滚的状态迁移

### Step 3 · 异常分支显式化（强制要求）

**每条子流程必须配套 3-5 条异常分支**，每条说明：

| 字段 | 说明 | 示例 |
|------|------|------|
| 触发条件 | 什么情况下走异常 | 支付超时 / 库存不足 / 用户取消 |
| 系统响应 | 系统做什么 | 释放锁定库存 / 订单状态→cancelled |
| 用户感知 | 用户看到什么 | "支付超时，订单已取消" |
| 是否可恢复 | 能否回到正常流程 | 重新下单 / 不可恢复 |

#### 异常分支覆盖率校验（防"凑够 3 条就停"）

**数量达标 ≠ 覆盖完整**。3-5 条只是下限，必须对照以下 4 个异常源逐个核对，**不能漏**：

| 异常源 | 搜索方式 | 翻译成异常分支 |
|--------|---------|--------------|
| ① `try/catch` 块 | Grep `catch\s*\(` | 每个 catch 块 = 一条异常分支（catch 的异常类型 = 触发条件） |
| ② 事务回滚 | Grep `rollback` `@Transactional` `abort` `compensate` | 每个回滚点 = 一条异常分支（回滚条件 = 触发条件） |
| ③ 补偿事务 | Grep `compensate` `undo` `cancel` `revert` `reverse` | 每个补偿动作 = 一条异常分支（Saga 模式必查） |
| ④ 错误响应 | Grep `throw new` `raise` `errorResponse` `BizException` `ErrorResponse` | 每个业务异常 = 一条异常分支（异常消息 = 用户感知） |

**强制校验流程**：
1. 用上面 4 路搜索该子流程涉及的代码段
2. 把每个 catch / rollback / compensate / throw 对应到一条异常分支
3. **未对应上的搜索结果** = 遗漏，必须补充为异常分支
4. 在 `business-knowledge.md` 该子流程的异常分支列表后加一行校验记录：
   ```
   > 异常分支覆盖率：catch 5 处 / rollback 2 处 / compensate 1 处 / throw 4 处 → 已识别 5 条异常分支，无遗漏。
   ```

**示例**（错误 vs 正确）：

❌ 错误（凑够 3 条就停）：
```
子流程：创建订单
异常分支：1. 库存不足  2. 用户取消  3. 支付超时
```
没核对代码里的 catch/rollback，可能漏了"地址变更异常""风控拦截""优惠券失效"等。

✅ 正确（4 路核对后）：
```
子流程：创建订单
异常分支：
  1. 库存不足（catch InsufficientStockException → 释放库存锁定 → 提示"库存不足"）
  2. 用户取消（POST /cancel → 订单状态→cancelled → 提示"已取消"）
  3. 支付超时（@Scheduled 定时检查 → 订单状态→timeout → 提示"超时已取消"）
  4. 风控拦截（catch RiskControlException → 订单状态→risk_blocked → 提示"风控审核中"）
  5. 优惠券失效（rollback 事务 → 提示"优惠券已失效，请重新选择"）
覆盖率：catch 4 处 / rollback 1 处 / compensate 0 处 / throw 4 处 → 已识别 5 条，无遗漏。
```

### 有 codegraph

```bash
# 从路由/API 符号开始追踪
codegraph_context "order creation flow"
codegraph_callers "createOrder"
codegraph_callees "createOrder" --depth 5
# 追踪状态变更
codegraph_search "setStatus" --kind function
codegraph_search "updateStatus" --kind function
```

### 无 codegraph

```bash
# 搜索路由定义
grep -rE "@(Get|Post|Put|Delete)Mapping|app\.(get|post)|router\.(get|post)|Route::" --include="*.ts" --include="*.go" --include="*.java"
# 搜索状态变更
grep -rE "setStatus|updateStatus|\.status\s*=" --include="*.ts" --include="*.go" --include="*.java" --include="*.py"
# 搜索事件发布（领域事件 = 流程节点）
grep -rE "publish|applicationEventPublisher|emit|dispatch" --include="*.ts" --include="*.go" --include="*.java" --include="*.py"
```

### 产出格式 · 端到端主线 + 子流程

```
📋 端到端主线：订单到现金 (O2C)
   匹配模板：O2C · 置信度高
   状态节点：下单→支付→发货→收货→开票→收款

  ┌─ 子流程 1：创建订单
  │   触发：用户选商品后点击下单
  │   正常：用户选商品→系统校验库存→系统锁定库存→系统创建订单(pending)
  │   状态：Order [无] → pending
  │   衔接：Order status=pending → 触发支付子流程
  │   异常：
  │     - 库存不足 → 拒绝下单，提示用户 → 不可恢复
  │     - 重复提交 → 幂等校验拦截 → 返回已有订单
  │
  ├─ 子流程 2：支付
  │   触发：订单进入 pending 状态
  │   正常：系统发起支付→用户完成支付→支付回调→订单状态→paid
  │   状态：Order pending → paid
  │   衔接：Order status=paid → 触发发货子流程
  │   异常：
  │     - 30分钟未支付 → 定时任务取消订单 → pending→cancelled
  │     - 支付失败 → 订单保持 pending → 用户可重试
  │
  ├─ 子流程 3：发货
  │   ...
  │
  └─ 子流程 N：收款
      ...

📋 端到端主线：采购到付款 (P2P)
   ...

📋 跨主线关系（深化为跨业务域协作，不能只写一句话）
   浅层：P2P 的"入库"→ O2C 的"可售库存"（上下游依赖）
   深化：跨域协作时序——哪些域按什么顺序联动完成一个业务目标

   示例（跨域协作时序）：
   采购域(P2P)         →  库存域(I2O)        →  销售域(O2C)
   采购入库                  增加可售库存           可下单
   (采购单 received)  →   (库存 available)  →  (订单 created)
```

**跨业务域协作**（借鉴 CodeWiki 跨模块交互）：
- 每条跨域协作要说明：哪个域做什么动作 → 触发哪个域做什么 → 联动结果
- 用 Mermaid `sequenceDiagram` 画跨域时序图（域作为参与者）
- 识别"跨域枢纽动作"——一个动作触发多个域联动的关键节点（如"订单 paid"同时触发库存占用+发货+积分）

### 事件风暴逆向提取（可选增强）

如果项目有大量事件发布（`publish`/`dispatch`/`emit`），用事件风暴方法增强流程分析：

1. **枚举所有领域事件**：grep 所有事件发布点
2. **按业务因果排序**（不是技术调用栈顺序）
3. **渲染事件时间线**：用 Mermaid `sequenceDiagram` 画跨角色时序图

```
OrderCreated → InventoryLocked → PaymentInitiated → PaymentSucceeded
→ OrderPaid → ShipmentCreated → OrderShipped → OrderDelivered → OrderClosed
```

每个事件 = 流程节点，事件之间的因果关系 = 流程主线。

### 判断：流程分析够了没？

- [ ] 识别了 1-3 条端到端主线（每条有业务名字）
- [ ] 每条主线拆解了 3-7 个子流程
- [ ] 每个子流程有四要素（触发条件 + 正常流程 + 状态变化 + 衔接点）
- [ ] 每个子流程有 3-5 条异常分支
- [ ] 核心实体有完整状态机图
- [ ] **跨主线关系已深化为跨业务域协作时序**（不是一句话）
- [ ] 多主线项目有跨域时序图（Mermaid `sequenceDiagram`）
- [ ] 能用业务语言向同事讲述"一单生意从头到尾怎么走"

---

## 2.3 业务规则挖掘

### 什么是业务规则

**不是**：密码长度 ≥ 8 位（那是技术校验）
**是**：VIP 用户免运费 / 同一商品每人限购 3 件 / 超过 5000 元需审批

**区分技巧**：如果这条规则改了，业务会受影响吗？会 → 业务规则。不会 → 技术规则。

### 从哪里找

**5 路全扫**（不能只扫后端校验——前端校验、数据库约束、业务常量、AOP 拦截器都藏着规则）：

| 来源类型 | 搜索关键词 | 提取什么 | 示例 |
|---------|-----------|---------|------|
| ① 后端校验 | `validate` `check` `verify` `ensure` `rule` `policy` `constraint` `limit` | 输入约束、业务判断 | `if(amount > 5000) requireApproval()` |
| ② 前端校验 | `yup` `zod` `ajv` `schema` `required` `min` `max` `pattern` `validator` | 表单约束（常反映业务边界） | `yup.number().max(100, '不能超过100件')` |
| ③ 数据库约束 | `CHECK` `UNIQUE` `NOT NULL` `FOREIGN KEY` `DEFAULT` （由 `analyze-schema.py` 抽取） | 数据完整性规则 | `CHECK(status IN ('active','closed'))` |
| ④ 业务常量 | `MAX_` `MIN_` `LIMIT_` `THRESHOLD` `RATE` `TIMEOUT_` `DAYS` `COUNT` | 业务参数阈值 | `MAX_REFUND_DAYS = 30` |
| ⑤ AOP/拦截器 | `@PreAuthorize` `@Roles` `@Valid` `@Interceptor` `@Aspect` `@Before` `middleware` `guard` | 权限/审计/限流等横切规则 | `@PreAuthorize("hasRole('ADMIN')")` |
| ⑥ 条件分支 | `if.*amount` `if.*status` `if.*role` `switch.*type` | 业务判断逻辑 | `if(user.isVIP) waiveShippingFee()` |
| ⑦ 错误消息 | `throw new` `raise` `error` `exception` （业务相关的） | 业务约束的反面 | `throw new BizException("库存不足")` |
| ⑧ 定时任务 | `cron` `@Scheduled` `schedule` `job` `task` | 时间驱动的规则 | `@Scheduled(cron="0 0 * * *")` 每日对账 |

### 有 codegraph

```bash
codegraph_search "validate" --kind function
codegraph_search "check" --kind function
codegraph_search "rule" --kind function
codegraph_search "policy" --kind function
```

### 无 codegraph

```bash
# 5 路全扫（漏任一路都可能丢规则）
grep -rE "(validate|check|verify|ensure|rule|policy|constraint|limit|threshold|MAX_|MIN_|LIMIT_|TIMEOUT_|DAYS)" --include="*.ts" --include="*.go" --include="*.java" --include="*.py"

# 前端校验（常被漏）
grep -rE "(yup|zod|ajv|schema|validator|\.required\(|\.min\(|\.max\(|\.pattern\()" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.jsx"

# AOP/拦截器（常被漏）
grep -rE "(@PreAuthorize|@Roles|@Valid|@Interceptor|@Aspect|@Before|@RequiresPermission|@RolesAllowed)" --include="*.java" --include="*.ts"

# 业务常量（常被漏）
grep -rE "(MAX_[A-Z]|MIN_[A-Z]|LIMIT_[A-Z]|THRESHOLD|TIMEOUT_)" --include="*.ts" --include="*.go" --include="*.java" --include="*.py"
```

### 数据库约束规则（由 analyze-schema.py 自动抽取）

`analyze-schema.py` 已抽取的字段级约束 → 翻译为业务规则：

| 数据库约束 | 业务规则 |
|-----------|---------|
| `NOT NULL` + 业务字段（非技术字段） | 该字段是业务必填项 |
| `UNIQUE` 约束 | 业务唯一性规则（如一个用户只能有一个主账户） |
| `CHECK` 约束 | 字段值域约束（如 status 只能是特定值） |
| `FOREIGN KEY` | 实体关系约束（如订单必须属于有效用户） |
| `DEFAULT` 业务值 | 默认业务状态（如新建订单默认 status='pending'） |

**注意**：当前 `analyze-schema.py` 只抽取了字段，未抽取表级约束。需检查 schema.json 中是否有 `constraints`/`checks`/`indexes` 字段，如有则一并翻译为业务规则。

### 产出格式

| 规则 ID | 触发条件 | 执行动作 | 业务原因 | 来源类型 | 置信度 |
|---------|---------|---------|---------|---------|--------|
| BR-001 | 订单金额 > 5000 | 触发风控人工审核 | 大额交易风险控制 | ① 后端校验 | `[代码明确]` |
| BR-002 | 用户当日提现次数 ≥ 3 | 拒绝本次提现 | 反洗钱合规要求 | ④ 业务常量 | `[代码明确]` |
| BR-003 | VIP 用户免运费 | 跳过运费计算 | VIP 权益 | ⑥ 条件分支 | `[推断]` |
| BR-004 | 同一商品每人限购 3 件 | 超出数量拒绝下单 | 防囤货 | ② 前端校验 + ① 后端校验 | `[代码明确]` |

**强制要求**：至少覆盖 3 种来源类型（不能只从①后端校验提取——前端校验、数据库约束、AOP 拦截器都是规则的藏身之处）。

---

## 2.4 用户角色与权限

### 从哪里找

| 来源 | 搜索方式 |
|------|---------|
| 枚举/常量 | `role` `permission` `UserType` `UserRole` |
| 中间件/拦截器 | `auth` `guard` `middleware` `hasRole` `canAccess` |
| 路由权限注解 | `@RolesAllowed` `@RequiresPermission` |
| 配置文件 | RBAC 配置、权限矩阵 |

### 产出格式

| 角色 | 一句话画像 | 核心能力 | 不能做的事 |
|------|-----------|---------|-----------|
| 普通用户 | 使用产品核心功能的消费者 | 浏览、下单、查看自己的数据 | 看别人的数据、修改系统配置 |
| 管理员 | 管理平台内容和用户的运营者 | 管理用户、查看全局数据、配置规则 | 修改系统底层代码 |

---

## 2.5 领域划分

### 什么时候需要划分

当实体超过 10 个、或业务流程超过 5 条时，需要把系统切分为子领域。每个子领域有自己的：
- 业务语言（同一词在不同领域意思可能不同）
- 核心实体集群
- 独立的业务规则

### 划分方法

按**业务能力**切割，不是按代码包切割：

```
✅ 好的切法:
- 交易域（下单、支付、退款）
- 商品域（商品管理、库存、价格）
- 用户域（注册、认证、会员）

❌ 差的切法:
- Controller 层
- Service 层
- Repository 层
（这是技术分层，不是业务划分）
```

---

## 2.6 业务能力分层与入口点枚举（借鉴 CodeWiki 分层分解 + ArchGuard 入口地图）

> "业务能力一览"一级平铺太浅。要分 **业务域 → 业务能力 → 业务操作** 三级，并从入口点全枚举确保不遗漏。

### 业务能力三级分层

```
业务域（2-5 个）          业务能力（每域 3-7 个）       业务操作（每能力 1-N 个）
─────────────            ──────────────               ──────────────
交易域                    订单管理                      创建订单 / 取消订单 / 查看订单
                         支付                          发起支付 / 退款 / 对账
                         售后                          申请退款 / 换货
商品域                    商品管理                      上架 / 下架 / 改价
                         库存                          锁定 / 释放 / 盘点
```

**分层方法**：
1. 顶层业务域来自 §2.5 领域划分
2. 每个域拆出 3-7 个业务能力（业务能力 = 一类相关操作）
3. 每个能力下列出具体业务操作（业务操作 = 用户/系统的一次完整动作）
4. **每个业务操作必须能对应到一个入口点**（见下方入口点枚举）

### 业务入口点全枚举（不只微服务才做，所有项目必做）

**借鉴 ArchGuard 的 API 地图**：每个入口点 = 一个业务操作。枚举所有入口，翻译成业务语言，确保业务能力清单不遗漏。

| 入口类型 | 搜索方式 | 翻译成业务操作 |
|---------|---------|--------------|
| HTTP API | `@(Get/Post)Mapping` `app.get/post` `router.` | POST /api/orders → 创建订单 |
| CLI 命令 | `argparse` `command` `@click` `cobra` | `sync-inventory` → 同步库存 |
| 消息消费者 | `@RabbitListener` `@KafkaHandler` `subscribe` | consume order.created → 处理订单创建事件 |
| 定时任务 | `@Scheduled` `cron` `celery beat` | 每日 0 点对账 → 日常对账任务 |
| Webhook | `webhook` `callback` `/hooks/` | payment.success callback → 处理支付成功 |
| 后台管理操作 | admin 路由 / 后台页面 | 后台改价 → 运营改价 |

**无 codegraph**：
```bash
# 全量入口扫描（不要只搜 API，定时任务和 MQ 常被遗漏）
grep -rE "@(Get|Post|Put|Delete)Mapping|app\.(get|post|put|delete)|router\.(get|post)|@(Scheduled|RabbitListener|KafkaHandler)|cron|webhook|callback" --include="*.ts" --include="*.go" --include="*.java" --include="*.py"
```

**产出**：
- 入口点全清单（入口类型 + 路径 + 翻译成的业务操作）
- 与业务能力三级分层对照（每个业务操作对应哪个入口）
- **遗漏检查**：业务能力树上的每个操作都有入口对应吗？有入口没对应到业务能力吗？（两者都要补）

### 判断：能力分层够了没？

- [ ] 识别了 2-5 个业务域（来自 §2.5）
- [ ] 每个域拆出 3-7 个业务能力
- [ ] 每个能力下列出具体业务操作
- [ ] **枚举了所有入口点**（API + CLI + MQ + 定时 + Webhook + 后台）
- [ ] 入口点与业务操作一一对照，无遗漏
- [ ] 能用业务能力树向新人讲清"这个系统能做哪些事"

---

## 2.7 模块作为业务证据（从代码结构读业务信号）

> 模块/目录结构是业务划分的"化石"。不输出技术架构图，但要把模块当**业务证据**来读，
> 系统性地从中提取业务信号——而不是跳着读、漏掉业务重心。

### 从模块读什么业务信号

| 模块信号 | 怎么读 | 业务含义 | 产出 |
|---------|--------|---------|------|
| **目录/包名** | 看顶层目录、包结构 | 目录名常=业务域（order/、payment/、inventory/） | 补充领域划分（§2.5） |
| **模块职责** | 看 Service/Controller 类名和方法名 | OrderService.createOrder → 订单管理能力 | 补充业务能力树（§2.6） |
| **模块复杂度** | 看文件数、代码行数、方法数 | 复杂度最高的 2-3 个模块=业务重心 | 标注核心业务域 |
| **模块间调用** | 看 import/依赖注入 | 跨模块调用=跨域协作线索 | 补充跨域协作时序（§2.2） |
| **模块注释** | 看文件头/类注释 | 注释常写明业务定位 | 补充业务定义（置信度[注释/文档]） |

### 判断业务重心（必做）

**不是所有模块同等重要**。用复杂度指标找业务重心：

```bash
# 统计每个目录的代码行数（找出最大的 2-3 个模块）
# Windows PowerShell
Get-ChildItem -Recurse -File -Include *.java,*.ts,*.go,*.py | Group-Object DirectoryName | ForEach-Object { [PSCustomObject]@{ Dir=$_.Name; Lines=(($_.Group | Get-Content | Measure-Object -Line).Lines) } } | Sort-Object Lines -Descending | Select-Object -First 10

# Linux/Mac
find . -type f \( -name "*.java" -o -name "*.ts" -o -name "*.go" -o -name "*.py" \) | xargs wc -l | sort -rn | head -20
```

**业务重心判断**：
- 代码量最大的 2-3 个模块 → 核心业务域（文档重点讲）
- 代码量极小的模块 → 辅助功能（文档一句话带过）
- 有大量状态变更逻辑的模块 → 核心流程所在（重点拆子流程）
- 被多个模块 import 的模块 → 枢纽模块/共享服务（可能是业务脊柱）

> 🔧 **全量深挖模式（模式 B）下**："一句话带过"的限制解除——辅助功能也要完整分析（产出格式 5 项全做），只是放在文档末尾或辅助章节，不占重点篇幅。核心/辅助的区分仅用于**排序**（核心在前），不用于**省略**。

### 模块 → 业务映射表（产出）

```
模块名            业务域      业务能力              复杂度    业务定位
order-service    交易域      订单管理              高        核心业务（重点讲）
payment-service  交易域      支付                  中        核心业务
inventory-service 商品域     库存管理              高        核心业务（重点讲）
user-service     用户域      用户管理              低        辅助功能
notification     -          通知                  低        辅助功能（一句话带过）
```

### 陷阱

| 陷阱 | 正确做法 |
|------|---------|
| 把模块名直接当业务域名（如 "svc-order" → 业务域 "svc-order"） | 翻译成业务语言 → "交易域" |
| 所有模块平均用力 | 按复杂度区分重心，核心模块详讲，辅助模块略过 |
| 输出模块依赖图/调用拓扑 | 不输出技术图，只提取业务协作线索 |
| 只看模块名不看内容 | 模块名只是入口，要读类/方法确认实际业务 |

### 判断：模块证据够了没？

- [ ] 看了顶层目录结构，翻译成业务域名称
- [ ] 用代码量/复杂度找出了 2-3 个业务重心模块
- [ ] 每个核心模块读了类/方法名，提取了业务能力
- [ ] 跨模块调用关系作为跨域协作线索记入了 §2.2
- [ ] 产出了模块→业务映射表

---

## 业务知识置信度标注（借鉴 Graphify EXTRACTED/INFERRED）

每条业务知识在 `business-knowledge.md` 里标注来源，帮读者区分"事实"和"推断"：

| 标注 | 含义 | 示例 |
|------|------|------|
| `[代码明确]` | 代码/数据库/注释里直接写明 | 订单状态 ENUM: pending/paid/shipped |
| `[注释/文档]` | 从代码注释或 README 推导 | "30 分钟未支付自动取消"（注释写明） |
| `[推断]` | 从代码逻辑推断，非直接声明 | 大额订单需风控（从 if 金额判断推断） |
| `[待确认]` | 不确定，需用户/业务方确认 | 退款是否走原路返回（代码不明确） |

**标注格式**（写在每条业务知识末尾）：
```
- 订单 30 分钟未支付自动取消 [代码明确]（定时任务 OrderTimeoutJob）
- VIP 用户免运费 [注释/文档]（README 提及，阈值未明确）[待确认]
```

**原则**：
- `[代码明确]` 的可信度最高，文档里可以直接引用
- `[推断]` 的要在文档里用"系统会……"而非"系统必然……"
- `[待确认]` 的必须在检查点向用户提问，**不编造业务逻辑**

---

## 常见陷阱

| 陷阱 | 为什么错 | 正确做法 |
|------|---------|---------|
| 用代码模块名代替业务概念 | 读者不知道什么是 "OrderService" | 翻译成"订单处理" |
| 列出所有字段而不是关键属性 | 读者被细节淹没 | 只列 3-5 个最重要的业务属性（**全量深挖模式 B 除外**——模式 B 列全字段业务翻译） |
| 描述技术实现而非业务流程 | "系统调用 validate() 然后 save()" 没有信息量 | "系统校验库存后创建订单" |
| 把技术规则当业务规则 | "密码需含特殊字符" 是技术安全规则，不是业务规则 | 问自己：业务方会关心这条规则吗？ |
| 忽略异常路径 | 只写正常流程，读者以为系统永远不会出错 | 每个流程标注关键异常分支 |
