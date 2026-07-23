import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";

// Mermaid 图表复用组件。
// 用法：在 Section 里 <MermaidDiagram graph={diagramText} /> 或带主题：
//      <MermaidDiagram graph={diagramText} theme="dark" />
// 详见 references/diagram-guide.md。
//
// 离线原理：mermaid 是 npm 安装的，Vite 打包进 bundle，vite-plugin-singlefile 内联到单 HTML，断网可用。
// 不要用 CDN import（离线会失败）。
//
// 主题协调：默认 "neutral" 适配 tufte/press/vignelli；shannon/fuller 用 "dark"；freddie/andy 用 "base"。
// theme prop 可选值：neutral / dark / base / default（Mermaid 内置主题）。
//
// 视觉协调：src/mermaid-overrides.css 用 --ra-* token 覆盖 Mermaid SVG 内部样式，
// 让图表自动跟随文章主题（字体、颜色、线条粗细）。wrapper div 的 className
// "mermaid-wrapper" 是 CSS 选择器的钩子。

export type MermaidTheme = "neutral" | "dark" | "base" | "default";

// 按 theme 缓存 mermaid.initialize 的调用，避免每次渲染都重复 init。
const initializedThemes = new Set<MermaidTheme>();

function ensureInit(theme: MermaidTheme) {
  if (initializedThemes.has(theme)) return;
  mermaid.initialize({
    startOnLoad: false,
    theme,
    // themeVariables 只控制结构性变量；颜色/字体由 mermaid-overrides.css 用 --ra-* token 覆盖，
    // 这样切换文章主题时图表自动跟随。这里只设字号和曲线半径。
    themeVariables: {
      fontSize: "13px",
      // 以下设为透明，让 CSS 接管颜色
      mainBkg: "transparent",
      nodeBorder: "transparent",
      clusterBkg: "transparent",
      clusterBorder: "transparent",
      edgeLabelBackground: "transparent",
    },
    flowchart: {
      curve: "basis", // 曲线连线，比默认折线更柔和
      nodeSpacing: 40,
      rankSpacing: 40,
      useMaxWidth: true,
    },
    state: {
      useMaxWidth: true,
    },
    sequence: {
      useMaxWidth: true,
      actorMargin: 60,
      boxMargin: 12,
    },
  });
  initializedThemes.add(theme);
}

let renderCounter = 0;

export function MermaidDiagram({
  graph,
  theme = "neutral",
}: {
  graph: string;
  theme?: MermaidTheme;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    ensureInit(theme);
    renderCounter += 1;
    const id = `mmd-${renderCounter}-${Math.random().toString(36).slice(2, 6)}`;
    mermaid
      .render(id, graph)
      .then(({ svg }) => {
        if (!cancelled) {
          setSvg(svg);
          setError("");
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(String(err?.message || err));
          setSvg("");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [graph, theme]);

  if (error) {
    return (
      <div
        style={{
          padding: "var(--ra-space-3, 0.75rem)",
          border: "1px dashed var(--ra-color-border, currentColor)",
          borderRadius: "var(--ra-radius-md, 0.25rem)",
          fontSize: "var(--ra-text-sm, 0.875rem)",
          color: "var(--ra-color-muted, inherit)",
        }}
      >
        图表渲染失败：{error}
        <pre
          style={{
            fontSize: "var(--ra-text-xs, 0.75rem)",
            marginTop: "0.5rem",
            whiteSpace: "pre-wrap",
          }}
        >
          {graph}
        </pre>
      </div>
    );
  }

  // wrapper div 的 className "mermaid-wrapper" 是 mermaid-overrides.css 的选择器钩子。
  // CSS 通过这个钩子覆盖 SVG 内部样式，让图表跟随文章主题（字体/颜色/线条粗细）。
  return (
    <div ref={ref} className="mermaid-wrapper" dangerouslySetInnerHTML={{ __html: svg }} />
  );
}
