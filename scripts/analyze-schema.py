#!/usr/bin/env python3
"""
analyze-schema.py — 将 db-introspect.py 输出的 schema.json 转化为业务分析摘要

输入：schema.json（db-introspect.py 的输出）
输出：
  entities.md      业务实体清单（表→业务概念映射）
  relationships.md 潜在实体关系分析（基于外键/命名约定）
  summary.json     结构化摘要（供 agent 后续分析使用）

纯只读：仅读取 JSON 输入文件，不连接数据库，不修改任何数据。
"""

import json
import sys
import os
from collections import defaultdict

# Windows: 强制 stdout/stderr 使用 UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def load_schema(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============================================================
# 表名 → 业务名 翻译
# ============================================================

WORD_MAP = {
    "user": "用户", "users": "用户",
    "order": "订单", "orders": "订单",
    "product": "商品", "products": "商品",
    "payment": "支付", "payments": "支付记录",
    "account": "账户", "accounts": "账户",
    "role": "角色", "roles": "角色",
    "permission": "权限", "permissions": "权限",
    "config": "配置", "configuration": "配置",
    "setting": "设置", "settings": "设置",
    "log": "日志", "logs": "日志",
    "audit": "审计", "audits": "审计记录",
    "file": "文件", "files": "文件",
    "message": "消息", "messages": "消息",
    "notification": "通知", "notifications": "通知",
    "task": "任务", "tasks": "任务",
    "job": "作业", "jobs": "作业",
    "project": "项目", "projects": "项目",
    "team": "团队", "teams": "团队",
    "company": "公司", "companies": "公司",
    "customer": "客户", "customers": "客户",
    "supplier": "供应商", "suppliers": "供应商",
    "warehouse": "仓库", "warehouses": "仓库",
    "inventory": "库存", "inventories": "库存",
    "invoice": "发票", "invoices": "发票",
    "refund": "退款", "refunds": "退款",
    "coupon": "优惠券", "coupons": "优惠券",
    "review": "评价", "reviews": "评价",
    "comment": "评论", "comments": "评论",
    "tag": "标签", "tags": "标签",
    "category": "分类", "categories": "分类",
    "session": "会话", "sessions": "会话",
    "token": "令牌", "tokens": "令牌",
    "workflow": "工作流", "workflows": "工作流",
    "report": "报表", "reports": "报表",
    "dashboard": "仪表盘", "dashboards": "仪表盘",
    "subscription": "订阅", "subscriptions": "订阅",
    "plan": "计划", "plans": "计划/方案",
    "template": "模板", "templates": "模板",
    "workspace": "工作区", "workspaces": "工作区",
    "connection": "连接", "connections": "连接",
    "datasource": "数据源", "datasources": "数据源",
    "query": "查询", "queries": "查询",
    "export": "导出", "exports": "导出记录",
    "import": "导入", "imports": "导入记录",
    "backup": "备份", "backups": "备份",
    "monitor": "监控", "monitors": "监控项",
    "alert": "告警", "alerts": "告警规则",
    "pipeline": "流水线", "pipelines": "流水线",
    "deploy": "部署", "deploys": "部署记录",
    "release": "发布", "releases": "发布版本",
    "artifact": "制品", "artifacts": "制品",
    "image": "镜像", "images": "镜像",
    "container": "容器", "containers": "容器",
    "cluster": "集群", "clusters": "集群",
    "node": "节点", "nodes": "节点",
    "network": "网络", "networks": "网络配置",
    "domain": "域名", "domains": "域名",
    "certificate": "证书", "certificates": "证书",
    "secret": "密钥", "secrets": "密钥",
    "event": "事件", "events": "事件",
    "metric": "指标", "metrics": "指标",
    "trace": "追踪", "traces": "链路追踪",
    "span": "跨度", "spans": "追踪跨度",
}

PREFIXES = ["t_", "tbl_", "tb_", "tab_"]


def infer_business_name(table_name: str, comment: str | None) -> str:
    """从表名和注释推测业务概念名称"""
    if comment and len(comment.strip()) > 2:
        return comment.strip()

    clean = table_name
    for p in PREFIXES:
        if clean.lower().startswith(p):
            clean = clean[len(p):]
            break

    # 尝试完整匹配
    if clean.lower() in WORD_MAP:
        return WORD_MAP[clean.lower()]

    # 尝试拆分匹配
    parts = clean.lower().replace("_", " ").split()
    for part in parts:
        if part in WORD_MAP:
            return WORD_MAP[part]

    # 无匹配，保留原名作为可读名称
    return clean.replace("_", " ").title()


TIMESTAMP_KEYWORDS = [
    "created_at", "updated_at", "deleted_at", "create_time",
    "update_time", "modify_time", "expire", "timestamp", "date", "time",
]

STATUS_KEYWORDS = ["status", "state", "stage", "phase", "step"]

AMOUNT_KEYWORDS = [
    "amount", "price", "total", "fee", "balance",
    "quantity", "count", "num", "volume", "weight",
    "cost", "revenue", "profit", "discount", "tax",
]


def infer_timestamp_hint(col_name: str) -> str:
    name = col_name.lower()
    hints = {
        "create": "记录创建时间",
        "update": "最后修改时间", "modify": "最后修改时间",
        "delete": "软删除时间",
        "expire": "过期时间",
        "login": "登录时间",
        "pay": "支付时间",
        "ship": "发货时间",
        "deliver": "签收时间",
        "complete": "完成时间",
        "start": "开始时间", "begin": "开始时间",
        "end": "结束时间", "finish": "结束时间",
    }
    for kw, hint in hints.items():
        if kw in name:
            return hint
    return "时间戳"


def infer_referenced_entity(col_name: str) -> str:
    """从 user_id → user → 用户"""
    base = col_name
    if base.endswith("_id"):
        base = base[:-3]
    if base.endswith("_"):
        base = base[:-1]
    return infer_business_name(base, None)


def guess_relationship_type(fk_col: str, from_table: str) -> str:
    if any(kw in fk_col.lower() for kw in ["parent", "owner", "creator", "created_by"]):
        return "belongs_to"
    return "references"


def any_keyword(col_name: str, keywords: list[str]) -> bool:
    return any(kw in col_name.lower() for kw in keywords)


def derive_state_machine(col_name: str, col_type: str) -> dict | None:
    """从 ENUM 字段自动推导状态机。
    输入: col_type = "enum('pending','paid','shipped','completed','cancelled')"
    输出: {initialState, normalPath, exceptionPaths, terminalStates} 或 None
    """
    import re

    # 匹配 ENUM / enum / set 类型
    match = re.search(
        r"(?:enum|ENUM|set|SET)\s*\(([^)]+)\)",
        col_type, re.IGNORECASE
    )
    if not match:
        return None

    raw = match.group(1)
    # 提取所有值
    values = re.findall(r"'([^']*)'", raw)
    if len(values) < 2:
        return None

    # 识别终态和异常值
    terminal_keywords = ["done", "complete", "finish", "success",
                         "cancel", "fail", "reject", "error",
                         "refunded", "closed", "archived", "expired", "deleted"]
    exception_keywords = ["cancel", "fail", "reject", "error", "refund", "dispute"]

    terminal_states = []
    exception_paths = []
    normal_states = []

    for i, v in enumerate(values):
        vl = v.lower()
        is_terminal = any(kw in vl for kw in terminal_keywords)
        is_exception = any(kw in vl for kw in exception_keywords)

        if is_terminal:
            terminal_states.append(v)
        if is_exception:
            # 找到异常入口：它前面的那个非异常状态
            for j in range(i - 1, -1, -1):
                prev_vl = values[j].lower()
                if not any(kw in prev_vl for kw in exception_keywords):
                    exception_paths.append({
                        "from": values[j],
                        "to": v,
                        "reason": _infer_exception_reason(col_name, v),
                    })
                    break
        else:
            normal_states.append(v)

    # 构建正常路径：排除异常值后的顺序
    normal_path = [v for v in values
                   if not any(kw in v.lower() for kw in exception_keywords)]

    return {
        "fieldName": col_name,
        "allValues": values,
        "initialState": values[0],
        "normalPath": normal_path,
        "exceptionPaths": exception_paths,
        "terminalStates": terminal_states,
        "valueCount": len(values),
    }


def _infer_exception_reason(field_name: str, value: str) -> str:
    """从状态值推测异常原因的中文描述"""
    vl = value.lower()
    if "cancel" in vl:
        return "取消"
    if "fail" in vl:
        return "失败"
    if "reject" in vl:
        return "驳回"
    if "refund" in vl:
        return "退款"
    if "error" in vl:
        return "异常"
    if "dispute" in vl:
        return "争议"
    return "异常终止"


# ============================================================
# 分析引擎
# ============================================================

def analyze_tables(databases: list[dict]) -> dict:
    """统一分析入口，兼容 MySQL/PG/Oracle/SQLServer 输出格式"""
    entities = []
    relationships = []
    total_columns = 0

    for db in databases:
        db_name = db["name"]
        # MySQL / Oracle / SQLServer: tables 直接在 database 下
        # PostgreSQL: database → schemas → tables
        table_collections = []

        if "tables" in db:
            table_collections.append((db_name, db["tables"]))
        if "schemas" in db:
            for schema in db["schemas"]:
                schema_name = schema.get("name", "public")
                table_collections.append((f"{db_name}.{schema_name}", schema.get("tables", [])))

        for scope_name, tables in table_collections:
            for table in tables:
                table_name = table["name"]
                comment = table.get("comment") or table.get("description")
                columns = table.get("columns", [])

                entity = {
                    "sourceTable": f"{scope_name}.{table_name}",
                    "suggestedBusinessName": infer_business_name(table_name, comment),
                    "comment": comment,
                    "rowCount": table.get("rowCount") or table.get("rowEstimate", 0),
                    "columnCount": len(columns),
                    "keyColumns": [],
                    "timestampColumns": [],
                    "statusColumns": [],
                    "amountColumns": [],
                    "referenceColumns": [],
                }

                for col in columns:
                    total_columns += 1
                    col_name = col["name"]
                    col_type = col.get("type", "")
                    col_comment = col.get("comment") or col.get("description")
                    col_nullable = col.get("nullable", True)
                    col_default = col.get("defaultValue")
                    is_pk = col.get("isPrimaryKey", False)

                    entry = {
                        "name": col_name,
                        "type": col_type,
                        "comment": col_comment,
                    }

                    if is_pk:
                        entity["keyColumns"].append(entry)

                    if any_keyword(col_name, TIMESTAMP_KEYWORDS):
                        entity["timestampColumns"].append({
                            **entry,
                            "businessHint": infer_timestamp_hint(col_name),
                        })

                    if any_keyword(col_name, STATUS_KEYWORDS):
                        sm = derive_state_machine(col_name, col_type)
                        if sm:
                            entity["statusColumns"].append({**entry, "derivedStateMachine": sm})
                        else:
                            entity["statusColumns"].append(entry)

                    if any_keyword(col_name, AMOUNT_KEYWORDS):
                        entity["amountColumns"].append(entry)

                    if col_name.endswith("_id") and not is_pk:
                        ref_entity = infer_referenced_entity(col_name)
                        entity["referenceColumns"].append({
                            **entry,
                            "referencedEntity": ref_entity,
                        })
                        relationships.append({
                            "from": f"{scope_name}.{table_name}",
                            "fromColumn": col_name,
                            "to": ref_entity,
                            "type": guess_relationship_type(col_name, table_name),
                        })

                entities.append(entity)

    return {
        "entityCount": len(entities),
        "totalColumns": total_columns,
        "entities": entities,
        "relationships": relationships,
    }


# ============================================================
# Markdown 生成
# ============================================================

def format_entities_md(analysis: dict, output_path: str):
    """生成 entities.md"""
    lines = [
        "# 数据库业务实体分析",
        f"> 实体数量：{analysis['entityCount']} 张表",
        f"> 字段总数：{analysis['totalColumns']}",
        "",
        "> 以下是从数据库 Schema 推测的业务实体。带注释的表名直接翻译，无注释的通过命名约定推断。",
        "> ⚠️ 推测结果需要人工验证——你比算法更了解你的业务。",
        "",
    ]

    # 按业务相关性排序
    def relevance(e: dict) -> int:
        score = 0
        if e.get("comment"): score += 5
        if e.get("timestampColumns"): score += 3
        if e.get("statusColumns"): score += 3
        if e.get("referenceColumns"): score += 2
        if e.get("amountColumns"): score += 2
        return -score

    sorted_entities = sorted(analysis["entities"], key=relevance)

    for entity in sorted_entities:
        lines.append(f"## {entity['suggestedBusinessName']}")
        lines.append(f"*来源表：`{entity['sourceTable']}`*")
        if entity.get("comment"):
            lines.append(f"\n**表注释**：{entity['comment']}")

        row_info = entity.get("rowCount", 0)
        if row_info:
            lines.append(f"**数据量**：约 {int(row_info):,} 行")
        lines.append("")

        # 主键
        if entity.get("keyColumns"):
            lines.append("**标识字段**：")
            for kc in entity["keyColumns"]:
                c = f" — {kc['comment']}" if kc.get("comment") else ""
                lines.append(f"- `{kc['name']}` ({kc['type']}){c}")
            lines.append("")

        # 状态字段
        if entity.get("statusColumns"):
            lines.append("**状态字段**（可能存在业务流程/状态机）：")
            for sc in entity["statusColumns"]:
                c = f" — {sc['comment']}" if sc.get("comment") else ""
                lines.append(f"- `{sc['name']}` ({sc['type']}){c}")
            lines.append("")

        # 业务指标
        if entity.get("amountColumns"):
            lines.append("**业务指标字段**：")
            for ac in entity["amountColumns"]:
                c = f" — {ac['comment']}" if ac.get("comment") else ""
                lines.append(f"- `{ac['name']}` ({ac['type']}){c}")
            lines.append("")

        # 时间锚点
        if entity.get("timestampColumns"):
            lines.append("**时间锚点**（反映实体生命周期节奏）：")
            for tc in entity["timestampColumns"]:
                hint = tc.get("businessHint", "")
                h = f" → {hint}" if hint else ""
                c = f" — {tc['comment']}" if tc.get("comment") else ""
                lines.append(f"- `{tc['name']}` ({tc['type']}){h}{c}")
            lines.append("")

        # 关联实体
        if entity.get("referenceColumns"):
            lines.append("**关联实体**（通过外键/命名约定推断）：")
            for rc in entity["referenceColumns"]:
                c = f" — {rc['comment']}" if rc.get("comment") else ""
                lines.append(f"- `{rc['name']}` → **{rc['referencedEntity']}**{c}")
            lines.append("")

        lines.append("---")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def format_relationships_md(analysis: dict, output_path: str):
    """生成 relationships.md"""
    lines = [
        "# 实体关系分析",
        f"> 从外键和命名约定推断的关系总数：{len(analysis['relationships'])}",
        "",
        "> 以下关系基于字段命名（`xxx_id`）和常见模式推断。",
        "> 实际关系请结合代码中的外键定义和业务逻辑验证。",
        "",
    ]

    # 去重
    seen = set()
    unique_rels = []
    for rel in analysis["relationships"]:
        key = f"{rel['from']}→{rel['to']}"
        if key not in seen:
            seen.add(key)
            unique_rels.append(rel)

    # 按来源分组
    by_source = defaultdict(list)
    for rel in unique_rels:
        by_source[rel["from"]].append(rel)

    for source, rels in sorted(by_source.items()):
        source_name = infer_business_name(source.rsplit(".", 1)[-1], None)
        lines.append(f"## {source_name} (`{source}`)")
        lines.append("")
        lines.append("| 关联字段 | 目标实体 | 关系类型 |")
        lines.append("|---------|---------|---------|")
        for rel in rels:
            lines.append(f"| `{rel['fromColumn']}` | {rel['to']} | {rel['type']} |")
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze-schema.py <schema.json> [output-dir]")
        print()
        print("Reads a schema.json file (from db-introspect.py) and generates:")
        print("  entities.md       — business entity analysis")
        print("  relationships.md  — entity relationship analysis")
        print("  summary.json      — structured summary for agent consumption")
        print()
        print("SAFETY: Read-only analysis. Only reads the input JSON file.")
        print("        No database connections, no write operations on data.")
        sys.exit(1)

    schema_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./db-analysis"

    if not os.path.exists(schema_path):
        print(f"Error: schema.json not found at {schema_path}")
        sys.exit(1)

    schema = load_schema(schema_path)
    databases = schema.get("databases", [])

    if not databases:
        # SQLite 格式：tables 直接在根下
        if "tables" in schema:
            databases = [{"name": "main", "tables": schema["tables"]}]
        else:
            print("Error: No databases or tables found in schema.json")
            sys.exit(1)

    analysis = analyze_tables(databases)
    analysis["dbType"] = schema.get("dbType", "unknown")

    os.makedirs(output_dir, exist_ok=True)

    # summary.json
    summary_path = os.path.join(output_dir, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    print(f"[analyze-schema] Summary: {summary_path}")

    # entities.md
    entities_path = os.path.join(output_dir, "entities.md")
    format_entities_md(analysis, entities_path)
    print(f"[analyze-schema] Entities: {entities_path}")

    # relationships.md
    rels_path = os.path.join(output_dir, "relationships.md")
    format_relationships_md(analysis, rels_path)
    print(f"[analyze-schema] Relationships: {rels_path}")

    print(f"\n[analyze-schema] Done.")
    print(f"  DB Type:     {analysis['dbType']}")
    print(f"  Entities:    {analysis['entityCount']} tables")
    print(f"  Columns:     {analysis['totalColumns']} total")
    print(f"  Relations:   {len(analysis['relationships'])} detected")
