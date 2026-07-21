# 数据库分析 · 从 Schema 到业务知识

本文档是 Phase 2 中数据库相关分析的操作手册。当项目涉及数据库时，数据库 Schema 是业务分析最可靠的信息源——**代码会过时，但数据结构不会说谎**。

## 核心原则

**数据库 Schema 是业务的一面镜子。**
- 表 → 业务实体
- 字段 → 业务属性
- 外键 → 实体关系
- 状态字段 → 业务流程节点
- 时间戳 → 实体生命周期
- 金额/数量字段 → 业务指标

但 Schema 不会直接告诉你业务——需要**翻译**。`t_order` 不是 "t_order 表"，是"订单"。

---

## Phase 2.0 · 数据库 Schema 抽取

### 步骤 1：获取连接信息

首先从项目代码中找数据库连接方式：

```bash
# 自动检测（推荐）
python scripts/db-introspect.py --auto-detect <project-dir>
```

这个命令会扫描：
- `.env` / `.env.local` 文件
- `application.yml` / `application.properties`（Spring Boot）
- `database.json` / `config.js` / `config.ts`
- 代码中的 JDBC URL 和连接字符串
- Python `settings.py` / Django settings

它会列出所有检测到的连接信息，但**不自动连接**——让用户确认后再执行。

### 步骤 2：抽取 Schema（只读）

用户确认后，手动执行抽取：

```bash
# MySQL
python scripts/db-introspect.py --type mysql --host 192.168.1.1 -u root -p 123456 -d mydb

# PostgreSQL
python scripts/db-introspect.py --type postgres --host localhost -u postgres -d mydb

# 指定输出目录
python scripts/db-introspect.py --type mysql ... -o ./business-docs/db-analysis/
```

**安全保证**：
- 所有 SQL 查询都是 `information_schema` / `pg_catalog` 的 SELECT
- 绝不执行 INSERT / UPDATE / DELETE / DROP / CREATE / ALTER
- MySQL 连接后立即设置 `SET SESSION TRANSACTION READ ONLY`
- PostgreSQL 连接时传递 `default_transaction_read_only=on`
- 连接失败 → 放弃，不重试，不影响后续分析

### 步骤 3：分析 Schema → 业务实体

```bash
python scripts/analyze-schema.py ./business-docs/db-analysis/schema-mysql.json
```

这会生成：
- `entities.md` — 表→业务实体映射，含关键字段、状态字段、时间戳、关联分析
- `relationships.md` — 基于外键和命名约定推断的实体关系
- `summary.json` — 结构化摘要供 agent 后续分析使用

### 连不上怎么办

如果连接失败，脚本会输出清晰的错误信息。不要反复重试——直接跳过数据库分析，从代码和文档中提取业务知识即可。

依赖安装提示（按需）：
```bash
pip install pymysql          # MySQL / MariaDB / Doris
pip install psycopg2-binary  # PostgreSQL
pip install oracledb         # Oracle
pip install pymssql          # SQL Server
# 或
pip install pyodbc           # SQL Server (ODBC)
```

---

## 从 Schema 翻译到业务知识

### 翻译规则

| Schema 信号 | 业务含义 | 例子 |
|-------------|---------|------|
| 表名含 `user` / `account` | 用户/账户实体 | `t_user` → "系统用户" |
| 表名含 `order` / `trade` / `transaction` | 交易核心实体 | `orders` → "订单" |
| 表名含 `log` / `history` / `audit` | 审计/追溯记录 | `audit_log` → "操作审计日志" |
| 表名含 `config` / `setting` / `param` | 配置/参数 | `sys_config` → "系统配置" |
| 表名含 `rel_` / `map_` / 两个实体名用 `_` 连接 | 关联表（多对多） | `user_role_rel` → "用户-角色关联" |
| 字段名 `status` / `state` / `stage` | 状态机/业务流程节点 | `order_status` → "订单状态流转" |
| 字段名 `created_at` + `updated_at` | 生命周期标记 | 实体有完整生命周期 |
| 字段名 `deleted_at` / `is_deleted` | 软删除 | 数据不物理删除 |
| 字段名 `amount` / `price` / `total` | 金额/业务值 | 涉及财务/交易 |
| 字段名以 `_id` 结尾 | 外键关系 | `user_id` → "属于某个用户" |
| 字段名 `parent_id` | 层级/树形结构 | `parent_category_id` → "分类层级" |
| 字段名 `type` / `kind` / `category` | 类型分异 | 同一实体有多种业务类型 |
| `ENUM` 类型 | 有限状态集 | `ENUM('pending','paid','shipped','done')` → 订单状态机 |
| `DECIMAL(10,2)` | 金额（精确计算） | 涉及财务精度 |
| `TEXT` / `JSON` 字段 | 非结构化业务数据 | `extra_info` JSON → 扩展属性 |
| 表 COMMENT | 最直接的业务定义 | `COMMENT='用户订单表'` → 这就是业务实体名 |

### 分析矩阵

对每张表，问 5 个问题：

1. **这是什么业务实体？**（翻译表名和 COMMENT）
2. **它的生命周期是什么？**（看 `status` + 时间戳字段）
3. **它和谁有关？**（看 `_id` 结尾的字段）
4. **它承载什么业务指标？**（看金额/数量字段）
5. **有 ENUM 吗？**（ENUM 里的值 = 业务状态全集）

### 例子：从表到业务

```sql
CREATE TABLE `orders` (
  `id` bigint PRIMARY KEY AUTO_INCREMENT,
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `total_amount` decimal(10,2) NOT NULL COMMENT '订单总金额',
  `status` enum('pending','paid','shipped','completed','cancelled','refunding','refunded'),
  `created_at` datetime,
  `paid_at` datetime,
  `shipped_at` datetime,
  `completed_at` datetime
) COMMENT='订单表';
```

翻译成业务：

> **订单（Order）**
> - 定义：用户发起的购买请求，记录了用户选择商品后的完整交易过程
> - 生命周期：待支付 → 已支付 → 已发货 → 已完成（异常分支：取消、退款中、已退款）
> - 关键属性：总金额（`total_amount`）
> - 时间锚点：创建时间 → 支付时间 → 发货时间 → 完成时间（可计算各环节耗时）
> - 关系：属于某个用户（`user_id` → User）

### 挖 ENUM 里的业务流程

ENUM 字段是业务流程的"硬编码说明书"：

```sql
status ENUM('pending','paid','shipped','completed','cancelled','refunding','refunded')
```

这告诉我们：
- 正常流程：pending → paid → shipped → completed
- 异常分支 1：任意前段 → cancelled（取消）
- 异常分支 2：paid 之后 → refunding → refunded（退款流程）
- 业务约束：未支付不能发货（paid 在 shipped 之前）

**ENUM 值的顺序通常就是业务流程的顺序。**

---

## 数据库分析 vs 代码分析

| 数据库告诉你 | 代码告诉你 |
|-------------|-----------|
| 系统管理了哪些实体（表） | 系统怎么操作这些实体（Controller/Service） |
| 实体有哪些属性（字段） | 属性的校验规则（validate） |
| 实体之间的关系（外键） | 关系怎么建立和维护（事务逻辑） |
| 状态流转的可能路径（ENUM） | 状态转换的触发条件（if/switch） |
| 数据量级（TABLE_ROWS） | 性能瓶颈在哪 |

**最佳实践**：先看数据库（Phase 2.0），再用代码补充细节（Phase 2.1-2.5）。数据库给出的是"这个系统管理什么"，代码给出的是"怎么管理"。

---

## 危险模式（绝不执行）

以下所有语句在本 skill 中**永不出现**——如果你在分析时产生了这些想法，说明走偏了：

- ❌ `INSERT INTO` / `UPDATE` / `DELETE` / `DROP` / `TRUNCATE` / `ALTER` / `CREATE`
- ❌ 在数据库中执行测试查询验证假设
- ❌ 导出生产数据做分析样本
- ❌ 修改任何数据库配置

**唯一允许的 SQL**：
- ✅ `SELECT ... FROM INFORMATION_SCHEMA....`
- ✅ `SELECT ... FROM pg_catalog....`
- ✅ `SELECT ... FROM sys....`（SQL Server）
- ✅ `SELECT ... FROM ALL_TAB_...`（Oracle）
- ✅ `SET SESSION TRANSACTION READ ONLY`（连接后立即执行）
