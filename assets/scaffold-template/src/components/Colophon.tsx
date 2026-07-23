import { Raw } from "reacticle";

type ColophonProps = {
  theme: string;
};

// 文章印记（footer）。每篇文档末尾必须保留，位置在 </Article> 之前。
// theme 参数显示该文档使用的主题名称。
export function Colophon({ theme }: ColophonProps) {
  return (
    <Raw title="">
      <footer
        style={{
          marginTop: "var(--ra-space-7, 3rem)",
          paddingTop: "var(--ra-space-4, 1rem)",
          borderTop: "1px solid var(--ra-color-border, currentColor)",
          color: "var(--ra-color-muted, inherit)",
          fontSize: "var(--ra-text-xs, 0.78rem)",
          textAlign: "center",
          letterSpacing: "0.02em",
          opacity: 0.85,
        }}
      >
        Made with{" "}
        <a
          href="https://github.com/xiaojiaenen/business-analyzer"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            color: "inherit",
            textDecoration: "underline",
            textUnderlineOffset: "0.2em",
          }}
        >
          Business Analyzer
        </a>{" "}
        · {theme} theme
      </footer>
    </Raw>
  );
}
