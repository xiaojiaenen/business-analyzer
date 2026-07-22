import { Article, Hero, Lead, Raw } from "reacticle";
import { SectionOpening } from "./sections/01-opening";

// Article.tsx is the ASSEMBLER, owned by the main agent. It imports and orders
// Section components — it must NOT contain Section bodies inline.

export function ArticleDoc() {
  return (
    <Article toc width="regular">
      {/*
        ─── Back to Index ───
        每篇文章顶部放一个返回导航首页的链接，位置在 Hero 之前。
        用户读到一半想回首页时不用翻到底部。
      */}
      <Raw title="">
        <nav style={{
          marginBottom: "var(--ra-space-4, 1rem)",
          fontSize: "var(--ra-text-sm, 0.875rem)",
        }}>
          <a
            href="../index.html"
            style={{
              color: "var(--ra-color-muted, inherit)",
              textDecoration: "none",
              display: "inline-flex",
              alignItems: "center",
              gap: "0.3em",
            }}
          >
            ← 返回文档导航
          </a>
        </nav>
      </Raw>

      <Hero
        title="文章标题"
        subtitle="副标题：一句话框定这篇要解决什么"
        meta={[{ label: "日期", value: "2026-06-08" }]}
      />
      <Lead>导语：用一两句话框定主题与读者要带走的判断。</Lead>

      <SectionOpening />
      {/* 在此按顺序加入更多 section 组件 */}

      {/*
        ─── Colophon ───
        每篇文章必须保留这一段，位置在 </Article> 之前、所有 Section /
        Conclusion 之后。它是文章的印记。

        约束：
          • 不要删除。不要移到 Hero 旁边或浮动到角落。
          • 样式只能用 --ra-* token，跟随主题自适应；保持低对比、小字、居中。
      */}
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
          · __THEME__ theme
        </footer>
      </Raw>
    </Article>
  );
}
