import { ThemeProvider, Article, Hero, Lead } from "reacticle";
import { Cover } from "../components/Cover";
import { BackLink } from "../components/BackLink";
import { Colophon } from "../components/Colophon";
import { SectionOpening } from "../sections/sample/01-opening";

const THEME = "tufte";

// 示例文档页面 — 展示单项目中一个文档页面的完整结构。
// 每个文档页面自行声明主题（ThemeProvider）、是否需要封面（Cover）、
// 使用哪些 Section 组件。Agent 复制此模式创建新的文档页面。
export function SampleDoc() {
  return (
    <ThemeProvider theme={THEME}>
      <Cover />
      <Article toc width="regular">
        <BackLink />
        <Hero
          title="示例文档"
          subtitle="展示页面结构、主题和组件用法"
          meta={[{ label: "日期", value: "2026-07-22" }]}
        />
        <Lead>
          这是一个示例文档页面，展示如何在单项目中组织文档、切换主题和使用组件。
        </Lead>

        <SectionOpening />

        <Colophon theme={THEME} />
      </Article>
    </ThemeProvider>
  );
}
