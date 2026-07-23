import { useState, useMemo } from "react";
import { ThemeProvider, Article, Hero, Lead, Section, Raw } from "reacticle";
import { Link, useNavigate } from "react-router-dom";
import { Colophon } from "../components/Colophon";

const THEME = "press";

// === 分析模式（Agent 维护：Checkpoint 0 选定后填入）===
// "A" = 重点深挖（核心 5-10 概念深挖，非核心带过，3 小时可读完）
// "B" = 全量深挖（每个业务都深挖，不漏任何细节，可能 50+ 页）
const ANALYSIS_MODE: "A" | "B" = "A";
const ANALYSIS_MODE_LABEL = ANALYSIS_MODE === "A" ? "重点深挖" : "全量深挖";

// 文档导航首页。
// D1: DocCard 支持按业务域分组（domain 字段），文档多时按域分区而非平铺。
// D2: 跨文档搜索框——输入关键词，实时过滤所有 DocCard（匹配 title/desc/domain）。
// D3: 跨域总览文档用 kind: "overview" 标记，DocCard 显示徽章并置顶。
// D4: 域分组带锚点 id，BackLink 可跳回所在域。
// Agent 在 Section "文档列表" 中添加更多 <DocGroup domain="..."> 或 <DocCard />。

// === 文档注册表（Agent 维护：每新增文档在此加一条）===
type DocEntry = {
  to: string;
  title: string;
  desc: string;
  domain?: string; // 业务域名，如"交易域""商品域"；不填归到"综合"
  kind?: "overview" | "domain-flow" | "normal"; // overview=跨域总览（置顶+徽章），domain-flow=域流程，normal=普通
  related?: { to: string; label: string }[];
};

const DOCS: DocEntry[] = [
  {
    to: "/sample",
    title: "示例文档",
    desc: "脚手架自带的示例页面，展示文档结构、主题和组件用法。",
    domain: "综合",
    kind: "normal",
    related: [{ to: "/sample", label: "示例" }],
  },
  // Agent 在此添加文档，例如：
  // { to: "/business-overview", title: "业务全景图", desc: "...", domain: "综合", kind: "normal",
  //   related: [{ to: "/domain-model", label: "领域模型" }] },
  // { to: "/domain-model", title: "领域模型", desc: "...", domain: "综合", kind: "normal" },
  // { to: "/sales-flow", title: "销售域业务流程", desc: "...", domain: "销售域", kind: "domain-flow" },
  // { to: "/procurement-flow", title: "采购域业务流程", desc: "...", domain: "采购域", kind: "domain-flow" },
  // { to: "/cross-domain-overview", title: "跨域主线总览", desc: "...", domain: "综合", kind: "overview" },
];

// Agent 须按实际识别的业务域更新此数组（顺序即首页展示顺序，未列出的域排最后）
const DOMAIN_ORDER = ["综合", "交易域", "销售域", "采购域", "库存域", "用户域", "商品域"];

export function IndexPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  // 导出 PDF：跳转到 /print-all 预览页，传 state.print=true 触发自动打印
  const handleExportPdf = () => {
    navigate("/print-all", { state: { print: true } });
  };

  // 搜索过滤：匹配 title/desc/domain
  const filteredDocs = useMemo(() => {
    if (!query.trim()) return DOCS;
    const q = query.toLowerCase();
    return DOCS.filter(
      (d) =>
        d.title.toLowerCase().includes(q) ||
        d.desc.toLowerCase().includes(q) ||
        (d.domain || "").toLowerCase().includes(q)
    );
  }, [query]);

  // 按业务域分组；跨域总览（kind=overview）强制归入"综合"并置顶
  const grouped = useMemo(() => {
    const map = new Map<string, DocEntry[]>();
    for (const d of filteredDocs) {
      const dom = d.domain || "综合";
      if (!map.has(dom)) map.set(dom, []);
      map.get(dom)!.push(d);
    }
    // 每个域内：跨域总览置顶，其余按原顺序
    for (const docs of map.values()) {
      docs.sort((a, b) => {
        const ao = a.kind === "overview" ? 0 : 1;
        const bo = b.kind === "overview" ? 0 : 1;
        return ao - bo;
      });
    }
    // 按 DOMAIN_ORDER 排序域，未列出的域排最后
    const domains = Array.from(map.keys()).sort((a, b) => {
      const ia = DOMAIN_ORDER.indexOf(a);
      const ib = DOMAIN_ORDER.indexOf(b);
      return (ia === -1 ? 999 : ia) - (ib === -1 ? 999 : ib);
    });
    return domains.map((dom) => ({ domain: dom, docs: map.get(dom)! }));
  }, [filteredDocs]);

  return (
    <ThemeProvider theme={THEME}>
      <Article toc width="regular">
        <Hero
          title="项目业务文档"
          subtitle="零基础读者指南"
          meta={[
            { label: "日期", value: new Date().toISOString().slice(0, 10) },
            { label: "分析模式", value: ANALYSIS_MODE_LABEL },
          ]}
        />
        <Lead>
          这里是所有业务文档的导航入口。按推荐顺序阅读，从零开始理解项目。
          {ANALYSIS_MODE === "B" && "（全量深挖模式：每个业务都完整分析，文档较详尽）"}
        </Lead>

        {/* 导出 PDF 按钮：跳转 /print-all 预览所有文档连排，自动弹打印对话框 */}
        <div style={{ marginBottom: "var(--ra-space-3, 0.75rem)" }}>
          <button
            onClick={handleExportPdf}
            className="no-print"
            style={{
              padding: "var(--ra-space-2, 0.5rem) var(--ra-space-4, 1rem)",
              border: "1px solid var(--ra-color-border, currentColor)",
              borderRadius: "var(--ra-radius-md, 0.25rem)",
              background: "var(--ra-color-surface, transparent)",
              color: "var(--ra-color-fg, inherit)",
              fontSize: "var(--ra-text-sm, 0.875rem)",
              cursor: "pointer",
            }}
          >
            导出 PDF
          </button>
        </div>

        <Section index="01" title="推荐阅读顺序">
          <p>建议按以下顺序阅读，逐步深入：</p>
          <ol>
            <li>业务全景图 — 全局视角理解项目在做什么</li>
            <li>领域模型 — 核心实体和它们的关系</li>
            <li>核心业务流程 — 关键操作的端到端链路</li>
            <li>关键概念词汇表 — 术语速查</li>
          </ol>
        </Section>

        <Section index="02" title="文档列表">
          {/* D2: 跨文档搜索框 */}
          <Raw title="">
            <div style={{ marginBottom: "var(--ra-space-3, 0.75rem)" }}>
              <input
                type="text"
                placeholder="搜索文档（标题/描述/业务域）..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                style={{
                  width: "100%",
                  padding: "var(--ra-space-2, 0.5rem) var(--ra-space-3, 0.75rem)",
                  border: "1px solid var(--ra-color-border, currentColor)",
                  borderRadius: "var(--ra-radius-md, 0.25rem)",
                  fontSize: "var(--ra-text-base, 1rem)",
                  background: "var(--ra-color-surface, transparent)",
                  color: "var(--ra-color-fg, inherit)",
                  boxSizing: "border-box",
                }}
              />
              {query && (
                <div
                  style={{
                    fontSize: "var(--ra-text-sm, 0.875rem)",
                    color: "var(--ra-color-muted, inherit)",
                    marginTop: "var(--ra-space-1, 0.25rem)",
                  }}
                >
                  找到 {filteredDocs.length} 个文档
                </div>
              )}
            </div>
          </Raw>

          {/* D1: 按业务域分组展示，每组带锚点 id 供 BackLink 跳回 */}
          {grouped.length === 0 ? (
            <p style={{ color: "var(--ra-color-muted, inherit)" }}>
              没有匹配的文档。
            </p>
          ) : (
            grouped.map(({ domain, docs }) => (
              <div
                key={domain}
                id={`domain-${domain}`}
                style={{ marginBottom: "var(--ra-space-4, 1rem)" }}
              >
                <h3
                  style={{
                    fontSize: "var(--ra-text-lg, 1.125rem)",
                    fontWeight: 600,
                    marginBottom: "var(--ra-space-2, 0.5rem)",
                    paddingBottom: "var(--ra-space-1, 0.25rem)",
                    borderBottom: "1px solid var(--ra-color-border, currentColor)",
                  }}
                >
                  {domain}
                </h3>
                <div
                  style={{
                    display: "grid",
                    gap: "var(--ra-space-3, 0.75rem)",
                  }}
                >
                  {docs.map((doc) => (
                    <DocCard key={doc.to} {...doc} />
                  ))}
                </div>
              </div>
            ))
          )}
        </Section>

        <Colophon theme={THEME} />
      </Article>
    </ThemeProvider>
  );
}

function DocCard({ to, title, desc, kind, related }: DocEntry) {
  const isOverview = kind === "overview";
  return (
    <Link
      to={to}
      style={{
        display: "block",
        padding: "var(--ra-space-3, 0.75rem) var(--ra-space-4, 1rem)",
        border: "1px solid var(--ra-color-border, currentColor)",
        borderRadius: "var(--ra-radius-md, 0.25rem)",
        textDecoration: "none",
        color: "var(--ra-color-fg, inherit)",
        background: isOverview
          ? "var(--ra-color-surface-raised, rgba(0,0,0,0.03))"
          : "transparent",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--ra-space-2, 0.5rem)",
        }}
      >
        <div
          style={{
            fontWeight: 600,
            fontSize: "var(--ra-text-lg, 1.125rem)",
          }}
        >
          {title}
        </div>
        {isOverview && (
          <span
            style={{
              fontSize: "var(--ra-text-xs, 0.75rem)",
              padding: "0.1em 0.4em",
              border: "1px solid var(--ra-color-border, currentColor)",
              borderRadius: "var(--ra-radius-sm, 0.15rem)",
              color: "var(--ra-color-muted, inherit)",
              whiteSpace: "nowrap",
            }}
          >
            跨域总览
          </span>
        )}
      </div>
      <div
        style={{
          fontSize: "var(--ra-text-sm, 0.875rem)",
          color: "var(--ra-color-muted, inherit)",
          marginTop: "0.25rem",
        }}
      >
        {desc}
      </div>
      {related && related.length > 0 && (
        <div
          style={{
            display: "flex",
            gap: "var(--ra-space-2, 0.5rem)",
            flexWrap: "wrap",
            marginTop: "var(--ra-space-2, 0.5rem)",
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <span
            style={{
              fontSize: "var(--ra-text-xs, 0.75rem)",
              color: "var(--ra-color-muted, inherit)",
            }}
          >
            相关文档：
          </span>
          {related.map((r) => (
            <Link
              key={r.to}
              to={r.to}
              style={{
                fontSize: "var(--ra-text-xs, 0.75rem)",
                textDecoration: "underline",
              }}
            >
              {r.label}
            </Link>
          ))}
        </div>
      )}
    </Link>
  );
}
