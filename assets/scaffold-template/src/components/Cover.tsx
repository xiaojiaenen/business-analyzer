import type { ReactNode } from "react";

type CoverProps = {
  children?: ReactNode;
};

// 文章封面外壳（3:4 比例，屏幕 + PDF 通用）。
// 各 Page 传入自定义 children 替换占位内容；不需要封面的页面直接不渲染 <Cover />。
//
// 硬约束（详见 references/cover.md）：
//   1. 3:4 比例固定，不要改 aspectRatio
//   2. 图文并茂，禁止纯文字封面
//   3. 颜色/字体/间距只用 --ra-* token
//   4. 内容忠实于文章主旨
//   5. 技术自由（SVG/CSS/Canvas/React），禁止远程图片
//   6. 封面不承担正文
export function Cover({ children }: CoverProps) {
  return (
    <section
      className="ra-cover"
      aria-label="文章封面"
      data-ra-cover=""
      style={{
        position: "relative",
        width: "100%",
        maxWidth: "min(100%, 48rem, calc((100vh - 8rem) * 3 / 4))",
        margin: "0 auto var(--ra-space-7, 3rem) auto",
        aspectRatio: "3 / 4",
        overflow: "hidden",
        background: "transparent",
        color: "var(--ra-color-fg, inherit)",
        borderRadius: "var(--ra-radius-md, 0)",
        border: "1px solid var(--ra-color-border, currentColor)",
        isolation: "isolate",
      }}
    >
      {children ?? <CoverPlaceholder />}
    </section>
  );
}

function CoverPlaceholder() {
  return (
    <>
      <svg
        viewBox="0 0 1200 1600"
        preserveAspectRatio="xMidYMid slice"
        aria-hidden="true"
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          color: "var(--ra-color-border, currentColor)",
          opacity: 0.55,
          zIndex: 0,
        }}
      >
        <defs>
          <pattern id="ra-cover-grid" width="80" height="80" patternUnits="userSpaceOnUse">
            <path d="M 80 0 L 0 0 0 80" fill="none" stroke="currentColor" strokeWidth="0.6" />
          </pattern>
        </defs>
        <rect width="1200" height="1600" fill="url(#ra-cover-grid)" />
        <circle cx="900" cy="1180" r="220" fill="var(--ra-color-accent, currentColor)" opacity="0.18" />
        <line x1="80" y1="1400" x2="560" y2="1400" stroke="currentColor" strokeWidth="2" />
      </svg>

      <div
        style={{
          position: "absolute",
          inset: 0,
          zIndex: 1,
          display: "grid",
          alignContent: "center",
          justifyItems: "start",
          padding:
            "var(--ra-space-7, 3rem) var(--ra-space-8, 4rem) var(--ra-space-7, 3rem) var(--ra-space-8, 4rem)",
          gap: "var(--ra-space-3, 0.75rem)",
        }}
      >
        <span
          style={{
            fontSize: "var(--ra-text-xs, 0.75rem)",
            letterSpacing: "0.22em",
            textTransform: "uppercase",
            color: "var(--ra-color-muted, inherit)",
            opacity: 0.85,
          }}
        >
          COVER · 3 : 4 · 占位
        </span>
        <h1
          style={{
            margin: 0,
            fontSize: "clamp(1.6rem, 4.6vw, var(--ra-text-4xl, 3rem))",
            lineHeight: 1.05,
            fontWeight: "var(--ra-font-weight-bold, 700)",
            color: "var(--ra-color-fg, inherit)",
            maxWidth: "70%",
          }}
        >
          按文章主旨 + 主题，在此处设计封面
        </h1>
        <p
          style={{
            margin: 0,
            fontSize: "var(--ra-text-sm, 0.95rem)",
            color: "var(--ra-color-muted, inherit)",
            maxWidth: "70%",
            lineHeight: 1.4,
          }}
        >
          先读 <code>references/cover.md</code> 与选定主题的 profile，再替换{" "}
          <code>CoverPlaceholder</code> 为本文专属的图文构图。
        </p>
      </div>
    </>
  );
}
