# 微服务业务分析指南

当项目是微服务架构（多仓库/多模块/多数据库），业务分析需要一个额外的**服务发现与拓扑还原**阶段。本文档是 Phase 1 和 Phase 2 的微服务扩展。

## 核心理念：从硬证据枚举，不凭直觉猜测

微服务分析的关键是**枚举式**——从网关配置、MQ topic、API 契约等硬证据出发逐条穷举，而不是"读到哪算哪"。硬证据不会遗漏已上线的业务能力。

---

## Phase 1.5 · 服务发现（在 Phase 1 扫描后执行）

### 目标

找到系统的所有服务、每个服务的代码路径、数据库，画出服务拓扑。

### 步骤 1：定位所有服务

按优先级依次尝试以下来源：

| 来源 | 搜什么 | 得到什么 |
|------|--------|---------|
| **网关配置** | Nginx conf / Kong route / APISIX / Istio VirtualService / Traefik config | 所有对外 API 路由 → 路由到哪个服务 |
| **服务发现** | Consul / Nacos / Eureka / K8s Service / docker-compose.yml | 服务清单（名称、实例数、端口） |
| **CI/CD 配置** | GitHub Actions / GitLab CI / Jenkinsfile | 哪些目录被独立构建部署（每个 = 一个服务） |
| **仓库目录结构** | Monorepo 的 `services/` / `apps/` / `packages/` 目录 | 直接列出所有子项目 |
| **Proto/API 文档目录** | `proto/` / `api/` / `spec/` / OpenAPI 文件 | 服务的 API 契约文件位置 |

**搜索优先级**：网关 → K8s/Compose → CI 配置 → 目录结构。找到一个来源能确认的就不需要下一个。

### 步骤 2：为每个服务定位关键资产

对找到的每个服务，记录：

| 资产 | 怎么找 | 用途 |
|------|--------|------|
| **代码路径** | 从服务发现或目录结构确定 | Phase 2 代码分析入口 |
| **数据库** | 读服务配置文件/环境变量 | Phase 2.0 Schema 分析 |
| **API 契约** | OpenAPI yaml / proto 文件 / 路由定义文件 | 同步调用链还原 |
| **MQ 依赖** | 读配置文件中的 Kafka/RabbitMQ topic 列表 | 异步流程还原 |

### 产出：服务清单（写入 `business-knowledge.md`）

```markdown
## 服务清单

| 服务 | 代码路径 | 数据库 | API 契约 | MQ Topic |
|------|---------|--------|---------|---------|
| order-service | ./services/order | order_db (MySQL) | api/order.openapi.yaml | pub: order.created, order.cancelled / sub: payment.completed |
| inventory-service | ./services/inventory | inventory_db (PG) | proto/inventory.proto | sub: order.created |
| payment-service | ./services/payment | payment_db (MySQL) | api/payment.openapi.yaml | pub: payment.completed / sub: — |
| notification-service | ./services/notify | — (无状态) | — | sub: order.created, payment.completed |
| api-gateway | ./gateway | — | nginx.conf | — |
```

---

## Phase 2.0 · 业务入口枚举（从网关路由出发）

### 方法

读取网关配置，提取所有路由，每条路由翻译为一个业务操作。

Nginx 示例：
```nginx
location /api/orders { proxy_pass http://order-service; }
location /api/products { proxy_pass http://product-service; }
```

Kong/APISIX 示例（从 Admin API 或声明式配置读取）：
```yaml
routes:
  - name: create-order
    paths: ["/api/orders"]
    methods: ["POST"]
    service: order-service
```

### 翻译规则

| 路由模式 | HTTP 方法 | 业务操作 |
|---------|----------|---------|
| `/api/orders` | POST | 创建订单 |
| `/api/orders` | GET | 查询订单列表 |
| `/api/orders/{id}` | GET | 查看订单详情 |
| `/api/orders/{id}/cancel` | POST | 取消订单 |
| `/api/payments/pay` | POST | 发起支付 |

### 产出：业务能力清单

```markdown
## 业务能力清单（从 API 网关提取）

| 业务操作 | 路由 | 方法 | 目标服务 | 需要登录 | 触发后续流程 |
|---------|------|------|---------|---------|------------|
| 创建订单 | /api/orders | POST | order-service | 是 | order.created → 扣库存+发通知 |
| 查询订单 | /api/orders | GET | order-service | 是 | — |
| 发起支付 | /api/payments/pay | POST | payment-service | 是 | payment.completed → 改订单状态+创建运单 |
```

---

## Phase 2.2 · 同步调用链追踪

### 方法

对每个服务的 HTTP client / gRPC stub / RPC 调用进行搜索：

```bash
# 搜索 HTTP 调用
grep -rE "(fetch|axios|httpClient|RestTemplate|WebClient|requests\.(get|post))" --include="*.ts" --include="*.go" --include="*.java" --include="*.py"

# 搜索 gRPC 调用
grep -rE "(\.pb\.|_grpc|GrpcClient|@GrpcClient|channel\()" --include="*.go" --include="*.java" --include="*.ts"

# 搜索服务名引用
grep -rE "(order-service|inventory-service|payment-service)" --include="*.{ts,go,java,py,yaml,yml}"
```

### 翻译为调用链

从代码中还原：
- "OrderService.createOrder() 调用了 `POST inventory-service/api/inventory/reserve`"
- → 翻译：创建订单时，系统调用库存服务锁定库存

### 产出：服务调用拓扑

```
用户 → [Gateway] → order-service
                      ├── POST → inventory-service (锁定库存)
                      ├── POST → payment-service (发起支付)
                      └── PUB → order.created (异步通知)
```

---

## Phase 2.3 · 异步流程还原（从 MQ Topic）

### 方法

这是微服务分析**最有价值、也最容易遗漏**的环节。

#### 步骤 1：枚举所有 Topic

搜索配置文件和代码中的 topic 定义：

```bash
grep -rE "(topic|Topic|TOPIC)\s*[=:]\s*[\"']" --include="*.{yml,yaml,properties,env,ts,go,java}"

grep -rE "(KafkaTemplate|kafka\.send|publish|emit|produce)" --include="*.{ts,go,java,py}"

grep -rE "(@KafkaListener|@RabbitListener|subscribe|consume|onMessage)" --include="*.{ts,go,java,py}"
```

#### 步骤 2：画 Producer → Topic → Consumer 矩阵

```markdown
| Topic | Producer | Consumer | 业务含义 |
|-------|---------|----------|---------|
| order.created | order-service | inventory-service | 创建订单后锁定库存 |
| order.created | order-service | notification-service | 创建订单后发通知 |
| payment.completed | payment-service | order-service | 支付完成→改订单状态为"已支付" |
| payment.completed | payment-service | shipping-service | 支付完成→创建运单 |
| payment.failed | payment-service | order-service | 支付失败→改订单状态为"支付失败" |
| shipment.delivered | shipping-service | order-service | 签收→改订单状态为"已完成" |
| shipment.delivered | shipping-service | settlement-service | 签收→触发结算 |
```

#### 步骤 3：合并为完整业务链路

从一个触发入口出发，串联所有 topic 的 producer/consumer，得到端到端链路：

```
用户操作: POST /api/orders (创建订单)
  ├── [同步] order-service → inventory-service: 锁定库存
  ├── [同步] order-service → payment-service: 发起支付
  └── [异步] order.created →
      ├── inventory-service: 扣减库存 (从"锁定"变成"已扣")
      └── notification-service: 发送"下单成功"通知

用户操作: POST /api/payments/pay (完成支付)
  └── [异步] payment.completed →
      ├── order-service: 订单状态 pending→paid
      └── shipping-service: 创建运单

系统事件: shipment.delivered (快递签收回调)
  └── [异步] shipment.delivered →
      ├── order-service: 订单状态 shipped→completed
      └── settlement-service: 触发商家结算
```

---

## Phase 2.4 · 补充来源（定时任务 + Webhook + 回调）

这些是容易被忽略的流程入口：

### 定时任务

```bash
grep -rE "(@Scheduled|@Cron|cron|schedule|setInterval|crontab)" --include="*.{ts,go,java,py,yml,yaml}"
```

| 定时任务 | 触发周期 | 做什么 | 涉及服务 |
|---------|---------|--------|---------|
| 订单超时取消 | 每 5 分钟 | 扫描 pending 超过 30 分钟的订单 → 自动取消 + 释放库存 | order-service → inventory-service |
| 日报生成 | 每天 8:00 | 汇总昨日交易数据 → 生成报表邮件 | analytics-service → notification-service |

### Webhook / 回调

```bash
grep -rE "(webhook|callback|notify.url|callbackUrl|returnUrl)" --include="*.{ts,go,java,py,yml,yaml}"
```

| 回调 | 谁调谁 | 触发时机 | 做什么 |
|------|--------|---------|--------|
| 支付回调 | 支付宝→payment-service | 用户完成支付 | 验证签名→发布 payment.completed |
| 快递回调 | 快递公司→shipping-service | 快递签收 | 更新运单状态→发布 shipment.delivered |

---

## Phase 2.5 · 流程合并去重

将所有来源（网关 API + MQ 链路 + 定时任务 + Webhook）汇总为**全局业务流程清单**：

1. **合并**：同一个业务链路可能从不同来源被识别（如"下单流程"既从 POST /api/orders 看到，又从 order.created topic 看到）
2. **去重**：相同业务语义的流程合并为一条，保留多来源交叉验证
3. **命名**：用业务语言命名（不是"order.created topic 链路"，是"用户下单后库存扣减和通知流程"）
4. **关联**：标注哪些流程之间有触发关系（A 流程完成后触发 B 流程）

### 产出：全局业务流程清单

```markdown
## 全局业务流程清单

### 流程 1：用户下单（端到端）
- 触发：用户 POST /api/orders
- 同步：order-service → inventory-service（锁定库存）
- 异步：order.created → 扣减库存 + 发送通知
- 涉及服务：order-service, inventory-service, notification-service
- 涉及数据：orders 表, inventory 表

### 流程 2：订单支付
- 触发：用户 POST /api/payments/pay 或 支付宝回调
- 异步：payment.completed → 改订单状态 + 创建运单
- 异常分支：payment.failed → 改订单状态为"支付失败"
- 涉及服务：payment-service, order-service, shipping-service

### 流程 3：订单超时自动取消（定时任务）
- 触发：order-service 每 5 分钟定时扫描
- 条件：status=pending 且 created_at 超过 30 分钟
- 动作：order-service → inventory-service（释放库存）
- 涉及服务：order-service, inventory-service

### 流程 4：订单完成结算
- 触发：快递公司 webhook → shipping-service → shipment.delivered
- 异步：shipment.delivered → 改已完成 + 触发商家结算
- 涉及服务：shipping-service, order-service, settlement-service
```

---

## Phase 4 渲染：微服务场景的特殊图表

### 服务拓扑图

用 Mermaid flowchart 画服务拓扑（服务当节点，调用当箭头，标注协议）：

```
flowchart LR
  GW[API Gateway] --> OS[order-service]
  GW --> PS[product-service]
  OS -->|gRPC| IS[inventory-service]
  OS -->|HTTP| PMS[payment-service]
  OS -->|PUB| KF[[Kafka]]
  KF -->|SUB| IS
  KF -->|SUB| NS[notification-service]
  PMS -->|PUB| KF
  KF -->|SUB| OS
  KF -->|SUB| SS[shipping-service]
```

### 跨服务时序图

用 Mermaid sequenceDiagram 画跨服务调用链：

```
sequenceDiagram
  actor U as 用户
  participant GW as Gateway
  participant OS as order-service
  participant IS as inventory-service
  participant PMS as payment-service
  participant KF as Kafka
  participant NS as notification-service

  U->>GW: POST /api/orders
  GW->>OS: 创建订单
  OS->>IS: gRPC 锁定库存
  IS-->>OS: 锁定成功
  OS->>OS: 创建订单(pending)
  OS->>KF: PUB order.created
  OS-->>U: 返回订单ID
  KF->>IS: SUB 扣减库存
  KF->>NS: SUB 发送下单通知
```

### 异步流程泳道图

用 SVG 泳道图模板（见 `references/diagram-guide.md` 方案 B3）画 MQ 驱动的流程，每个服务一条泳道，topic 发布/订阅用箭头连接。
