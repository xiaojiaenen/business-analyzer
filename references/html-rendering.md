# HTML 文档渲染引擎

本文档是 Phase 4 的入口——用 reacticle 组件协议将业务分析结果渲染为精美 HTML 文章。所有渲染相关的知识都在本 skill 的 `references/` 目录中，不依赖任何外部 skill。

## 架构

```
渲染引擎 = reacticle（React 组件库，npm 安装）+ 11 个内置主题 + 本 skill 的参考文档
```

reacticle 从 npm 安装（`npm install reacticle@latest`），提供：
- 语义化文章组件（`Article`, `Hero`, `Lead`, `Section`, `Raw` 等）
- 运行时主题系统（`<ThemeProvider theme="...">`）
- 构建工具链（Vite + vite-plugin-singlefile → 自包含 HTML）

---

## Phase 4 各步骤速查

| 步骤 | 做什么 | 读哪个参考文件 |
|------|--------|---------------|
| 搭工作区 | scaffold.py 创建 Vite + React + TS 项目 | `references/scaffold.md` |
| 选主题 | 从 11 个主题中选合适的 | `references/themes/index.json` + `references/theme-selection.md` |
| 写 source.md | 把分析笔记转为业务叙述 | `references/source-to-markdown.md` |
| 做规划 | Brief / Outline / Theme / Assets | `references/plan-template.md` |
| 定文章类型 | 选文章类型和结构 | `references/article-types.md` |
| 定信息密度 | 正文 vs 视觉块比例 | `references/information-density.md` |
| 写组件 | reacticle 组件用法和规则 | `references/component-policy.md` |
| 写 Raw | 自由层 HTML/CSS/JS/React | `references/raw-policy.md` |
| 写 Section | 一节一文件铁律 | `references/section-build.md` |
| 做封面 | 书封式题图 | `references/cover.md` |
| 定版式 | 宽度 + TOC | `references/layout.md` |
| 选配图 | 配图策略 | `references/asset-policy.md` |
| 质检 | 各阶段 checklist | `references/review-checklist.md` |
| 修复 | 最小切片修复规则 | `references/repair-policy.md` |
| 构建交付 | dev / build / html 命令 | `references/html-output.md` |
| 导出 PDF | 可选 PDF 导出 | `references/pdf-output.md` |

---

## 主题速查（11 个内置主题）

所有主题的完整 authoring profile 在 `references/themes/<id>.md`。索引和 bestFor 在 `references/themes/index.json`。

| ID | 名称 | 气质 | 最适合 |
|----|------|------|--------|
| `tufte` | Data-Ink | 证据、数据、克制、低装饰 | 领域模型、规则手册、流程、架构 |
| `press` | 书卷/编辑 | 出版、叙事、温暖、编辑感 | 业务全景、角色权限、词汇表 |
| `vignelli` | 瑞士国际 | 冷中性、sans、网格、系统化 | 参考文档、API 说明 |
| `freddie` | 暖黄/友善 | 暖白+明黄、机灵有人味 | 教程、入门文档、FAQ |
| `andy` | 静谧/温柔 | 暖奶油+暖橙、柔软平静 | 入门指南、生活内容 |
| `bodoni` | 报刊/Didone | 极致黑白、戏剧高反差 | 宣言、深度长文 |
| `bayer` | 包豪斯/三原色 | 响亮理性、三原色几何 | 教程、品牌、宣言 |
| `fuller` | 蓝图/工程制图 | 冷峻技术暗色、蓝图底 | RFC、系统设计 |
| `shannon` | 暗色工程 | 暗底、仪表信号、克制 | 系统设计、技术复盘 |
| `knuth` | 学术预印本 | 正式、严谨、公式优先 | 分析报告、技术论文 |
| `sottsass` | 孟菲斯/80s | 叛逆好玩、撞色粉彩 | 设计写作、文化内容 |

### 为业务文档选主题

| 文档 | 首选 | 备选 |
|------|------|------|
| 业务全景图 | `press`（叙事感强） | `freddie`（轻松入门） |
| 领域模型 | `tufte`（证据驱动） | `vignelli`（结构化） |
| 核心业务流程 | `tufte`（步骤清晰） | `press`（叙事流） |
| 业务规则手册 | `tufte`（严谨清单） | `vignelli`（中性规格） |
| 角色与权限 | `press`（可读性强） | `freddie`（轻松） |
| 词汇表 | `press` | `freddie` |
| 系统架构 | `tufte`（图表处理强） | `fuller`（工程感） |

---

## 最小工作区搭建

### 自动搭建（推荐）

```bash
python scripts/scaffold.py ./01-business-overview --theme=press
python scripts/scaffold.py ./06-glossary --theme=press --no-cover
python scripts/scaffold.py --list-themes
```

### 手动搭建（scaffold.py 不可用时）

```bash
mkdir -p article-doc/article/sections article-doc/article/raw-blocks article-doc/article/assets
mkdir -p article-doc/source article-doc/plan article-doc/review

# 复制 scaffold 模板文件
cp -r assets/scaffold-template/* article-doc/
cd article-doc && npm install && npm install reacticle@latest
```

---

## 核心规则（始终适用）

1. **Prose-first**：正文是主体，组件是点睛，Raw 是表现力
2. **语义，不表达布局**：说"这是关键洞察"，不说"蓝卡片 24px 边距"
3. **Props 即协议**：填齐必填字段，没有就留空让组件标记缺口
4. **主题，不写样式**：只通过 `<ThemeProvider>` 选主题，不手写组件样式
5. **一个 Section = 一个文件**：`sections/NN-*.tsx`，绝不把多个 Section 写在一个文件里
6. **版式与主题解耦**：`Article` 的 `width` 和 `toc` 是独立决策
7. **Raw 用 `--ra-*` token**：不写野生颜色

---

## 构建命令

```bash
npm run dev       # 开发预览
npm run build     # tsc + vite build → 自包含 HTML（CSS+JS 内联）
npm run html      # build + 复制到 article/article.html（交付物）
npm run typecheck # 仅类型检查
```

---

## Harness 流程（每份文档）

```
Source → Plan → Checkpoint → First Spread → Checkpoint → Full Build → Final Review → Repair → Delivery
```

**第一份文档（业务全景图）走全流程。后续文档复用主题，只确认首屏。**

---

## 核心提醒

- 正文是主体：每个 Section 至少 60% 是正文段落
- Raw 自由但一致：颜色/字体/间距必须用 `--ra-*` CSS 变量
- 业务文档配图选 `none`（不需要 AI 生成装饰图，Raw 不受影响）
- 每个 Section 写成独立文件（`sections/NN-*.tsx`）
- 封面默认开，词汇表和规则手册建议关
