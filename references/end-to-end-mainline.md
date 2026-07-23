# 端到端业务主线识别方法

> Phase 2.2 的第一步——在追踪具体子流程之前，先识别贯穿全系统的端到端业务主线。
> 端到端主线是"业务故事"，不是"技术链路"。它回答"这个业务从开始到结束经历了什么"。

## 为什么需要主线

没有主线的流程分析 = 孤立的步骤清单。读者看完知道"系统有哪些操作"，但不知道"一单生意从头到尾怎么走"。

**有主线的例子**（供应链）：
```
主线 1：采购到付款 (P2P)
  请购 → 采购下单 → 到货验收 → 入库 → 对账 → 付款
主线 2：订单到现金 (O2C)
  报价 → 下单 → 拣货 → 出库 → 发货 → 确认收货 → 开票 → 收款
```

**没主线的例子**（同样这些操作，平铺）：
```
流程 1：创建采购订单
流程 2：验收货物
流程 3：入库
流程 4：创建销售订单
流程 5：出库
流程 6：付款
...
```

读者无法理解"验收"和"入库"是采购主线的上下游，还是独立操作。

---

## 方法 1 · 行业模板指纹匹配

### 原理

很多业务领域有成熟的端到端流程模板。通过代码中的实体名、状态机节点、路由前缀做"指纹匹配"，套用行业模板骨架。

### 常见行业主线模板

#### 供应链 / 电商

| 主线代号 | 名称 | 关键实体 | 状态节点 | 路由指纹 |
|---------|------|---------|---------|---------|
| **P2P** | Procure-to-Purchase | Purchase, Supplier, Invoice, Payment | 请购→下单→到货→验收→入库→对账→付款 | `/purchase`, `/supplier`, `/invoice` |
| **O2C** | Order-to-Cash | Order, Shipment, Invoice, Payment | 下单→拣货→出库→发货→收货→开票→收款 | `/order`, `/shipment`, `/payment` |
| **MTO** | Make-to-Order | Order, BOM, Production, Quality | 下单→排产→领料→生产→质检→入库→发货 | `/production`, `/bom`, `/quality` |
| **MTS** | Make-to-Stock | Forecast, Production, Inventory | 预测→排产→生产→质检→入库→销售 | `/forecast`, `/inventory` |
| **R2R** | Return-to-Refund | Return, Inspection, Restock, Refund | 退货申请→质检→入库→退款 | `/return`, `/refund` |

#### 金融 / 支付

| 主线代号 | 名称 | 关键实体 | 状态节点 |
|---------|------|---------|---------|
| **L2P** | Loan-to-Pay | Loan, Disbursement, Repayment, Settlement | 申请→审批→放款→还款→结清 |
| **T2C** | Trade-to-Clear | Trade, Matching, Clearing, Settlement | 下单→撮合→成交→清算→交收 |
| **I2R** | Issue-to-Resolve | Ticket, Investigation, Resolution | 投诉→受理→调查→处理→回访 |

#### SaaS / 企业应用

| 主线代号 | 名称 | 关键实体 | 状态节点 |
|---------|------|---------|---------|
| **L2L** | Lead-to-Land | Lead, Opportunity, Contract, Onboarding | 线索→商机→签约→实施→上线 |
| **O2R** | Onboard-to-Renew | Account, Subscription, Usage, Renewal | 注册→开通→使用→续费/流失 |
| **R2F** | Request-to-Fulfill | Ticket, Approval, Fulfillment | 申请→审批→执行→验收 |

### 匹配步骤

1. **提取实体指纹**：从数据库表名/API 路由中提取所有名词
   ```bash
   # 从 API 路由提取
   grep -rE "@(Get|Post|Put|Delete)Mapping" --include="*.java" | grep -oE '/(\w+)' | sort -u
   # 从表名提取
   grep -rE "CREATE TABLE" --include="*.sql" | grep -oE 'table\s+(\w+)' 
   ```

2. **与模板指纹比对**：把提取的名词与上表的"关键实体"列交叉匹配
   - 命中 3+ 个关键实体 → 高置信度匹配该主线
   - 命中 1-2 个 → 可能是主线的子流程，标记为候选

3. **套用骨架**：匹配成功后，用模板的状态节点作为主线骨架，再用代码细节填充

4. **命名主线**：即使没有匹配到模板，也要给识别到的主线起一个**业务名字**
   - ✅ "从采购到付款" / "订单到现金" / "用户注册到首次下单"
   - ❌ "流程1" / "OrderFlow" / "创建订单到关闭订单"（太技术化）

### 输出格式

```markdown
## 端到端主线清单

### 主线 1：采购到付款 (P2P)  [匹配模板：P2P · 置信度高]
- **业务目标**：从需要采购物资开始，到完成付款为止
- **关键实体**：Purchase, Supplier, Invoice, Payment
- **状态节点**：请购→采购下单→到货验收→入库→对账→付款
- **子流程数**：6
```

---

## 方法 2 · 外部入口反向追踪法

### 原理

端到端主线一定从"系统外部触发"开始（用户操作/MQ消息/定时任务/Webhook），到"系统外部输出"结束（DB写入/MQ发送/API响应/通知）。枚举所有外部入口，反向追踪到出口，就是一条完整主线。

### 步骤

1. **枚举所有外部入口**
   ```
   HTTP 路由（@PostMapping 等）
   MQ consumer（@RabbitListener / @KafkaListener）
   定时任务（@Scheduled / cron）
   Webhook / 回调
   CLI 命令
   ```

2. **对每条入口反向追踪**
   ```
   入口：POST /api/orders（用户下单）
     → OrderService.create()
       → InventoryService.lock()（锁定库存）
       → PaymentService.initiate()（发起支付）
         → PaymentGateway.charge()（调用外部支付）
           → PaymentCallback（等待异步回调）
     → 出口：Order status=待支付 + 发送支付页面
   ```

3. **命名并归类**：把追踪到的链路命名为业务主线

### 追踪工具

```bash
# 有 codegraph
codegraph_callers "createOrder"
codegraph_callees "createOrder" --depth 5

# 无 codegraph
# 从 controller 追到 service 再到 repository/external
grep -rE "class.*Controller" --include="*.java"
grep -rE "class.*Service" --include="*.java"
```

---

## 方法 3 · 主线实体生命周期串联法

### 原理

选 1-2 个"主线实体"（贯穿整个业务的核心实体，如 Order、Loan、Application），它的状态机从"创建"到"终态"走过的所有状态迁移，对应的操作就是端到端主线。

### 步骤

1. **识别主线实体**
   - 被最多其他实体引用的实体（外键最多的表）
   - 有完整状态机的实体（status 字段 + 多个状态值）
   - 名字出现在最多 API 路由中的实体

2. **提取状态机**（详见 `state-machine-guide.md`）

3. **每个状态对应什么操作？**
   ```
   Order 状态机：created → paid → shipped → delivered → closed
     created  ← POST /orders（创建订单）
     paid     ← PaymentCallback（支付回调）
     shipped  ← POST /orders/{id}/ship（发货）
     delivered ← POST /orders/{id}/confirm（确认收货）
     closed   ← 定时任务/手动关闭
   ```

4. **串联成主线**
   ```
   主线：订单生命周期 (created→paid→shipped→delivered→closed)
   对应操作链：创建订单 → 支付 → 发货 → 收货 → 关闭
   ```

### 优势

- 状态机是业务事实（写在数据库 ENUM 里），比 API 路由更可靠
- 一个实体的状态机天然就是一条端到端主线
- 多个主线实体的状态机交叉点 = 跨主线关系

### 数据库连不上时的退化处理

状态机最可靠的源是数据库 ENUM。**如果数据库连不上**（见 `SKILL.md` §2.0），状态机只能从代码推断：

| 来源 | 置信度 | 提取方式 |
|------|--------|---------|
| 数据库 ENUM（最可靠） | `[代码明确]` | `analyze-schema.py` 自动提取 |
| 代码常量定义（次可靠） | `[代码明确]` | Grep `Status.*=` / `const.*Status` / `enum.*Status` |
| `setStatus`/`updateStatus` 调用 | `[推断]` | Grep 调用点，提取被赋值的状态值 |
| `if(status==)`/`switch(status)` 分支 | `[推断]` | Grep 分支判断，提取被比较的状态值 |

**退化时必做**：
1. 在 `business-knowledge.md` 状态机段开头加标注：
   ```
   > ⚠️ 本项目状态机源于代码推断（数据库未连接），可能不完整。
   > 已用 setStatus 调用 + if(status==) 分支 + 常量定义三路交叉验证，但可能漏掉：
   > - 仅在数据库 ENUM 中出现、代码从未引用的状态值
   > - 历史遗留的废弃状态
   > 建议连上数据库后用 `analyze-schema.py` 重新提取 ENUM 全集校准。
   ```
2. **三路交叉验证**：常量定义 ∪ setStatus 调用 ∪ if 分支 = 推断状态全集。任一路独有 = 标 `[待确认]`。
3. Phase 3 Checkpoint 1 显式问用户："状态机是从代码推断的，是否有遗漏的状态值？"

---

## 方法 4 · 领域事件因果链法

### 原理

系统中的 `publish`/`dispatch`/`emit`/`send` 调用 = 领域事件。把所有事件按业务时间序排列，事件之间的因果关系 = 端到端主线。

### 步骤

1. **枚举所有事件发布点**
   ```bash
   # Java
   grep -rE "publish|applicationEventPublisher|send\(|dispatch" --include="*.java"
   # Go
   grep -rE "publish|emit|send\(" --include="*.go"
   # Python
   grep -rE "publish|emit|send\(" --include="*.py"
   ```

2. **提取每个事件的语义**
   - 事件名 → 业务语义（`OrderCreated` → "订单已创建"）
   - 发布位置 → 触发条件（在 `OrderService.create()` 末尾发布 → "用户下单后"）

3. **按业务因果排序**（不是技术调用栈顺序）
   ```
   OrderCreated → InventoryLocked → PaymentInitiated → PaymentSucceeded
   → OrderPaid → ShipmentCreated → OrderShipped → OrderDelivered → OrderClosed
   ```

4. **渲染为时间线**：用 Mermaid `sequenceDiagram` 画跨角色时序图

---

## 跨主线关系

识别完多条主线后，必须说明它们之间怎么交叉。常见模式：

| 交叉模式 | 例子 | 说明 |
|---------|------|------|
| **上下游依赖** | 采购入库 → 可售库存 → 销售出库 | 主线 A 的输出是主线 B 的输入 |
| **并行协作** | 物流发货 + 通知发货 | 同一触发点启动两条并行主线 |
| **条件分支** | 验收通过→入库 / 验收不通过→退货 | 同一节点根据条件走不同主线 |
| **补偿回滚** | 支付成功→发货 / 支付失败→释放库存 | 主线异常触发补偿主线 |

### 输出格式

```markdown
## 跨主线关系

| 上游主线 | 下游主线 | 交叉点 | 关系类型 |
|---------|---------|--------|---------|
| P2P 采购到付款 | O2C 订单到现金 | 采购入库→可售库存 | 上下游依赖 |
| O2C 订单到现金 | R2R 退货到退款 | 退货触发退款 | 条件分支 |
```

---

## 完成标准

- [ ] 识别 1-3 条端到端主线（简单项目 1 条，复杂项目 3 条）
- [ ] 每条主线有**业务名字**（不是"流程1"）
- [ ] 每条主线有**状态节点序列**（3-7 个节点）
- [ ] 每条主线标注了**匹配的行业模板**（如有）或说明是自定义主线
- [ ] 说明了主线之间的**交叉关系**（如有多条主线）
- [ ] 每条主线至少拆解出 3 个子流程（详见 `analysis-methods.md` 2.2 节的子流程拆解）

---

## 与其它参考的关系

- 主线识别完成后 → 进入 `analysis-methods.md` 2.2 节做子流程拆解
- 主线实体的状态机提取 → `state-machine-guide.md`
- 主线渲染（Mermaid 时序图/流程图）→ `diagram-guide.md`
- 主线文档模板 → `document-templates.md` #3 核心业务流程（升级版）
