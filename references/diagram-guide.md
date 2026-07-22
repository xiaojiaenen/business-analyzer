# 图表指南 · 业务流程可视化

本文档是 Phase 2.2（业务流程提取）和 Phase 4（HTML 渲染）的图表工具箱。业务文档里最需要"一眼就懂"的内容——流程图、状态机、泳道、实体关系——这里提供从数据到图表的完整方案。

## 什么时候用什么图

| 业务场景 | 图表类型 | 来源 |
|---------|---------|------|
| 端到端用户操作链路（单角色） | **流程图** | Mermaid `flowchart` 或 SVG 模板 |
| 多角色协作流程 | **泳道图** | SVG 泳道模板 |
| ENUM 字段的状态流转 | **状态迁移图** | Mermaid `stateDiagram` 或 SVG 状态图 |
| 实体之间的调用/数据流 | **时序图** | Mermaid `sequenceDiagram` |
| 实体和关系总览 | **ER 图** | Mermaid `erDiagram` |

---

## 方案 A · Mermaid.js（首选，表现力最强）

Mermaid 用文本描述画图，在 Raw 块里引入 mermaid CDN + `<div class="mermaid">` 即可。

### 完整示例：在 Raw 块里嵌入 Mermaid

```tsx
<Raw title="订单生命周期">
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
    mermaid.initialize({ startOnLoad: true, theme: 'neutral' });
  </script>
  <div className="mermaid">
    stateDiagram-v2
    [*] --> pending: 用户提交订单
    pending --> paid: 支付成功
    pending --> cancelled: 超时/用户取消
    paid --> shipped: 仓库发货
    shipped --> completed: 用户签收
    paid --> refunding: 用户申请退款
    refunding --> refunded: 退款到账
    cancelled --> [*]
    completed --> [*]
    refunded --> [*]
  </div>
  <div style={{
    fontSize: 'var(--ra-text-sm)',
    color: 'var(--ra-color-muted)',
    marginTop: 'var(--ra-space-2)',
  }}>▲ 订单状态迁移图。正常路径：待支付→已支付→已发货→已完成。</div>
</Raw>
```

### Mermaid 主题匹配

Mermaid 的 `theme` 参数要和文章主题协调：

| 文章主题 | Mermaid theme | 效果 |
|---------|--------------|------|
| `tufte` / `press` | `neutral` | 低饱和、线条为主 |
| `vignelli` | `neutral` | 冷中性 |
| `shannon` / `fuller` | `dark` | 暗底适配 |
| `freddie` / `andy` | `base` | 温暖、圆角 |

### 流程图语法速查

```
flowchart TD
  A[用户浏览商品] --> B{库存充足?}
  B -->|是| C[锁定库存]
  B -->|否| D[提示缺货]
  C --> E[创建订单]
  E --> F[发起支付]
  F -->|成功| G[订单已支付]
  F -->|失败| H[订单待支付]
  H -->|30分钟超时| I[自动取消]
```

节点形状：`[矩形]` `(圆角)` `{菱形判断}` `((圆形))` `[[子程序]]` `[(数据库)]`

### 时序图语法速查

```
sequenceDiagram
  actor 用户
  participant 系统
  participant 支付网关
  用户->>系统: 提交订单
  系统->>系统: 校验库存
  系统->>支付网关: 发起支付请求
  支付网关-->>系统: 支付结果回调
  系统-->>用户: 显示支付结果
```

### ER 图语法速查

```
erDiagram
  USER ||--o{ ORDER : "创建"
  ORDER ||--|{ ORDER_ITEM : "包含"
  ORDER_ITEM }|--|| PRODUCT : "引用"
  ORDER ||--|| PAYMENT : "对应"
```

### 离线使用 Mermaid

业务文档交付物是离线 HTML。Mermaid 从 CDN 加载只在开发时有效。离线方案：

**方案 1**：构建前将 mermaid 打包进 HTML。在 `index.html` 的 `<head>` 中：

```html
<script type="importmap">
{ "imports": { "mermaid": "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs" } }
</script>
```

`vite-plugin-singlefile` 会自动将 importmap 引用的 CDN 资源内联到输出的单文件 HTML。

**方案 2**：如果 `vite-plugin-singlefile` 不支持 importmap 内联，改用方案 B（纯 SVG）。

---

## 方案 B · 内联 SVG 模板（零依赖，100% 离线）

当不需要 Mermaid 的复杂表现力，或者环境不支持 importmap 时，直接用 Raw 块手写 SVG。

### B1 · 水平流程图（3-5 步骤）

```tsx
<Raw title="用户注册流程">
  <svg viewBox="0 0 720 120" width="100%" style="max-width:720px;display:block;">
    {[
      { label: '填写信息', x: 20 },
      { label: '邮箱验证', x: 200 },
      { label: '设置密码', x: 380 },
      { label: '完成注册', x: 560 },
    ].map((step, i, arr) => (
      <>
        <rect x={step.x} y="30" width="130" height="44" rx="6"
          fill="var(--ra-color-surface)" stroke="var(--ra-color-border)" strokeWidth="1.5"/>
        <text x={step.x + 65} y="57" textAnchor="middle"
          fill="var(--ra-color-fg)" fontFamily="var(--ra-font-body)" fontSize="14">{step.label}</text>
        {i < arr.length - 1 && (
          <line x1={step.x + 150} y1="52" x2={step.x + 190} y2="52"
            stroke="var(--ra-color-accent)" strokeWidth="1.5"
            markerEnd="url(#arrow)"/>
        )}
      </>
    ))}
    <defs>
      <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <path d="M0,0 L10,5 L0,10 Z" fill="var(--ra-color-accent)"/>
      </marker>
    </defs>
  </svg>
  <div style={{fontSize:'var(--ra-text-sm)',color:'var(--ra-color-muted)',marginTop:'var(--ra-space-2)'}}>
    ▲ 用户注册四步流程
  </div>
</Raw>
```

### B2 · 状态迁移图

```tsx
<Raw title="订单状态迁移">
  <svg viewBox="0 0 600 300" width="100%" style="max-width:600px;display:block;">
    {[
      { id: 'pending', label: '待支付', x: 240, y: 20, fill: 'var(--ra-color-surface)' },
      { id: 'paid', label: '已支付', x: 400, y: 120, fill: 'var(--ra-color-surface)' },
      { id: 'shipped', label: '已发货', x: 400, y: 240, fill: 'var(--ra-color-surface)' },
      { id: 'completed', label: '已完成', x: 240, y: 260, fill: 'var(--ra-color-accent-muted)' },
      { id: 'cancelled', label: '已取消', x: 30, y: 120, fill: 'var(--ra-color-risk-muted)' },
    ].map(node => (
      <>
        <rect x={node.x} y={node.y} width="100" height="36" rx="18"
          fill={node.fill} stroke="var(--ra-color-border)" strokeWidth="1"/>
        <text x={node.x + 50} y={node.y + 23} textAnchor="middle"
          fill="var(--ra-color-fg)" fontFamily="var(--ra-font-body)" fontSize="13">{node.label}</text>
      </>
    ))}
    {/* 箭头：pending→paid, paid→shipped, shipped→completed, pending→cancelled */}
    <line x1="290" y1="56" x2="390" y2="120" stroke="var(--ra-color-accent)" strokeWidth="1.2" markerEnd="url(#arrow2)"/>
    <line x1="450" y1="156" x2="450" y2="230" stroke="var(--ra-color-accent)" strokeWidth="1.2" markerEnd="url(#arrow2)"/>
    <line x1="400" y1="260" x2="340" y2="270" stroke="var(--ra-color-accent)" strokeWidth="1.2" markerEnd="url(#arrow2)"/>
    <line x1="240" y1="56" x2="140" y2="120" stroke="var(--ra-color-risk)" strokeWidth="1.2" markerEnd="url(#arrow2-risk)"/>
    <defs>
      <marker id="arrow2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <path d="M0,0 L10,5 L0,10 Z" fill="var(--ra-color-accent)"/>
      </marker>
      <marker id="arrow2-risk" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <path d="M0,0 L10,5 L0,10 Z" fill="var(--ra-color-risk)"/>
      </marker>
    </defs>
  </svg>
</Raw>
```

### B3 · 泳道图（多角色流程）

```tsx
<Raw title="退款流程 · 泳道图">
  <svg viewBox="0 0 700 360" width="100%" style="max-width:700px;display:block;">
    {/* 泳道背景 */}
    {['用户', '系统', '支付网关'].map((lane, i) => (
      <>
        <rect x="0" y={i * 120 + 40} width="700" height="110"
          fill={i % 2 === 0 ? 'var(--ra-color-surface)' : 'transparent'}
          stroke="var(--ra-color-border)" strokeWidth="0.5" strokeDasharray="4,2"/>
        <text x="12" y={i * 120 + 62} fontSize="13" fontWeight="600"
          fill="var(--ra-color-muted)" fontFamily="var(--ra-font-body)">{lane}</text>
      </>
    ))}
    {/* 步骤节点 */}
    {[
      { label: '申请退款', lane: 0, x: 30 },
      { label: '校验退款条件', lane: 1, x: 170 },
      { label: '调用退款接口', lane: 1, x: 350 },
      { label: '处理退款', lane: 2, x: 530 },
      { label: '退款到账通知', lane: 0, x: 530 },
    ].map((step, i, arr) => (
      <>
        <rect x={step.x} y={step.lane * 120 + 65} width="110" height="36" rx="6"
          fill="var(--ra-color-surface)" stroke="var(--ra-color-accent)" strokeWidth="1.2"/>
        <text x={step.x + 55} y={step.lane * 120 + 88} textAnchor="middle"
          fill="var(--ra-color-fg)" fontFamily="var(--ra-font-body)" fontSize="12">{step.label}</text>
        {i < arr.length - 1 && (
          <line x1={step.x + 110} y1={step.lane * 120 + 83}
                x2={arr[i + 1].x - 10} y2={arr[i + 1].lane * 120 + 83}
                stroke="var(--ra-color-accent)" strokeWidth="1.2" markerEnd="url(#arrow3)"/>
        )}
      </>
    ))}
    <defs>
      <marker id="arrow3" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
        <path d="M0,0 L10,5 L0,10 Z" fill="var(--ra-color-accent)"/>
      </marker>
    </defs>
  </svg>
</Raw>
```

---

## 方案 C · 从 ENUM 自动推导状态迁移图

当 `analyze-schema.py` 发现 ENUM 字段时（如 `status ENUM('pending','paid','shipped','completed','cancelled')`），按以下规则推导状态图：

### 推导规则

1. **ENUM 值的顺序是业务流程的大致顺序**：第一个值通常是初始态，最后一个值通常是终态
2. **包含 `cancel` / `fail` / `reject` / `error` 的值** → 异常终止路径（用红色/虚线箭头）
3. **包含 `ing` / `progress` 的值** → 中间态
4. **包含 `done` / `complete` / `success` / `finish` 的值** → 正常终态
5. **字段名 + ENUM** 的组合给出状态名称（如 `order_status` 的 `pending` → "订单待支付"）

### 推导示例

输入：字段 `order_status`，ENUM `('pending','paid','shipped','completed','cancelled','refunding','refunded')`

推导结果：

```
正常路径:    pending → paid → shipped → completed
异常路径 1:  pending → cancelled
异常路径 2:  paid → refunding → refunded
终态:       completed, cancelled, refunded
```

### 在 Phase 2.0 中自动触发

`analyze-schema.py` 输出的 `summary.json` 中，每个有 ENUM 状态字段的实体都会带 `stateMachine` 字段：

```json
{
  "entities": [{
    "name": "orders",
    "statusColumns": [{
      "name": "status",
      "type": "enum('pending','paid','shipped','completed','cancelled','refunding','refunded')",
      "derivedStateMachine": {
        "initialState": "pending",
        "normalPath": ["pending","paid","shipped","completed"],
        "exceptionPaths": [
          {"from": "pending", "to": "cancelled", "reason": "取消"},
          {"from": "paid", "to": "refunding", "reason": "退款"},
          {"from": "refunding", "to": "refunded", "reason": "退款完成"}
        ],
        "terminalStates": ["completed","cancelled","refunded"]
      }
    }]
  }]
}
```

Phase 4 渲染时，agent 读取 `derivedStateMachine`，用方案 A（Mermaid stateDiagram）或方案 B2（SVG 状态图）渲染。

---

## 图表颜色规范

所有图表必须使用 `--ra-*` CSS 变量，切换主题时自动适配：

| 语义 | CSS 变量 | 用途 |
|------|---------|------|
| 主色 / 强调 | `var(--ra-color-accent)` | 正常流程箭头、节点边框、高亮 |
| 前景 / 文字 | `var(--ra-color-fg)` | 节点文字 |
| 背景 / 面板 | `var(--ra-color-surface)` | 节点填充、泳道背景 |
| 边框 / 参考线 | `var(--ra-color-border)` | 分隔线、辅助线 |
| 弱化文字 | `var(--ra-color-muted)` | 图例、标注、caption |
| 风险 / 异常 | `var(--ra-color-risk)` | 异常路径、取消、失败节点 |
| 成功 / 确认 | `var(--ra-color-accent-muted)` | 终态节点填充 |

---

## Phase 4 渲染决策树

```
有 ENUM 状态字段？
├── 是 → 用 derivedStateMachine 生成状态迁移图
│        ├── 在线开发 → 方案 A（Mermaid stateDiagram）
│        └── 离线交付 → 方案 B2（SVG 状态图）
│
有明确端到端用户操作？
├── 是，单角色 → 流程图
│   ├── 步骤 ≤ 5 → 方案 B1（水平 SVG 流程图）
│   └── 步骤 > 5 或有分支 → 方案 A（Mermaid flowchart）
│
├── 是，多角色 → 方案 B3（SVG 泳道图）
│
有实体间数据/调用流？
├── 是 → 方案 A（Mermaid sequenceDiagram）
│
实体 > 10 个需要关系总览？
└── 是 → 方案 A（Mermaid erDiagram）
```

---

## 核心提醒

- **图表是仆人不是主人**：每个图必须配一句 caption 解释"这张图说明了什么"
- **颜色只用 token**：写死 `#FF0000` 切换主题时图表不变色，等于废了主题系统
- **离线优先**：构建交付物时确保图表在断网下能看（用方案 B 内联 SVG 或方案 A 的 importmap 内联）
- **不只画图**：图表前后要有正文说明，读者不能只看到一张孤零零的图
- **ENUM 是自动化的入口**：`analyze-schema.py` 发现 ENUM 后自动推导状态机，不需要 agent 手动分析
