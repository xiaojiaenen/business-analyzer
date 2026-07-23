# Business Analyzer · 业务领域分析器

> 对任何代码项目进行深度业务领域分析，产出一套面向零基础读者的精美 HTML 业务文档。
> **代码和数据库是素材，产出是业务文档——不懂技术的人读完应该能理解这个项目在做什么生意。**

---

## 介绍

`business-analyzer` 是一个通用的 AI Agent Skill，遵循标准 skill 协议（YAML frontmatter + 指令文件 + 脚本 + 模板），**可在任何支持 skill 的 AI 客户端中运行**——Claude Code、Trae、Cursor、Windsurf 等。它把代码仓库和数据库作为输入，自动梳理业务知识，最终生成一套**离线可打开、可分享的单文件 HTML 业务文档**。

它解决一个长期痛点：**新人 / 产品经理 / 非技术 stakeholders 想搞懂一个项目在做什么生意，但代码读不懂、README 太技术、设计文档过时**。这个 skill 让 AI 扮演业务领域分析师，从数据库 Schema、API 路由、代码注释中提取业务实体、流程、规则、角色，翻译成零基础读者能理解的语言，配上 Mermaid 图表和精心设计的版式，输出像精装书一样的 HTML 文档。

**适用场景**

- 新人业务入门：3 天缩短到 3 小时
- 产品经理理解领域模型：不用追着开发问
- 业务知识沉淀：把"老员工脑子里的"变成可分享的资产
- 跨部门业务说明：给老板 / 合作方看的非技术版本

**不适用**

- 代码架构分析（这是技术文档不是业务文档）
- API 文档生成（用 Swagger / OpenAPI 工具）
- 代码质量审查（用 lint / SonarQube）

---

## 特点

### 1. 业务优先，不是代码翻译

看到 `OrderController 调用 OrderService，注入 InventoryService`，会翻译成：

> 创建订单时，先检查库存，锁定库存并发起支付。30 分钟未支付自动取消并释放库存。

**数据库 Schema 是最可靠的信源**——代码会过时，数据结构不会说谎。表 = 业务实体，ENUM = 状态机，外键 = 实体关系。优先从数据库入手，再用代码补充。

### 2. 四步递进业务梳理（不是浅层罗列）

- **端到端主线识别**：找出"订单到现金 O2C""采购到付款 P2P"这种有业务名字的主线，不是"流程1/流程2"
- **子流程拆解**：每条主线拆 3-7 个子流程，含触发条件 / 正常流程 / 状态变化 / 衔接点四要素
- **状态机提取**：ENUM → 状态值，`setStatus` → 迁移表，配 Mermaid `stateDiagram-v2` 图
- **异常分支显式化**：每子流程配 3-5 条异常分支（触发条件 + 系统响应 + 用户感知 + 是否可恢复）

### 3. 11 主题精装书渲染

集成 [reacticle](https://www.npmjs.com/package/reacticle) 渲染引擎，11 个主题各具人格，每个文档页面可独立选主题：

| 主题 | 气质 | 适合 |
|------|------|------|
| `tufte` | 数据克制、低装饰 | 数据报告、长文 |
| `press` | 出版叙事、温暖 | 业务全景、随笔 |
| `shannon` | 暗底工程现场 | 事后复盘、系统设计 |
| `vignelli` | 瑞士国际主义 | 规格文档、参考手册 |
| `knuth` | 学术预印本 | 论文、研究 |
| `freddie` | 暖黄友善 | 教程、产品介绍 |
| `andy` | 静谧温柔 | 入门引导、生活向 |
| `bodoni` | 报刊高反差 | 长篇报道、宣言 |
| `bayer` | 包豪斯三原色 | 品牌宣言、教程 |
| `fuller` | 蓝图工程制图 | 系统规格、RFC |
| `sottsass` | 孟菲斯 80s 撞色 | 文化、设计写作 |

### 4. Mermaid 图表跟随主题

Mermaid 默认 neutral 主题用 sans-serif + 粗方框 + 灰箭头，跟 reacticle 衬线美学冲突。本 skill 预置 `mermaid-overrides.css`，用 `--ra-*` CSS 变量 + `!important` 覆盖 Mermaid 11 的 inline style，让流程图 / 状态机 / 时序图 / ER 图自动跟随文章主题——切主题时图表自动变色，不需要手动调。

### 5. 离线单文件交付

构建产物 `dist/index.html` 是自包含单文件（CSS + JS 全内联），**断网可打开、可分享、可邮件附件**。用 `vite-plugin-singlefile` 把所有资源内联，包括 Mermaid 渲染引擎。

### 6. 单项目 SPA 架构

所有文档页面共享一个 Vite + React 项目，通过 HashRouter 路由切换。`file://` 协议下也能用（锚点跳转已修复）。文档多了不分裂成多个项目，一份 `dist/index.html` 装下所有文档。

### 7. 数据库只读抽取

支持 MySQL / PostgreSQL / Oracle / Doris / SQL Server 自动检测 + Schema 抽取，**仅 SELECT information_schema / pg_catalog，不写不删**。连接失败不影响后续分析，从代码维度继续。

### 8. 增量更新

代码变了不用重跑全流程。读 `git diff <上次交付>..HEAD`，按"变更类型 → 业务维度 → 文档映射表"只更新受影响的 Section 文件，纯技术重构（不改业务逻辑）→ 不更新任何文档。

### 9. PDF 导出

两种方式：
- **页面点击导出**（推荐，离线可用）：首页「导出 PDF」按钮 → 跳转 `/print-all` 预览页 → 自动弹浏览器打印对话框 → 另存为 PDF
- **命令行导出**：`python scripts/html-to-pdf.py --route print-all`，用本机 Chromium / Chrome / Edge headless 打印

### 10. 多维度质量自检

每份文档交付前按 5 维度量化打分（可读性 / 业务准确性 / 结构化 / 表现力 / 完整性），任一项 < 7 分返工补强。

---

## 安装

本 skill 遵循标准 skill 协议，**任何支持 skill 的 AI 客户端都能用**。仓库地址：

```
https://github.com/xiaojiaenen/business-analyzer
```

### 方式一 · npx skills 安装（推荐）

通过 [skills.sh](https://skills.sh/) 的 CLI 直接从 GitHub 安装（Claude Code 等客户端原生支持）：

```bash
npx skills add xiaojiaenen/business-analyzer
```

首次运行会自动克隆仓库到客户端的 skill 目录并完成注册。后续更新：

```bash
npx skills update business-analyzer
```

也可以用 [OpenSkills](https://github.com/anthropics/skills) CLI：

```bash
npx openskills install xiaojiaenen/business-analyzer
```

安装后，在对话里说"分析这个项目的业务""帮我搞懂这个项目"等触发词，skill 会自动激活。

### 方式二 · 克隆到客户端的 skill 目录

如果客户端不支持 `npx skills`，或你想手动控制安装位置，直接 `git clone` 进对应目录：

```bash
# Claude Code（Linux / macOS）
git clone https://github.com/xiaojiaenen/business-analyzer.git ~/.claude/skills/business-analyzer

# Claude Code（Windows PowerShell）
git clone https://github.com/xiaojiaenen/business-analyzer.git "$env:USERPROFILE\.claude\skills\business-analyzer"

# Trae（Linux / macOS）
git clone https://github.com/xiaojiaenen/business-analyzer.git ~/.trae-cn/skills/business-analyzer

# Trae（Windows PowerShell）
git clone https://github.com/xiaojiaenen/business-analyzer.git "$env:USERPROFILE\.trae-cn\skills\business-analyzer"
```

### 方式三 · 克隆到任意位置再软链

如果想让多个客户端共享同一份 skill、或集中管理 + `git pull` 更新，可以克隆到任意位置再软链：

```bash
# 1. 克隆到你的 skill 仓库集中目录
git clone https://github.com/xiaojiaenen/business-analyzer.git ~/skills/business-analyzer

# 2. 软链到对应客户端的 skill 目录
# Claude Code（Linux / macOS）
ln -s ~/skills/business-analyzer ~/.claude/skills/business-analyzer

# Claude Code（Windows PowerShell，管理员）
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.claude\skills\business-analyzer" -Target "$HOME\skills\business-analyzer"

# Trae（Linux / macOS）
ln -s ~/skills/business-analyzer ~/.trae-cn/skills/business-analyzer

# Trae（Windows PowerShell，管理员）
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.trae-cn\skills\business-analyzer" -Target "$HOME\skills\business-analyzer"
```

软链方式的好处：以后 `cd ~/skills/business-analyzer && git pull` 就能更新，所有客户端同步生效。

### 方式四 · Cursor / Windsurf / 其他客户端

这些客户端的 skill 加载机制各不相同，参考各自文档：
- **Cursor**：在 `.cursorrules` 或项目设置里指定 skill 路径，或放在 `~/.cursor/skills/`（如支持）
- **Windsurf**：参考其 skill / rules 配置文档
- **其他**：把本仓库根目录的绝对路径填进客户端的 skill 配置项即可

### 后续更新

无论哪种方式，更新到最新版只需：

```bash
cd <你的 business-analyzer 目录>
git pull
```

> 注：`assets/scaffold-template/` 下的 `node_modules/` 和 `dist/` 是验证时生成的，不在 git 里，不影响使用。scaffold 时会自动 `npm install`。

### 前置环境

Skill 本身不需要安装依赖（它是给 AI 读的指令集 + 脚本 + 模板）。但**运行时**（scaffold 文档项目、连数据库、导出 PDF）需要：

| 工具 | 用途 | 检测命令 |
|------|------|---------|
| **Node.js ≥ 18** + npm | scaffold 文档项目 + 构建 | `node --version && npm --version` |
| **Python ≥ 3.10** | 跑脚本（数据库抽取 / PDF 导出） | `python --version` 或 `python3 --version` |
| [CodeGraph](https://github.com/colbymchenry/codegraph)（可选） | 代码知识图谱，提升分析效率 89% | `codegraph --version` |
| Chromium / Chrome / Edge（可选） | PDF 导出 headless 打印 | 系统通常自带 |

**Python 驱动**（按用到的数据库装）：

```bash
pip install pymysql            # MySQL / Doris
pip install psycopg2-binary    # PostgreSQL
pip install oracledb           # Oracle
pip install pymssql            # SQL Server
pip install "markitdown[pdf,docx]"  # 解析设计文档（PDF/DOCX）
```

**国内镜像**（连默认 registry 慢时）：

```bash
npm config set registry https://registry.npmmirror.com
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# scaffold 时临时传给 npm
NPM_REGISTRY=https://registry.npmmirror.com python scripts/scaffold.py ./business-docs
```

---

## 快速开始

在任何支持 skill 的 AI 客户端（Claude Code / Trae / Cursor / Windsurf 等）里打开你要分析的项目，对 AI 说：

> 帮我分析这个项目的业务，我想搞懂它在做什么生意

或者更明确：

> 用 business-analyzer skill 分析当前项目，生成业务文档

AI 会按 5 个 Phase 推进：

1. **Phase 1 · 项目扫描**：搞清"这是个什么项目"，5 个元问题口述回答等用户确认
2. **Phase 2 · 业务领域深潜**：数据库 Schema → 业务实体 → 用户角色 → 业务流程 → 业务规则 → 领域划分
3. **Phase 3 · 知识结构化**：选文档组合 + 主题，列清单等用户确认
4. **Phase 4 · HTML 文档生成**：scaffold 项目 → 逐 Section 写 → build
5. **Phase 5 · 交付与维护**：`dist/index.html` 双击打开，附维护提醒

最终产物：

```
your-project/
└── business-docs/
    ├── src/                  # 单项目 SPA 源码
    │   ├── pages/            # 各文档页面（各选主题）
    │   ├── sections/         # Section 组件（一个文件一节）
    │   └── components/       # 共享组件（Cover/Colophon/MermaidDiagram）
    ├── analysis/
    │   └── business-knowledge.md   # 分析笔记（agent 记忆，不交付）
    └── dist/
        └── index.html        # 📦 交付物（单文件，所有文档在一个 HTML 里）
```

---

## 集成的开源项目

本 skill 站在巨人肩膀上，向以下开源项目致谢：

### 渲染与构建

| 项目 | 用途 | 仓库 |
|------|------|------|
| [**reacticle**](https://www.npmjs.com/package/reacticle) | 文章渲染引擎，11 主题 + 语义组件协议（Section / Aside / Raw / Table / Hero ...） | npm 包 |
| [**React**](https://react.dev/) + [**React Router**](https://reactrouter.com/) | SPA 框架 + HashRouter（支持 `file://` 离线路由） | https://github.com/facebook/react |
| [**Vite**](https://vitejs.dev/) | 构建工具，dev server + production build | https://github.com/vitejs/vite |
| [**vite-plugin-singlefile**](https://github.com/richardtallent/vite-plugin-singlefile) | 把所有 CSS / JS 内联到单 HTML，离线可打开 | GitHub |
| [**TypeScript**](https://www.typescriptlang.org/) | 类型安全 | https://github.com/microsoft/TypeScript |

### 图表

| 项目 | 用途 | 仓库 |
|------|------|------|
| [**Mermaid**](https://mermaid.js.org/) | 文本描述画图：flowchart / stateDiagram / sequenceDiagram / erDiagram | https://github.com/mermaid-js/mermaid |

> 本 skill 预置 `mermaid-overrides.css` 用 `--ra-*` token 覆盖 Mermaid 11 的 inline style，让图表跟随 reacticle 主题。Mermaid 是 npm 安装 + Vite 打包 + singlefile 内联，**离线可用**。

### 代码分析

| 项目 | 用途 | 仓库 |
|------|------|------|
| [**CodeGraph**](https://github.com/colbymchenry/codegraph) | Rust 内核的代码知识图谱（tree-sitter + SQLite），tree-sitter 解析 + 调用边索引，业务分析效率提升 89% | https://github.com/colbymchenry/codegraph |

### 数据库驱动（按需）

| 项目 | 用途 | 仓库 |
|------|------|------|
| [**PyMySQL**](https://github.com/PyMySQL/PyMySQL) | MySQL / Doris 连接 | https://github.com/PyMySQL/PyMySQL |
| [**psycopg**](https://www.psycopg.org/) | PostgreSQL 连接 | https://github.com/psycopg/psycopg |
| [**python-oracledb**](https://oracle.github.io/python-oracledb/) | Oracle 连接 | https://github.com/oracle/python-oracledb |
| [**pymssql**](https://github.com/pymssql/pymssql) | SQL Server 连接 | https://github.com/pymssql/pymssql |

### 文档解析

| 项目 | 用途 | 仓库 |
|------|------|------|
| [**MarkItDown**](https://github.com/microsoft/markitdown) | Microsoft 出品，把 PDF / DOCX 设计文档转成可读 Markdown | https://github.com/microsoft/markitdown |

### PDF 导出

PDF 导出脚本（`scripts/html-to-pdf.py`）不引入额外 Python 依赖，直接调用本机已装的 **Chromium / Google Chrome / Microsoft Edge** headless 模式打印，自动探测浏览器路径。

---

## 目录结构

```
business-analyzer/
├── SKILL.md                    # Skill 主指令（AI 读这个）
├── README.md                   # 本文件
├── references/                 # 参考文档（AI 按需读）
│   ├── analysis-methods.md     # 业务分析方法（四步递进）
│   ├── end-to-end-mainline.md  # 端到端主线识别
│   ├── state-machine-guide.md  # 状态机提取
│   ├── diagram-guide.md        # Mermaid 图表指南
│   ├── html-rendering.md       # Phase 4 渲染入口
│   ├── scaffold.md             # 脚手架说明
│   ├── document-templates.md   # 文档模板
│   ├── microservices-guide.md  # 微服务分析
│   ├── codegraph-guide.md      # CodeGraph 使用
│   ├── database-analysis.md    # 数据库分析
│   ├── incremental-update.md   # 增量更新
│   ├── pdf-output.md           # PDF 导出
│   ├── themes/                 # 11 个主题 profile
│   │   ├── index.json
│   │   ├── tufte.md
│   │   ├── press.md
│   │   └── ...
│   └── ...
├── scripts/                    # Python 脚本
│   ├── scaffold.py             # 创建文档项目工作区
│   ├── db-introspect.py        # 数据库 Schema 抽取（只读）
│   ├── analyze-schema.py       # Schema → 业务实体分析
│   ├── html-to-pdf.py          # HTML → PDF（headless 浏览器）
│   ├── source-to-markdown.py   # 项目 MD/TXT 转可读格式
│   └── source-to-markdown-markitdown.py  # PDF/DOCX → Markdown
└── assets/
    └── scaffold-template/      # 文档项目模板（scaffold.py 复制源）
        ├── src/
        │   ├── main.tsx        # 入口（HashRouter + 锚点修复 + import CSS）
        │   ├── App.tsx         # 路由定义
        │   ├── mermaid-overrides.css   # Mermaid 跟随主题
        │   ├── print-overrides.css     # 打印 CSS
        │   ├── components/     # 共享组件
        │   │   ├── Cover.tsx
        │   │   ├── Colophon.tsx
        │   │   ├── BackLink.tsx
        │   │   └── MermaidDiagram.tsx
        │   ├── pages/          # 页面（含 IndexPage / PrintAllPage / SampleDoc）
        │   └── sections/       # Section 示例
        ├── package.json        # 依赖：react / react-router / mermaid / reacticle
        ├── vite.config.ts      # Vite + singlefile 插件
        └── tsconfig.json
```

---

## 常用命令

```bash
# 列出所有可用主题
python scripts/scaffold.py --list-themes

# 创建文档项目工作区
python scripts/scaffold.py ./business-docs

# 自动检测数据库连接（扫描 .env / application.yml / JDBC URL）
python scripts/db-introspect.py --auto-detect <project-dir>

# 抽取数据库 Schema（只读，仅 SELECT information_schema）
python scripts/db-introspect.py --type mysql --host HOST -u USER -p PASS -d DB

# 分析 Schema → 业务实体
python scripts/analyze-schema.py ./analysis/db-schema/schema-mysql.json

# 导出 PDF（命令行方式）
python scripts/html-to-pdf.py --route print-all

# 文档项目构建（在 business-docs 目录）
cd business-docs && npm run build    # 产出 dist/index.html
```

---

## 工作流程一览

```
Phase 1 项目扫描
  ├─ 环境检测（Python / Node / CodeGraph）
  ├─ CodeGraph 初始化（可选，文件 > 50 个推荐）
  └─ 5 元问题口述确认 → 🛑 Checkpoint 0
        ↓
Phase 2 业务领域深潜
  ├─ 2.0 数据库 Schema 抽取（最可靠信源）
  ├─ 2.1 业务实体 + 核心业务概念关系网
  ├─ 2.2 端到端主线 → 子流程 → 状态机 → 异常分支
  ├─ 2.3 业务规则
  ├─ 2.4 用户角色
  ├─ 2.5 领域划分
  └─ 写入 business-knowledge.md
        ↓
Phase 3 知识结构化
  ├─ 选文档组合（业务全景图 / 领域模型 / 流程 / 规则 / 角色 / 词汇表 / 架构 / 状态机）
  ├─ 每份文档选主题
  └─ 🛑 Checkpoint 1 确认清单
        ↓
Phase 4 HTML 文档生成
  ├─ scaffold.py 创建项目（仅一次）
  ├─ 每份文档：Page 组件 → Plan → First Spread → Full Build → Review → Repair
  └─ npm run build → dist/index.html
        ↓
Phase 5 交付与维护
  ├─ 双击 dist/index.html 打开
  ├─ 推荐 PDF 导出（页面点击 / 命令行）
  └─ 增量更新机制说明（git diff 驱动）
```

---

## License

MIT
