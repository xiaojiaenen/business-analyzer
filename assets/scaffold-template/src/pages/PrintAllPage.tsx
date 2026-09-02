import { useEffect } from "react";
import { Raw } from "reacticle";
import { useNavigate, useLocation } from "react-router-dom";
import { BusinessOverview } from "./BusinessOverview";
import { DomainModel } from "./DomainModel";
import { MesProcess } from "./MesProcess";
import { WmsProcess } from "./WmsProcess";
import { VmiProcess } from "./VmiProcess";
import { CrossDomainFlow } from "./CrossDomainFlow";
import { BusinessRules } from "./BusinessRules";
import { RolesAndPermissions } from "./RolesAndPermissions";
import { Glossary } from "./Glossary";
import { SystemArchitecture } from "./SystemArchitecture";
import { StateMachine } from "./StateMachine";
import { BpmDomain } from "./BpmDomain";
import { PlatformDomain } from "./PlatformDomain";
import { AuxDomain } from "./AuxDomain";

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
    // 打印时机：不能固定延时——14 份文档 + 36 张 Mermaid 图是异步渲染的，
    // 固定 1.5s 很可能图还没画出来，打印/导出 PDF 就是空白。
    // 改为轮询等待：14 个 .ra-root 都出现 + 所有 .mermaid-wrapper 都 data-mermaid-ready
    // （ready 或 error 均可），最多等 30s，然后才 window.print()。
    let cancelled = false;
    let tries = 0;
    const tryPrint = () => {
      if (cancelled) return;
      const roots = document.querySelectorAll(".ra-root").length;
      const wrappers = document.querySelectorAll(".mermaid-wrapper").length;
      const readyWrappers = document.querySelectorAll(
        '.mermaid-wrapper[data-mermaid-ready="ready"], .mermaid-wrapper[data-mermaid-ready="error"]'
      ).length;
      const done =
        roots >= 14 && (wrappers === 0 || readyWrappers === wrappers);
      if (done || tries >= 60) {
        // 给浏览器最后一帧绘制的机会，再弹打印框
        requestAnimationFrame(() => {
          if (!cancelled) window.print();
        });
        return;
      }
      tries += 1;
      setTimeout(tryPrint, 500);
    };
    const timer = setTimeout(tryPrint, 400);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
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
          预览模式：所有文档连排（14 份）。点"打印"后在对话框选"另存为 PDF"。
        </span>
      </div>

      {/* ── 综合域 ── */}
      <BusinessOverview />
      <PageBreak />
      <DomainModel />
      <PageBreak />
      <CrossDomainFlow />
      <PageBreak />
      <Glossary />
      <PageBreak />
      <SystemArchitecture />
      <PageBreak />
      <StateMachine />
      <PageBreak />
      <BusinessRules />
      <PageBreak />

      {/* ── 制造执行域 ── */}
      <MesProcess />
      <PageBreak />

      {/* ── 仓储物流域 ── */}
      <WmsProcess />
      <PageBreak />

      {/* ── 供应商库存域 ── */}
      <VmiProcess />
      <PageBreak />

      {/* ── 流程审批域 ── */}
      <BpmDomain />
      <PageBreak />

      {/* ── 平台底座域 ── */}
      <RolesAndPermissions />
      <PageBreak />
      <PlatformDomain />
      <PageBreak />

      {/* ── 辅助域 ── */}
      <AuxDomain />

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
