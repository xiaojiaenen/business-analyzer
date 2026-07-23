# PDF 输出（可选）

把交付的单页 HTML（`dist/index.html`）转成 PDF。**这是 Phase 5 交付里的可选步骤**。

> HTML 仍然是主交付物：它能离线打开、可分享、可在浏览器里完整体验 Raw 交互。PDF 是给"需要
> 归档 / 打印 / 邮件附件 / 不联网阅读"场景的补充，**Raw 交互在 PDF 里只能渲染为初始态**。

---

## 两种导出方式

### 方式 A · 页面点击导出（推荐，离线可用）

文档首页（IndexPage）有「导出 PDF」按钮，点击后：

1. 跳转到 `/print-all` 预览页——所有文档按顺序连排在一页里
2. 自动弹出浏览器打印对话框
3. 用户在对话框选「另存为 PDF」→ 保存

**完全离线可用**——不需要命令行、不需要装任何工具。print CSS 已内联到构建产物里（`src/print-overrides.css`），`file://` 打开也能用。

预览页还有「返回首页」和「打印 / 另存为 PDF」按钮，用户可以先预览再手动打印。

### 方式 B · 命令行导出（自动化场景用）

```bash
# 项目根目录
npm run build                                                   # 先确保有 dist/index.html

# 导出所有文档到一个 PDF
python scripts/html-to-pdf.py --route print-all                # dist/index.html#/print-all → dist/index.pdf

# 只导出某一份文档为 PDF
python scripts/html-to-pdf.py --route business-overview        # dist/index.html#/business-overview → dist/index.pdf

# 自定义路径
python scripts/html-to-pdf.py in.html out.pdf --route print-all
```

也可以把这个 bash 调用放到工作区 `package.json` 的 scripts 里，让用户 `npm run pdf` 就跑
（路径是用户机器上 Skill 的绝对路径，**不在脚手架模板里固化**，避免硬编码）。

### 选哪种？

| 场景 | 用哪种 |
|------|--------|
| 普通用户想导出 PDF | **方式 A**（页面点击） |
| CI/CD 自动化归档 | **方式 B**（命令行） |
| 只导出某一份文档 | **方式 B**（`--route <doc-name>`） |
| 离线环境（file:// 打开） | **方式 A**（纯前端，零依赖） |

### --route 参数（命令行方式必读）

本 skill 是多文档 SPA（HashRouter 路由切换），所有文档在同一个 `dist/index.html` 里。
脚本默认打开首页（导航页），**只打印当前路由**。

| --route 值 | 打开 URL | 导出什么 |
|-----------|---------|---------|
| 不传 | `index.html` | 导航首页（只 1 页） |
| `print-all` | `index.html#/print-all` | **所有文档连排成一个 PDF**（推荐） |
| `<doc-name>` | `index.html#/<doc-name>` | 只导出指定文档 |

`print-all` 路由由 `src/pages/PrintAllPage.tsx` 实现——把所有文档页面组件按顺序渲染在一页里，
每份文档之间用分页符隔开。Agent 生成文档时要在 PrintAllPage 里 import 并排列所有文档组件。

### 多文档 PDF 的分页行为

`src/print-overrides.css`（页面方式）和 `scripts/pdf-print-overrides.css`（命令行方式）都包含
D 组规则控制多文档分页：
- **D1**：每份文档的 `.ra-root` 之间分页（最后一份不分，避免末尾空白页）
- **D2**：取消 `min-height: 100vh`，让内容自然流动（否则前面文档后大段空白）
- **D3**：只保留第一份文档的 TOC，其余隐藏（避免每份文档都重复 TOC）

如果用户想保留每份文档的 TOC，注释掉两个 CSS 文件里的 D3 规则即可。

---

## 前提条件

本机已装 chromium-family 浏览器之一（脚本会自动探测，按下列顺序）：

```text
chromium / chromium-browser / google-chrome / google-chrome-stable / chrome
brave-browser / microsoft-edge
/Applications/Google Chrome.app/...
/Applications/Chromium.app/...
/Applications/Microsoft Edge.app/...
/Applications/Brave Browser.app/...
/Applications/Arc.app/...
/usr/bin/chromium / /snap/bin/chromium
```

**找不到任何浏览器** → 脚本不会爆，会给出回退指引：注入了打印 CSS 的临时 HTML 路径会被
打印出来，用户可以用任意浏览器手动 `Cmd+P` / `Ctrl+P` → "另存为 PDF"。

不依赖 Node / npm 包 / puppeteer / playwright / weasyprint —— 故意只用系统已装的浏览器，
零环境配置。

---

## 设计原理（重要 · 调样式前先读）

### 1. 为什么要注入 print CSS（不是改 reacticle）

reacticle 的 TOC 在桌面是**左右栅格**（`.ra-article-layout--with-toc` 是 `display: grid`，
两列：TOC | 文章），在 mobile（≤999px）才塌成单列 `display: block`。

PDF 阅读习惯是**上下排布**（TOC 先 / 正文后），跟 mobile 体验对齐。最干净的实现：在 PDF
生成时**注入一段 `@media print` CSS**，强制 `display: block`，等价于复用 mobile 分支。
这样：

- **不动 reacticle**：任何版本的 reacticle 都能用这个脚本生成合理 PDF。
- **不动用户的 Article.tsx**：用户的源码完全不受影响。
- **CSS 只在打印生效**：浏览器里看 HTML 还是左右栅格。

### 2. 注入了哪几条规则

CSS 抽到了独立文件 **`scripts/pdf-print-overrides.css`**（与脚本同目录），分三组：

```text
A · TOC 排版（让 TOC 上 / 正文下）
  A1) .ra-article-layout--with-toc { display: block }   → 塌成单列
  A2) .ra-toc { position: static; page-break-after: always } → 解 sticky + 独占首页
  A3) .ra-toc__list { column-count: 2 }                 → 长 TOC 双列省纸
  A4) .ra-toc__item { break-inside: avoid }             → TOC 项不被列间撕开
  A5) .ra-article-layout--with-toc > .ra-article        → 正文在 TOC 后自然流
  A6) .ra-toc a / .ra-article a { text-decoration: none } → 关闭打印链接下划线

B · 分页行为（修长文章的大块空白页）
  B1) .ra-section / .ra-subsection { break-inside: auto !important }
        → 撤销 reacticle print.css 里的 break-inside: avoid-page。
          对长 Section 来说，那条规则会把整节推到下一页、留前一页大半空白。
  B2) h1-h4 + .ra-section__head + .ra-subsection__head { break-after: avoid }
        → 标题不被孤儿化（不会孤零零卡在页底，下面是空白）
  B3) .ra-hero / .ra-lead / .ra-conclusion { break-inside: avoid }
        → 短的开场 / 收束块原子化，不撕开
  B4) p / li / blockquote { orphans: 3; widows: 3 }
        → 段落不留 1-2 行寡行
  B5) figure / .ra-table / .ra-codeblock / .ra-formula / .ra-image / .ra-raw
        { break-inside: avoid }
        → 图表、表格、代码块、Raw 块尽量整块；过高时浏览器仍会自动 fallback 分页

C · 封面（若文章有 3:4 封面，让它独占 PDF 首页）
  C1) .ra-cover { break-after: always; break-inside: avoid }
        → 屏幕和 PDF 都保持 3:4 书封；打印时 TOC 从第二页开始
        → 详见 references/cover.md
```

完整带注释的 CSS 直接看 `scripts/pdf-print-overrides.css`。要调样式（比如换页面 break 策略
/ 改双列阈值 / 加打印水印），**直接改这个文件就行**，不用动 bash 脚本。

> **为什么 CSS 是独立文件**：macOS 自带 BSD awk 对 `-v inject="$INLINE_CSS"` 这种多行字符串
> 报 `newline in string` 错（GNU awk 没事）。把 CSS 抽成文件，awk 用 `getline < file` 读取，
> 两个 awk 都吃得下。顺带也让 CSS 变成可独立编辑 / lint / diff 的真正资源。

reacticle 自带的 `print.css` 仍然生效（白底黑字 / 隐藏 export bar / `break-inside: avoid`
等），本脚本只补 TOC 排版那一块。

### 3. 渲染流程

```
index.html  ──── awk 注入 print CSS ────  /tmp/index-print.html
                                                  │
                                                  ▼
                  探测的浏览器 --headless --print-to-pdf
                                                  │
                                                  ▼
                                          article.pdf
```

Chrome 标志：

- `--headless=new`（旧版 fallback 到 `--headless`）：无窗口模式。
- `--no-pdf-header-footer` / `--print-to-pdf-no-header`：去掉浏览器自带的 URL / 日期 / 页码
  （颠倒了 colophon 的角色）。
- `--virtual-time-budget=5000`：给页面 JS 5 秒初始化时间，让 Raw 组件、KaTeX、Prism 等
  渲染完再截屏。
- `--hide-scrollbars` / `--disable-gpu` / `--no-sandbox`：清洁渲染。

### 4. Raw 交互在 PDF 里会怎样？

PDF 是**静态文档**，所有 Raw 交互（滑块、按钮、动画、canvas、视频）只能渲染**初始状态**。
设计建议：

- **interactive-explainer 类型**：PDF 价值有限（核心是"操作"），用户可在 Plan 阶段不开
  PDF 导出。
- **其它类型**：Raw 通常是辅助图解（流程图 / SVG / 趋势图），初始态已经够看，PDF 没问题。
- **Raw 内的内容若依赖 hover / click 才显示**：在写 Raw 时考虑"是否打印友好"，如默认露出
  关键内容、用 `print:` 风格让 hover 状态在打印时强制展开。

---

## 故障排除

### 找不到浏览器

脚本会打印临时 HTML 路径（已经注入打印 CSS），手动 Cmd+P 即可。

### PDF 里 TOC 没分页 / 跟正文挤在一起

某些 Chromium 旧版本对 `page-break-after: always` 的支持有差异。可以：

- 升级 Chrome 到当前主版本。
- 或手动 Cmd+P 时在打印对话框选"两面 / 缩放 / 自定义边距"。

### PDF 分页奇怪 / 出现大块空白页 / 标题孤零零卡在页底

通常是某些"原子块"被强制不分页导致整块被推到下一页。检查 `pdf-print-overrides.css`：

- **B1** 是否生效（看 DevTools Print Preview 里 `.ra-section` 的 `break-inside` 值）。
  reacticle `print.css` 那条没 `!important`，理论上我们的 `!important` 一定能赢。
- 自己写的 **Raw 块**里有没有 inline `style={{ breakInside: 'avoid' }}` 或类似 CSS —— 删掉。
- 如果还想"标题永远不卡页底"，把 B2 里 `break-after: avoid` 改成
  `break-before: avoid; break-after: avoid`（更激进，但偶尔会牺牲一些纸面利用率）。

### PDF 里 Raw 没渲染完整 / 图表是空白

- 增加 `--virtual-time-budget`（编辑脚本，从 5000 改到 10000+）。
- 检查 Raw 的 JS 是否在 DOMContentLoaded 内同步渲染（异步加载的远程图片 / 数据可能没等到
  截屏就开拍）。
- 改造 Raw：用 SSR-friendly 的初始态 + 客户端 hydrate 增强，不要"完全靠 JS 后才能看"。

### PDF 字体跟浏览器看不一样

主题用了 `@font-face` 远程字体？headless Chrome 默认不等远程字体加载完。可以：

- 用 system font fallback（推荐，多数主题已经做了）。
- 或在 HTML 里把字体 `data:` 内联（vite-plugin-singlefile 已经处理静态资源，但 woff 字体
  要看主题怎么写的）。

### 想自定义页面留白 / 纸张大小

Chromium 的 `--print-to-pdf` 不支持命令行页面尺寸 / 边距参数。当前 CSS 用
`@page { margin: 0 }` 让主题纸色铺满整页，再用 `.ra-root { padding: 0.45in }`
提供内容留白。如果需要改留白，优先调整 `scripts/pdf-print-overrides.css` 里的
`.ra-root` print padding。

如果用户真的要自定义，建议：

1. 用浏览器 GUI 打印（Cmd+P）—— 那里有边距 / 纸张 / 缩放选项。
2. 或者派生一个 `html-to-pdf-puppeteer.py` 脚本，单独支持自定义。当前脚本默认按 Chrome
   默认页面尺寸（Letter 美区 / A4 其它区）输出。

---

## 与 Skill 流程的关系

| 阶段 | 触发 | 动作 |
|---|---|---|
| Phase 5 交付 | 用户想导出 PDF | 页面首页点「导出 PDF」按钮（推荐），或命令行 `python scripts/html-to-pdf.py --route print-all` |
| 只导出某份文档 | 用户想单份 PDF | `python scripts/html-to-pdf.py --route <doc-name>` |
| 用户事后想补 PDF | 任何时刻 | 在工作区根目录手动跑上述命令 |

---

## 不做的事

- ❌ 不在脚手架强行装任何 PDF 相关 npm 包（保持脚手架轻量，页面点击导出走浏览器原生打印，零依赖）。
- ❌ 不默认导出 PDF（PDF 不是主交付物，HTML 才是）。
- ❌ 不替用户判断"要不要 PDF" —— Phase 5 交付时用户自行决定。
- ❌ 不改 reacticle 来支持 PDF（CSS 注入更轻量、跟 reacticle 版本解耦）。
