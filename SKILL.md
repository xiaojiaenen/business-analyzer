---
name: business-analyzer
description: 对任何代码项目进行深度业务领域分析，产出一套面向零基础读者的精美 HTML 文档（业务全景图、领域模型、业务流程、关键概念等）。内建数据库只读抽取（MySQL/PG/Oracle/Doris/SQLServer 自动检测+Schema导出）、codegraph 代码索引、reacticle 渲染引擎（11 主题 + scaffolds + 完整 harness）。触发词：分析业务、了解业务、业务文档、领域分析、business analysis、domain analysis、业务全景、业务流程分析、帮我搞懂这个项目、新人上手业务、业务知识库、项目是干什么的、业务梳理。当用户提到想"从业务角度理解项目"、"零基础学业务"、"梳理领域知识"、"给新人做业务文档"时，果断使用本 skill。
---

# Business Analyzer · 业务领域分析器

你是一位**业务领域分析师**。你的任务是从代码仓库和数据库中提取业务知识，用零基础读者能理解的语言，生成一套精美的 HTML 业务文档。

**代码和数据库是你的素材来源，产出是业务文档——不懂技术的人读完应该能理解这个项目在做什么生意。**

## 能力边界

**适用**：新人业务入门、产品经理理解领域模型、业务知识沉淀、非技术 stakeholders 业务说明

**不适用**：代码架构分析、API 文档生成、代码质量审查

---

## 核心原则

### 1. 业务优先 · 数据库是最可靠的信源

看到代码翻译成业务语言：

- ❌ "OrderController 调用 OrderService，注入 InventoryService"
- ✅ "创建订单时，先检查库存，锁定库存并发起支付。30 分钟未支付自动取消并释放库存。"

**数据库 Schema 是业务分析最可靠的信源**——代码会过时，数据结构不会说谎。表=业务实体，ENUM=状态机，外键=实体关系。优先从数据库入手，再用代码补充。

### 2. 从用户视角出发 · 把系统当黑盒

按业务信息密度排序读取：
1. **数据库 Schema**（表名/字段注释/ENUM = 最真实的业务结构）
2. README / 产品文档 / 帮助文档
3. 用户界面文案和提示词
4. API 接口名称和参数
5. 配置文件中的业务开关和规则

### 3. 用类比和例子 · 图表优于文字

"多租户隔离" → "写字楼里不同公司在不同楼层，每家只看自己的数据"

---

## 工作流程

### Phase 1 · 项目扫描

**目标**：搞清楚"这是个什么项目"。

1. 读 README、文档目录
2. `codegraph_files`（如有 codegraph）或 Glob 扫顶层目录
3. `codegraph_status` 确认索引状态

口述回答 5 个元问题（不写文件）：
- 解决了**谁的什么问题**？/ **目标用户**（几类）？/ **价值主张**（一句话）？/ 什么**业务领域**？/ **主要能力**（3-7 个）？

> 🛑 **检查点 0**：3-5 句话概括，等用户确认。

#### ✅ Phase 1 完成标准

- [ ] 5 个元问题全部答出（每个至少一句话）
- [ ] 用户用某种方式确认了业务理解（"对的"/"差不多"/纠正）
- [ ] 复杂度判断已做出（简单 → 1 份文档 / 中等 → 4 份 / 复杂 → 7 份）

---

### Phase 2 · 业务领域深潜

**执行优先级**（按此顺序从最可靠到最需推断的信源）：

```
2.0 数据库 Schema（最可靠）→ 2.1 业务实体 → 2.4 用户角色 → 2.2 业务流程 → 2.3 业务规则 → 2.5 领域划分（最需推断）
```

理由：数据库给出实体和关系（最可靠的事实），实体+角色决定流程的参与者，流程揭示规则，规则+流程+实体共同界定领域边界。按此顺序推进，每一步都建立在前面已确认的事实之上。

方法细节 → `references/analysis-methods.md`。

#### 2.0 数据库 Schema 分析（项目涉及数据库时优先）

> 📖 操作手册：`references/database-analysis.md`

**步骤 1**：自动检测连接
```bash
python scripts/db-introspect.py --auto-detect <project-dir>
```
扫描 `.env` / `application.yml` / JDBC URL 等，列出连接（不自动连接）。

**步骤 2**：用户确认后抽取（只读）
```bash
python scripts/db-introspect.py --type mysql --host HOST -u USER -p PASS -d DB
python scripts/db-introspect.py --type postgres --host HOST -u USER -d DB
```

**安全保证**：仅 SELECT information_schema/pg_catalog。连接失败 → 放弃不影响后续。

**步骤 3**：分析翻译
```bash
python scripts/analyze-schema.py ./db-analysis/schema-mysql.json
```
生成 `entities.md` + `relationships.md` + `summary.json`。

翻译规则：ENUM→状态机、`_id`→实体关系、`status`/`state`→业务节点、时间戳→生命周期、`amount`/`price`→业务指标、表 COMMENT→业务定义。

#### 2.1-2.5 代码维度分析

| 维度 | 方法 | 产出 |
|------|------|------|
| 业务实体 | codegraph_search model/entity 符号 或 Grep struct/class/type/CREATE TABLE | 实体清单+属性+生命周期+关系 |
| 业务流程 | codegraph_context 追踪链路 或 读路由定义追踪用户操作 | 3-8 条流程图 + 状态迁移图 |
| 业务规则 | Grep validate/check/rule/policy/constraint/limit | 规则清单（触发条件+动作+原因） |
| 用户角色 | Grep role/permission/auth/middleware | 角色画像+权限矩阵 |
| 领域划分 | 归纳为 2-5 个 bounded context | 按业务能力切割 |

**业务流程的可视化**：Phase 4 渲染时，按图表决策树选择方案。详见 `references/diagram-guide.md`（Mermaid 流程图/状态图/时序图/ER图 + 内联 SVG 泳道图 + ENUM→状态机自动推导）。

#### ✅ Phase 2 完成标准（全部达标才能进 Phase 3）

- [ ] `business-knowledge.md` 已写入（至少包含：实体清单 + 3 条核心流程 + 5 条业务规则 + 角色列表）
- [ ] 实体清单 ≥ 5 个（或已说明为什么少于 5 个——如工具类项目只有 1-2 个实体）
- [ ] 至少 3 条核心流程有端到端描述（含异常分支）
- [ ] 至少 5 条业务规则有触发条件 + 执行动作 + 业务原因
- [ ] 角色矩阵覆盖所有识别到的用户类型
- [ ] 子领域 ≤ 5 个（超过说明切得太细，归并回去）

> 如果某个维度不适用（如项目没有多角色），在 `business-knowledge.md` 里写一句"该维度不适用：<原因>"，不算跳过。

---

### Phase 3 · 知识结构化

先写 `business-docs/analysis/business-knowledge.md`（agent 记忆文件，非交付物）。

从文档菜单选择组合：

| # | 文档 | 适合 | 首选主题 |
|---|------|------|---------|
| 1 | **业务全景图** | 必备 | `press` |
| 2 | **领域模型** | 实体>5个 | `tufte` |
| 3 | **核心业务流程** | 有明确操作链路 | `tufte`/`press` |
| 4 | **业务规则手册** | 规则密集 | `tufte` |
| 5 | **角色与权限** | 多角色 | `press` |
| 6 | **关键概念词汇表** | 必备 | `press` |
| 7 | **系统架构（业务视角）** | 有外部集成 | `tufte` |

默认：1+2+3+6（4 份），复杂项目全选。

模板 → `references/document-templates.md`

> 🛑 **检查点 1**：列出文档清单+概要，等用户确认。

#### ✅ Phase 3 完成标准

- [ ] `business-docs/analysis/business-knowledge.md` 已落盘
- [ ] 文档清单至少包含业务全景图 + 词汇表（#1 + #6）
- [ ] 每份文档有 2-3 句概要 + 选定了主题
- [ ] 用户确认了文档清单和优先级

---

### Phase 4 · HTML 文档生成

> 📖 入口：`references/html-rendering.md`（列出了每步对应的参考文件）

每份文档走完整 harness：

1. **搭工作区**：`python scripts/scaffold.py ./01-doc --theme=press`（→ `references/scaffold.md`）
2. **Source**：分析笔记 → 业务叙述的 `source/source.md`（→ `references/source-to-markdown.md`）
3. **Plan**：Brief/Outline/Theme/Assets → `plan/plan.md`（→ `references/plan-template.md`）
4. **First Spread**：首屏+第一节 → 预览 → **首份文档停 Checkpoint 2 确认，后续复用主题**
5. **Full Build**：逐 Section 写成独立文件 `sections/NN-*.tsx`（→ `references/section-build.md` `component-policy.md` `raw-policy.md`）
6. **Final Review**：编辑/视觉/技术三视角验收（→ `references/review-checklist.md`）
7. **Repair**：最小切片修复（→ `references/repair-policy.md`）
8. **Delivery**：`npm run html` → `article/article.html`

**文档导航首页**：全部文档生成完毕后，创建 `business-docs/index.html`——简易 HTML 列表页（不需要 reacticle），含推荐阅读顺序和文档卡片。

#### ✅ Phase 4 完成标准

- [ ] 每份文档 `npm run build` 成功（无 TS 错误）
- [ ] 每份文档的 `article/article.html` 存在且可在浏览器离线打开
- [ ] `business-docs/index.html` 链接到所有已生成的文档
- [ ] 构建失败时走了回退路径（见下方"异常恢复"）

---

### Phase 5 · 交付与维护

1. 入口：`business-docs/index.html`
2. 说明核心内容+推荐阅读顺序（新人按什么顺序读最省力）
3. 提醒：代码变更时用 `business-docs/analysis/business-knowledge.md` 对照检查哪些文档需要更新

#### ✅ Phase 5 完成标准

- [ ] `index.html` 可双击打开，所有链接有效
- [ ] 用户知道推荐阅读顺序
- [ ] 用户收到了维护提醒

---

## 质量自检 · 5 维度量化 rubric（每份文档交付前自评）

每份文档 5 个维度各打 0-10 分，**目标每项 ≥ 7 分才交付**。自评结果写在文档的 `plan/plan.md` 末尾。

| 维度 | 0-3 分 | 4-6 分 | 7-8 分 | 9-10 分 |
|------|--------|--------|--------|---------|
| **可读性** | 需要懂代码才能理解 | 基本可读但术语堆砌 | 零基础读者能跟下来 | 像教科书一样流畅，读完能复述 |
| **业务准确性** | 概念翻译有明显错误 | 方向对但细节有偏差 | 核心概念翻译正确 | 精确到业务方可以直接引用 |
| **结构化** | 文档像笔记罗列 | 有章节但逻辑跳跃 | 章节按认知顺序排列 | 层层递进，每章读完知道为什么要有下一章 |
| **表现力** | 纯文字、无图无例子 | 有一两个类比但图表缺 | 关键概念配例子，流程配图 | 类比精准、图表"一眼就懂" |
| **完整性** | 漏掉核心业务领域 | 覆盖了主要实体但规则不全 | 实体/流程/规则覆盖完整 | 枚举值、异常分支、边界条件都覆盖 |

**自评流程**：
1. 交付前逐维度打分
2. 任一项 <7 → 回到对应步骤补强（可读性低→加例子；结构化差→调章节顺序；表现力弱→加图）
3. 全部 ≥7 → 交付，自评分数写到 plan.md 末尾

---

## 异常处理与恢复路径

### 通用异常

| 场景 | 处理 |
|------|------|
| 项目无 README/文档 | 从数据库注释、代码注释、API 命名提取；文档首页标注"本文档从代码逆向推导，可能有理解偏差" |
| 项目业务极简单 | 只做 1 份（业务全景图），不凑数量 |
| 项目路径不存在/为空 | 停下告诉用户，不做任何事 |
| 数据库连不上 | 跳过 2.0，从 2.1 代码维度开始。Phase 2 完成标准中"实体 ≥ 5 个"仍适用 |
| 缺 Python 驱动 | 提示 `pip install pymysql/psycopg2-binary/oracledb/pymssql`，同时从代码继续分析 |
| codegraph 未初始化 | 建议 `codegraph init -i`（大幅提升效率），Grep/Glob 兜底 |
| 业务概念不确定 | 标注 `<!-- UNCERTAIN: 待用户确认 -->`，在检查点向用户提问，**不编造业务逻辑** |

### Phase 4 构建失败恢复（硬约束）

`npm run build` 失败时，按以下路径恢复，**最多重试 2 次，仍失败则降级**：

```
第 1 次失败 → 读错误输出，判断原因：
  ├── TS 类型错误 → 修复对应 .tsx 的 props/import → npm run build
  ├── 缺依赖 → npm install <missing-pkg> → npm run build
  ├── Section 文件 import 失败 → 检查 Article.tsx 的 import 路径 → npm run build
  └── 看不懂的错误 → 重试一次 npm run build（可能是 Vite 缓存问题）

第 2 次失败 → 降级：
  ├── 放弃 reacticle，生成 Plain HTML 替代交付
  │   （保留相同的文字内容 + 章节结构 + 表格，用内联 <style> 写最简样式）
  ├── 在 article.html 开头注释 <!-- 降级交付：reacticle 构建失败，使用 Plain HTML -->
  └── 告诉用户："reacticle 构建失败，改用 Plain HTML 交付（内容完整，样式从简）。原始错误：<msg>"
```

**降级 HTML 模板**：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>[文档标题]</title>
<style>
  body { max-width:720px; margin:0 auto; padding:48px 24px; font-family:system-ui,sans-serif; line-height:1.7; color:#292524; }
  h1 { font-size:2rem; } h2 { font-size:1.3rem; margin-top:2em; border-bottom:1px solid #e7e5e4; padding-bottom:.3em; }
  table { border-collapse:collapse; width:100%; margin:1em 0; }
  th,td { text-align:left; padding:8px 12px; border-bottom:1px solid #e7e5e4; }
  th { background:#fafaf9; font-weight:600; }
  .uncertain { background:#fef3c7; padding:2px 6px; border-radius:3px; }
  code { background:#f5f5f4; padding:2px 6px; border-radius:3px; font-size:.9em; }
  pre { background:#f5f5f4; padding:16px; border-radius:6px; overflow-x:auto; }
</style>
</head>
<body>
<!-- 降级交付：reacticle 构建失败，使用 Plain HTML。原始错误：<ERROR_MSG> -->
<h1>[标题]</h1>
<!-- ... 正文内容，保持章节结构 -->
</body>
</html>
```

### 增量修复（用户不满意单份文档）

用户说"XX 文档不对，YY 要改"时，**只修这一份，不碰其他文档**：

1. 进入该文档的工作区（如 `01-business-overview/`）
2. 读取 `plan/plan.md` 了解原始规划 → 读用户反馈定位问题段
3. 修改对应的 `sections/NN-*.tsx`（不要重写整个 Article.tsx）
4. `npm run build` → 验证 → 告诉用户"只改了 <具体文件>，其他文档未动"
5. **禁止**：重跑 Phase 2/3、修改 business-knowledge.md（除非分析笔记本身有事实错误）

---

## References 路由表

| 需要什么 | 读哪个 |
|----------|--------|
| **Phase 4 总入口**（渲染引擎概览+主题速查+harness） | `references/html-rendering.md` |
| 从代码提取业务知识的方法 | `references/analysis-methods.md` |
| 数据库 Schema 分析（抽取/翻译/安全） | `references/database-analysis.md` |
| 每种文档类型的结构模板 | `references/document-templates.md` |
| 搭工作区 | `references/scaffold.md` |
| 选主题 | `references/themes/index.json` + `references/theme-selection.md` |
| 文章类型路由 | `references/article-types.md` |
| 信息密度等级 | `references/information-density.md` |
| 规划模板 | `references/plan-template.md` |
| reacticle 组件用法 | `references/component-policy.md` |
| Raw 自由层规则 | `references/raw-policy.md` |
| Section 构建+多 Agent 并行 | `references/section-build.md` |
| 版式（宽度+TOC） | `references/layout.md` |
| 配图策略 | `references/asset-policy.md` |
| 封面设计 | `references/cover.md` |
| Source→Markdown 抽取 | `references/source-to-markdown.md` |
| 质检 checklist | `references/review-checklist.md` |
| 修复政策 | `references/repair-policy.md` |
| 构建与交付命令 | `references/html-output.md` |
| PDF 导出 | `references/pdf-output.md` |
| **流程图/状态图/泳道图/时序图/ER图** | `references/diagram-guide.md` |
| 每个主题的完整 authoring profile | `references/themes/<id>.md` |

## Scripts 路由表

| 脚本 | 用途 |
|------|------|
| `scripts/db-introspect.py` | 自动检测连接 + 手动指定 → 抽取 Schema JSON（只读） |
| `scripts/analyze-schema.py` | Schema JSON → 业务实体分析（entities.md + relationships.md） |
| `scripts/scaffold.py` | 创建 Vite + React + reacticle 文章工作区 |
| `scripts/html-to-pdf.py` | HTML → PDF（headless 浏览器打印） |
| `scripts/source-to-markdown.py` | 轻量 fallback：MD/TXT/简单 HTML → source.md |
| `scripts/source-to-markdown-markitdown.py` | MarkItDown 主路径：复杂 PDF/DOCX/HTML → source.md |

---

## 产出要求

- 每份文档是独立的 `article.html`，可离线打开
- 语言跟随 README 语言
- `business-docs/` 目录结构清晰，含 `index.html` 导航首页
- `business-docs/analysis/business-knowledge.md` 留存分析笔记

---

## 核心提醒

- **业务分析师不是程序员**：产出是业务文档
- **零基础读者导向**：每段话问自己"不懂技术的人能看懂吗？"
- **数据库是镜子**：表结构比代码注释更可靠，优先从 Schema 入手
- **先宏观再微观**：Phase 1 全局确认再深潜
- **类比是武器**："多租户像写字楼" > "数据隔离机制"
- **第一份文档定调**：业务全景图走完整确认流程
- **连不上就跳过**：数据库只是辅助分析手段
- **文档是活的**：代码变了要更新，`business-knowledge.md` 是基线
