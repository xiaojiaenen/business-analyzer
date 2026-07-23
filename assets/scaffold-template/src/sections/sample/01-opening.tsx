import { Section, Aside, Raw } from "reacticle";
import { MermaidDiagram } from "../../components/MermaidDiagram";

// 一个 Section = 一个文件（铁律）。
// Sections 按文档分组：src/sections/<doc-name>/NN-*.tsx
// 每个 Section 导出一个组件，由对应的 Page 组件 import 并排列。
export function SectionOpening() {
  // 状态机图：业务文档里最常用的图型之一。
  // 用 stateDiagram-v2 而非 flowchart——状态机节点更克制，配合 mermaid-overrides.css
  // 的胶囊形圆角，视觉上跟 reacticle 衬线主题更协调。
  const stateGraph = `
stateDiagram-v2
  [*] --> pending: 用户提交
  pending --> paid: 支付成功
  pending --> cancelled: 超时取消
  paid --> shipped: 仓库发货
  shipped --> completed: 用户签收
  paid --> refunding: 申请退款
  refunding --> refunded: 退款到账
  completed --> [*]
  cancelled --> [*]
  refunded --> [*]
`;

  return (
    <Section index="01" title="第一节">
      <p>正文段落用 children —— 这应是文章主体，尽量多写正文，把背景、推理、结论讲清楚。</p>
      <p>再写一段，保持阅读节奏。语义组件只在内容确实"是"那个结构时才用。</p>

      <Aside tone="principle" label="核心判断">
        一句话的核心判断，给本节点睛。
      </Aside>

      <Raw title="为本段现写的内联 SVG（用主题 token 取色）">
        <svg viewBox="0 0 240 60" width="100%">
          <polyline
            points="0,50 40,42 80,46 120,20 160,28 200,8 240,14"
            fill="none"
            stroke="var(--ra-color-accent)"
            strokeWidth="2"
          />
        </svg>
      </Raw>

      <Raw title="Mermaid 状态机图（跟随主题 token，离线渲染）">
        <MermaidDiagram graph={stateGraph} />
        <div style={{
          fontSize: "var(--ra-text-sm)",
          color: "var(--ra-color-muted)",
          marginTop: "var(--ra-space-2)",
        }}>▲ 订单生命周期状态迁移。正常路径：待支付→已支付→已发货→已完成；异常路径：取消 / 退款。</div>
      </Raw>
    </Section>
  );
}
