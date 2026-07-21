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

### 判断：实体识别够了没？

- 能不能用业务语言回答"这个系统管理哪些核心数据"？
- 能不能在不看代码的情况下画出实体-关系草图？

---

## 2.2 业务流程提取

### 方法：追踪"完整用户故事"

选 3-5 个最核心的用户场景，端到端追踪。

**场景来源**：
1. README 的功能列表
2. API 路由的顶层分组（如 `/order/`, `/user/`, `/payment/`）
3. 前端路由/页面结构
4. 测试用例中的场景描述

**追踪路径**（从前到后）：
```
用户入口（CLI命令/API端点/UI页面）
  → 输入校验（校验了什么 = 业务约束）
  → 核心逻辑（做了什么业务操作）
  → 副作用（发了通知？改了其他实体？）
  → 输出/结果（用户得到了什么）
```

### 有 codegraph

```bash
# 从路由/API 符号开始追踪
codegraph_context "order creation flow"
codegraph_callers "createOrder"
codegraph_callees "createOrder"
```

### 无 codegraph

```bash
# 搜索路由定义
grep -rE "@(Get|Post|Put|Delete)Mapping|app\.(get|post)|router\.(get|post)|Route::" --include="*.ts" --include="*.go" --include="*.java"
```

### 产出格式 · 业务流程图

用 ASCII 流程图 + 文字说明：

```
📋 业务流程：用户下单

用户                   系统                    外部
 |                      |                       |
 |-- 选择商品 --------->|                       |
 |                      |-- 校验库存 ---------->|
 |                      |<-- 库存充足 ----------|
 |<-- 确认订单 ---------|                       |
 |-- 提交订单 --------->|                       |
 |                      |-- 锁定库存            |
 |                      |-- 创建订单(待支付)    |
 |                      |-- 发起支付 ---------->| 支付网关
 |<-- 支付页面 ---------|                       |
 |-- 完成支付 --------->|                       | (异步回调)
 |                      |<-- 支付成功 ----------|
 |                      |-- 订单状态→已支付     |
 |                      |-- 发送通知            |
 |<-- 订单确认 ---------|                       |
```

每步补充：
- 如果某步失败会发生什么（异常分支）
- 关键业务规则的触发点

---

## 2.3 业务规则挖掘

### 什么是业务规则

**不是**：密码长度 ≥ 8 位（那是技术校验）
**是**：VIP 用户免运费 / 同一商品每人限购 3 件 / 超过 5000 元需审批

**区分技巧**：如果这条规则改了，业务会受影响吗？会 → 业务规则。不会 → 技术规则。

### 从哪里找

| 来源 | 搜索关键词 | 提取什么 |
|------|-----------|---------|
| 校验逻辑 | `validate` `check` `verify` `ensure` | 输入约束 |
| 条件分支 | `if.*amount` `if.*status` `if.*role` `switch.*type` | 业务判断 |
| 配置常量 | `MAX_` `MIN_` `LIMIT` `THRESHOLD` `RATE` | 业务参数 |
| 错误消息 | `error` `exception` `throw new` (业务相关的) | 业务约束的反面 |
| 定时任务 | `cron` `schedule` `job` `task` | 时间驱动的规则 |

### 有 codegraph

```bash
codegraph_search "validate" --kind function
codegraph_search "check" --kind function
```

### 无 codegraph

```bash
grep -rE "(validate|check|verify|ensure|rule|policy|constraint|limit|threshold|MAX_|MIN_)" --include="*.ts" --include="*.go" --include="*.java" --include="*.py"
```

### 产出格式

| 规则 ID | 触发条件 | 执行动作 | 业务原因 |
|---------|---------|---------|---------|
| BR-001 | 订单金额 > 5000 | 触发风控人工审核 | 大额交易风险控制 |
| BR-002 | 用户当日提现次数 ≥ 3 | 拒绝本次提现 | 反洗钱合规要求 |

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

## 常见陷阱

| 陷阱 | 为什么错 | 正确做法 |
|------|---------|---------|
| 用代码模块名代替业务概念 | 读者不知道什么是 "OrderService" | 翻译成"订单处理" |
| 列出所有字段而不是关键属性 | 读者被细节淹没 | 只列 3-5 个最重要的业务属性 |
| 描述技术实现而非业务流程 | "系统调用 validate() 然后 save()" 没有信息量 | "系统校验库存后创建订单" |
| 把技术规则当业务规则 | "密码需含特殊字符" 是技术安全规则，不是业务规则 | 问自己：业务方会关心这条规则吗？ |
| 忽略异常路径 | 只写正常流程，读者以为系统永远不会出错 | 每个流程标注关键异常分支 |
