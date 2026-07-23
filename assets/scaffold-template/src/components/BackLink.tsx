import { Link } from "react-router-dom";

type BackLinkProps = {
  // 传 domain 时，返回首页对应业务域分组锚点，文案显示域归属
  // 例如 <BackLink domain="采购域" /> → "← 返回采购域文档导航"，跳转 /#domain-采购域
  domain?: string;
};

// 返回文档导航链接。IndexPage 不使用此组件（它自己就是首页）。
// 多业务域文档（如"采购域业务流程"）应传 domain，让读者返回时直接定位到所在域分组。
export function BackLink({ domain }: BackLinkProps) {
  const to = domain ? `/#domain-${domain}` : "/";
  const label = domain
    ? `← 返回${domain}文档导航`
    : "← 返回文档导航";
  return (
    <nav
      style={{
        marginBottom: "var(--ra-space-4, 1rem)",
        fontSize: "var(--ra-text-sm, 0.875rem)",
      }}
    >
      <Link
        to={to}
        style={{
          color: "var(--ra-color-muted, inherit)",
          textDecoration: "none",
          display: "inline-flex",
          alignItems: "center",
          gap: "0.3em",
        }}
      >
        {label}
      </Link>
    </nav>
  );
}
