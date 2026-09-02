import { useEffect, useRef, useState, useCallback } from "react";
import { createPortal } from "react-dom";
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
//
// 交互（v6）：
//   · 点击图表 → 全屏灯箱放大查看（矢量 SVG，放大不糊）
//   · 灯箱内：滚轮 / + / − 缩放，滚动条平移，点击遮罩或 Esc 关闭
//   · wrapper 加 data-mermaid-ready，供 PrintAllPage 检测渲染完成后再 window.print()
//     （避免 14 文档 + 36 图异步渲染未完时打印出空白 PDF）

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

/** 解析 SVG 字符串里的 viewBox，返回 {w, h}；取不到时返回 null */
function parseViewBox(svgHtml: string): { w: number; h: number } | null {
  const m = svgHtml.match(/viewBox="\s*[\d.\-]+\s+[\d.\-]+\s+([\d.]+)\s+([\d.]+)"/);
  if (!m) return null;
  const w = parseFloat(m[1]);
  const h = parseFloat(m[2]);
  if (!isFinite(w) || !isFinite(h) || w <= 0 || h <= 0) return null;
  return { w, h };
}

export function MermaidDiagram({
  graph,
  theme = "neutral",
}: {
  graph: string;
  theme?: MermaidTheme;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState("");
  const [svgId, setSvgId] = useState("");
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState("");

  // 灯箱状态
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [scale, setScale] = useState(1);
  const vb = svg ? parseViewBox(svg) : null;
  // 灯箱里用一份"克隆 SVG"：把原 SVG 的 id 前缀整体换成新 id，避免两份同 id 的
  // <style>/<defs> 互相干扰（mermaid 生成的 SVG 内部用 #mmd-xxx 选择器）。
  const lightboxSvg = useRef("");

  useEffect(() => {
    let cancelled = false;
    ensureInit(theme);
    renderCounter += 1;
    const id = `mmd-${renderCounter}-${Math.random().toString(36).slice(2, 6)}`;
    setSvgId(id);
    setStatus("loading");
    mermaid
      .render(id, graph)
      .then(({ svg: rendered }) => {
        if (cancelled) return;
        setSvg(rendered);
        // 克隆并改名 id，供灯箱放大使用
        lightboxSvg.current = rendered.split(id).join(`${id}-zoom`);
        setStatus("ready");
        setError("");
      })
      .catch((err) => {
        if (cancelled) return;
        setStatus("error");
        setError(String(err?.message || err));
        setSvg("");
      });
    return () => {
      cancelled = true;
    };
  }, [graph, theme]);

  // Esc 关闭灯箱
  useEffect(() => {
    if (!lightboxOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setLightboxOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [lightboxOpen]);

  // 灯箱打开时重置缩放
  const openLightbox = useCallback(() => {
    if (status !== "ready" || !svg) return;
    setScale(1);
    setLightboxOpen(true);
  }, [status, svg]);

  const zoomBy = useCallback((factor: number) => {
    setScale((s) => Math.min(5, Math.max(0.5, s * factor)));
  }, []);

  if (error) {
    return (
      <div
        data-mermaid-ready="error"
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

  return (
    <>
      <div className="mermaid-figure">
        {/* wrapper div 的 className "mermaid-wrapper" 是 mermaid-overrides.css 的选择器钩子。
            CSS 通过这个钩子覆盖 SVG 内部样式，让图表跟随文章主题（字体/颜色/线条粗细）。 */}
        <div
          ref={ref}
          className="mermaid-wrapper"
          data-mermaid-ready={status}
          data-mermaid-svg-id={svgId}
          role="button"
          tabIndex={0}
          aria-label="点击放大查看图表"
          title="点击放大"
          onClick={openLightbox}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              openLightbox();
            }
          }}
          dangerouslySetInnerHTML={{ __html: svg }}
        />
        {status === "ready" && (
          <div className="mermaid-zoom-hint" aria-hidden="true">
            <svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="7" cy="7" r="4.5" />
              <line x1="10.5" y1="10.5" x2="14" y2="14" />
              <line x1="5" y1="7" x2="9" y2="7" />
            </svg>
            点击放大
          </div>
        )}
      </div>

      {/* 灯箱：点击遮罩 / 关闭按钮 / Esc 关闭；滚轮与按钮缩放 */}
      {lightboxOpen &&
        createPortal(
          <div
            className="mermaid-lightbox no-print"
            onClick={(e) => {
              if (e.target === e.currentTarget) setLightboxOpen(false);
            }}
          >
            <div className="mermaid-lightbox__toolbar">
              <span className="mermaid-lightbox__title">图表放大查看</span>
              <div className="mermaid-lightbox__controls">
                <button type="button" onClick={() => zoomBy(1 / 1.25)} title="缩小" aria-label="缩小">
                  −
                </button>
                <span className="mermaid-lightbox__scale">{Math.round(scale * 100)}%</span>
                <button type="button" onClick={() => zoomBy(1.25)} title="放大" aria-label="放大">
                  +
                </button>
                <button type="button" onClick={() => setScale(1)} title="重置为 100%" aria-label="重置缩放">
                  重置
                </button>
                <button
                  type="button"
                  className="mermaid-lightbox__close"
                  onClick={() => setLightboxOpen(false)}
                  title="关闭 (Esc)"
                  aria-label="关闭"
                >
                  ✕
                </button>
              </div>
            </div>
            <div
              className="mermaid-lightbox__canvas"
              onWheel={(e) => {
                e.preventDefault();
                zoomBy(e.deltaY < 0 ? 1.15 : 1 / 1.15);
              }}
            >
              <div
                className="mermaid-lightbox__scroller"
                style={
                  vb
                    ? { width: Math.round(vb.w * scale), minWidth: "100%" }
                    : { minWidth: "100%" }
                }
              >
                <div
                  className="mermaid-lightbox__svgwrap"
                  dangerouslySetInnerHTML={{ __html: lightboxSvg.current }}
                />
              </div>
            </div>
          </div>,
          document.body
        )}
    </>
  );
}
