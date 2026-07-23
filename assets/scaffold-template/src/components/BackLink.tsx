import { Link } from "react-router-dom";

// 返回文档导航链接。IndexPage 不使用此组件（它自己就是首页）。
export function BackLink() {
  return (
    <nav
      style={{
        marginBottom: "var(--ra-space-4, 1rem)",
        fontSize: "var(--ra-text-sm, 0.875rem)",
      }}
    >
      <Link
        to="/"
        style={{
          color: "var(--ra-color-muted, inherit)",
          textDecoration: "none",
          display: "inline-flex",
          alignItems: "center",
          gap: "0.3em",
        }}
      >
        ← 返回文档导航
      </Link>
    </nav>
  );
}
