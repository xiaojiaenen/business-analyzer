# HTML 输出与构建

项目是一个 Vite + React + TS + react-router 项目，从 npm 消费 `reacticle`（最新发布版）。
所有文档页面在 `src/pages/` 下，通过 HashRouter 路由切换，共享一个入口 `src/main.tsx`。

## 命令（在项目根目录）

| 命令 | 作用 |
|---|---|
| `npm run dev` | 启动预览（Phase 4 / 5 边写边看）。 |
| `npm run build` | `tsc --noEmit` 类型检查 **+** 构建自包含单页 HTML 到 `dist/index.html`（CSS + JS 内联）。TS 报错会让构建失败，避免错误漏进交付物。 |
| `npm run typecheck` | 仅类型检查。 |
| `npm run preview` | 预览构建产物。 |

单文件由 `vite-plugin-singlefile` 产出：CSS + JS 全部内联，**断网可打开、可分享**。
所有文档页面都在这一个 HTML 文件里，通过 hash 路由切换（如 `#/business-overview`）。

## 切换主题

每个页面组件内自行声明主题，改 `const THEME = "..."` 即可：

```tsx
const THEME = "press";  // 改这里

export function MyDoc() {
  return (
    <ThemeProvider theme={THEME}>
      ...
      <Colophon theme={THEME} />
    </ThemeProvider>
  );
}
```

不同页面可用不同主题。主题 id 必须是组件库已注册的 runtime theme id（`tufte` / `press` / …）。

## PDF（可选 · Phase 5 交付时用户决定）

详见 `references/pdf-output.md`。两种方式：

**方式 A · 页面点击导出**（推荐，离线可用）：首页有「导出 PDF」按钮 → 跳转 `/print-all` → 自动弹打印对话框 → 另存为 PDF。print CSS 已内联，`file://` 打开也能用。

**方式 B · 命令行导出**：
```bash
npm run build                                           # 先有 dist/index.html
python scripts/html-to-pdf.py --route print-all         # → dist/index.pdf（所有文档）
python scripts/html-to-pdf.py --route <doc-name>        # → dist/index.pdf（单份文档）
```

脚本会自动探测系统的 chromium-family 浏览器，headless 打印为 PDF。无 npm 依赖、无 Node。

> Raw 交互在 PDF 里只能渲染为初始态。`interactive-explorer` 类型 PDF 价值有限，用户可在 Phase 5 自行决定要不要导。

## 交付自检

- `npm run build` 成功，`dist/index.html` 能在浏览器离线打开。
- 所有路由链接有效（hash 路由切换正常）。
- 控制台无报错；桌面与移动端都可读，无文字溢出 / 遮挡 / 空白异常。
