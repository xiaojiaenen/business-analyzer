# 脚手架

脚手架在 Phase 4 创建文档项目工作区，**不把工程代码塞进 SKILL.md**。工程模板是 Skill
assets（`assets/scaffold-template/`），由 `scripts/scaffold.py` 复制并接线。

## 用法

```bash
# 创建文档项目（仅一次，所有文档共享）
python scripts/scaffold.py ./business-docs

# 查看可用主题
python scripts/scaffold.py --list-themes
```

项目可建在**任意目录**，不需要在 reacticle 仓库内。

## 脚手架做什么

- 创建项目目录 + 复制 Vite / React / TS / react-router 模板。
- **从 npm 安装最新发布版的 `reacticle`**：`package.json` 里 `reacticle: "latest"`，脚手架
  装完依赖后再 `npm install reacticle@latest` 强制刷新到当下最新，并打印实际版本。
- 创建 `src/` 目录结构：
  - `main.tsx` — 入口（HashRouter，支持离线 file:// 打开 + 锚点跳转修复 + import print-overrides.css + import mermaid-overrides.css）
  - `App.tsx` — 路由定义（含 `/print-all` 打印路由）
  - `print-overrides.css` — 打印 CSS（PDF 导出用，`@media print` 规则）
  - `mermaid-overrides.css` — Mermaid 图表样式覆盖（用 `--ra-*` token 让图表跟随文章主题）
  - `components/` — 共享组件（Cover、Colophon、BackLink、MermaidDiagram）
  - `pages/` — 文档页面（IndexPage 导航首页 + SampleDoc 示例文档 + PrintAllPage 打印专用页）
  - `sections/` — Section 组件（按文档分组）
  - `raw-blocks/` — Raw 块素材（自定义 HTML/SVG，见 `references/raw-policy.md`）
- 每个页面组件内通过 `<ThemeProvider theme="...">` 声明主题——**不同页面可用不同主题**。
- IndexPage 默认 `press` 主题，SampleDoc 默认 `tufte` 主题，展示多主题能力。
- 共享组件 `Colophon`（"Made with Business Analyzer" + GitHub 链接）已内置，
  **不可删除**（见 SKILL.md「默认策略」）。
- 共享组件 `Cover`（书封式封面外壳 + 占位）已内置，各页面自行决定是否使用。
- 共享组件 `BackLink`（返回文档导航）已内置，各页面自行决定是否使用。
- 创建工作记忆目录 `plan/`、`review/`、`analysis/`（`analysis/` 存 `business-knowledge.md` 事实底座 + `db-schema/` 数据库 Schema 抽取产物）。
- `katex` / `prismjs` 作为 `reacticle` 的依赖会被自动带下来，无需单独声明。

## 升级组件库

项目随时可升级到最新组件库：

```bash
npm install reacticle@latest
```

## 项目结构

```text
business-docs/
  package.json  vite.config.ts  tsconfig.json  tsconfig.node.json  index.html  .npmrc
  plan/   review/   analysis/
  src/
    main.tsx              # 入口：HashRouter + App + file:// 锚点修复 + import print/mermaid-overrides.css
    App.tsx               # 路由定义（含 /print-all 打印路由，在此添加 <Route>）
    print-overrides.css   # 打印 CSS（PDF 导出用，@media print 规则）
    mermaid-overrides.css # Mermaid 图表样式覆盖（用 --ra-* token 让图表跟随文章主题）
    components/
      Cover.tsx           # 封面外壳（各页面可选使用）
      Colophon.tsx        # 文章印记（每页末尾必须保留）
      BackLink.tsx        # 返回导航链接
      MermaidDiagram.tsx  # Mermaid 图表复用组件（npm mermaid 预装，离线可用，跟随主题）
    pages/
      IndexPage.tsx       # 导航首页（press 主题 + 导出 PDF 按钮 + 搜索框 + 按业务域分组）
      SampleDoc.tsx       # 示例文档（tufte 主题）
      PrintAllPage.tsx    # 打印专用页（所有文档连排，PDF 导出用）
    sections/
      sample/
        01-opening.tsx    # 示例 Section
```

> **一个 Section = 一个文件**（`sections/<doc-name>/NN-*.tsx`），坚决不允许把多个 Section
> 写进 Page 组件。Page 组件只做组装（import + 排列 Section）。这是多 Agent 并行的前提，
> 详见 `references/section-build.md`。

## 添加新文档

1. 在 `src/pages/` 创建新页面组件（复制 `SampleDoc.tsx` 模式）：
   - 声明主题 `<ThemeProvider theme="...">`
   - 决定是否使用 `<Cover />`
   - import 并排列 Section 组件
   - 末尾放 `<Colophon theme="..." />`
2. 在 `src/sections/<doc-name>/` 创建 Section 文件（`01-opening.tsx` 等）
3. 在 `src/App.tsx` 添加 `<Route path="/<doc-name>" element={<NewDoc />} />`
4. 在 `src/pages/IndexPage.tsx` 的 **`DOCS` 数组**添加一条：
   ```tsx
   {
     to: "/<doc-name>",
     title: "...",
     desc: "...",
     domain: "业务域名",  // 如"交易域""采购域"，用于按域分组
     related: [{ to: "/other-doc", label: "相关文档名" }],  // 可选
   }
   ```
   首页会自动按 `domain` 分组展示，并支持搜索过滤。
5. **在 `src/pages/PrintAllPage.tsx` import 新页面组件并排列**（PDF 导出需要，否则导出的 PDF 缺这份文档）：
   ```tsx
   import { NewDoc } from "./NewDoc";
   // 在 return 里：
   <NewDoc />
   <PageBreak />
   ```

## 切主题

每个页面组件内自行声明主题，改一处即可：

```tsx
const THEME = "tufte";  // 改这里

export function MyDoc() {
  return (
    <ThemeProvider theme={THEME}>
      ...
      <Colophon theme={THEME} />
    </ThemeProvider>
  );
}
```

主题 id 必须是 `references/themes/index.json` 里的 id（当前 `tufte` / `press` / …）。

## 构建 / 预览

见 `references/html-output.md`（`npm run dev` / `build`）。
