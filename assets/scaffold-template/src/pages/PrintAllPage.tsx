import { useEffect } from "react";
import { Raw } from "reacticle";
import { useNavigate, useLocation } from "react-router-dom";
import { SampleDoc } from "./SampleDoc";
// Agent 在此导入所有文档页面组件，例如：
// import { BusinessOverview } from "./BusinessOverview";
// import { DomainModel } from "./DomainModel";
// import { CoreBusinessProcess } from "./CoreBusinessProcess";
// import { Glossary } from "./Glossary";

// 打印专用页面：把所有文档按顺序渲染到一个长页面里，用于导出 PDF。
// 每份文档之间用分页符隔开（break-after: always），保证每份文档从新页开始。
//
// 两种访问方式：
//   1. 从 IndexPage 点"导出 PDF"按钮 → 带 state.print=true 跳转 → 自动弹打印对话框
//   2. 直接访问 /print-all → 仅预览，不自动打印（用户可手动 Ctrl+P）

// 文档间分页符
function PageBreak() {
  return (
    <div
      style={{
        breakAfter: "always",
        pageBreakAfter: "always",
        height: 0,
      }}
    />
  );
}

export function PrintAllPage() {
  const navigate = useNavigate();
  const location = useLocation();

  // 从 IndexPage 带 state.print=true 跳转来时，等渲染完后自动触发打印
  const shouldAutoPrint = (location.state as { print?: boolean } | null)?.print === true;

  useEffect(() => {
    if (!shouldAutoPrint) return;
    // 等 DOM 渲染完（多文档连排需要时间），延迟触发打印
    const timer = setTimeout(() => {
      window.print();
    }, 800);
    return () => clearTimeout(timer);
  }, [shouldAutoPrint]);

  return (
    <div className="print-all">
      {/* 预览工具栏：只在屏幕显示，打印时隐藏 */}
      <div
        className="no-print"
        style={{
          position: "sticky",
          top: 0,
          zIndex: 100,
          display: "flex",
          gap: "var(--ra-space-3, 0.75rem)",
          alignItems: "center",
          padding: "var(--ra-space-2, 0.5rem) var(--ra-space-4, 1rem)",
          background: "var(--ra-color-bg, #fff)",
          borderBottom: "1px solid var(--ra-color-border, #ddd)",
          marginBottom: "var(--ra-space-4, 1rem)",
        }}
      >
        <button
          onClick={() => navigate("/")}
          style={{
            padding: "0.25rem 0.75rem",
            border: "1px solid var(--ra-color-border, currentColor)",
            borderRadius: "var(--ra-radius-md, 0.25rem)",
            background: "transparent",
            color: "var(--ra-color-fg, inherit)",
            cursor: "pointer",
          }}
        >
          ← 返回首页
        </button>
        <button
          onClick={() => window.print()}
          style={{
            padding: "0.25rem 0.75rem",
            border: "1px solid var(--ra-color-border, currentColor)",
            borderRadius: "var(--ra-radius-md, 0.25rem)",
            background: "transparent",
            color: "var(--ra-color-fg, inherit)",
            cursor: "pointer",
          }}
        >
          打印 / 另存为 PDF
        </button>
        <span style={{ fontSize: "var(--ra-text-sm, 0.875rem)", color: "var(--ra-color-muted, inherit)" }}>
          预览模式：所有文档连排。点"打印"后在对话框选"另存为 PDF"。
        </span>
      </div>

      {/* Agent 按 IndexPage DOCS 数组的顺序，导入并渲染所有文档页面组件。
          每份文档之间加 <PageBreak /> 分页。
          文档页面组件自带 ThemeProvider + Article + Hero + Colophon，无需额外包裹。

          复杂项目按业务域拆分多份文档时，建议按域分组排列（用注释分隔），
          跨域总览文档放最后（与首页 DOCS 数组顺序一致）。示例（取消注释并改实际组件名）：

          // ── 综合域 ──
          <BusinessOverview /><PageBreak />
          <DomainModel /><PageBreak />
          <Glossary /><PageBreak />
          // ── 采购域 ──
          <ProcurementFlow /><PageBreak />
          // ── 销售域 ──
          <SalesFlow /><PageBreak />
          // ── 跨域总览（放最后）──
          <CrossDomainOverview /><PageBreak />
      */}

      <SampleDoc />
      <PageBreak />

      {/* Agent 添加更多文档，例如：
      <BusinessOverview />
      <PageBreak />
      <DomainModel />
      <PageBreak />
      <CoreBusinessProcess />
      <PageBreak />
      <Glossary />
      <PageBreak />
      */}

      {/* 打印说明 */}
      <Raw title="">
        <p
          style={{
            fontSize: "var(--ra-text-sm, 0.875rem)",
            color: "var(--ra-color-muted, inherit)",
            textAlign: "center",
            marginTop: "var(--ra-space-4, 1rem)",
          }}
        >
          — 文档结束 —
        </p>
      </Raw>
    </div>
  );
}
