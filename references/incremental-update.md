# 增量更新 · 代码变更后如何只更新受影响的文档

> 本文档是 Phase 5「交付与维护」的操作手册——用户改了代码后，如何用 git diff 驱动，
> 只更新受影响的文档，而不是全量重跑。

## 核心思路

**用 git diff 看用户改了什么 → 映射到受影响的业务知识维度 → 只重写受影响的文档。**

不全量重跑 Phase 2/3/4。增量更新只做三件事：
1. 读 git diff，判断改了什么业务
2. 对照 `business-knowledge.md` 找出哪些维度受影响
3. 只重写受影响的 Section 文件 + 重新 build

---

## Step 1 · 读取变更（git diff 驱动）

### 有 git 仓库的项目（首选）

```bash
# 看自上次文档生成以来的变更（用户上次交付时打过 tag 或记住 commit）
git log --oneline <上次交付的 commit>..HEAD
git diff --stat <上次交付的 commit>..HEAD        # 变更文件概览
git diff <上次交付的 commit>..HEAD -- '*.java'    # 具体语言变更
```

**如果不知道上次交付的 commit**：
```bash
# 看 business-knowledge.md 的最后修改时间，找最近的 commit
git log -1 --format="%H %ci" -- business-docs/analysis/business-knowledge.md
# 或看 dist/ 的构建时间反推
```

### 无 git 仓库的项目

让用户口述"改了哪些功能/文件"，或对比 `business-knowledge.md` 落盘时间后的文件修改时间：
```bash
# Windows
Get-ChildItem -Path <project> -Recurse -File | Where-Object { $_.LastWriteTime -gt "<business-knowledge.md 的修改时间>" }
# Linux/Mac
find <project> -type f -newer business-docs/analysis/business-knowledge.md -not -path "*/business-docs/*"
```

---

## Step 2 · 变更 → 业务维度 → 文档 映射

读 diff 内容，按下表判断哪些业务维度受影响、哪些文档要更新：

| 代码变更类型 | 怎么识别 | 受影响维度 | 要更新的文档 |
|------------|---------|-----------|------------|
| 新增/改实体字段 | model/entity/struct/CREATE TABLE 变更 | 业务实体、核心概念 | 领域模型、业务全景图 |
| 新增/改状态值 | ENUM/const 变更、status 字段 | 状态机、业务流程 | 状态机手册、核心业务流程 |
| 新增/改状态迁移 | setStatus/updateStatus/状态校验变更 | 状态机、业务流程 | 状态机手册、核心业务流程 |
| 新增 API/入口 | 新路由、新 CLI 命令、新 MQ consumer | 业务能力、入口点 | 业务全景图、系统架构 |
| 新增/改业务规则 | validate/check/if 条件变更 | 业务规则 | 业务规则手册 |
| 新增/改角色权限 | role/permission/middleware 变更 | 用户角色 | 角色与权限 |
| 新增外部依赖 | 新外部 API 调用、新 MQ topic | 系统边界 | 系统架构 |
| 新增/改术语 | 新业务概念出现 | 关键概念 | 关键概念词汇表 |
| 新增子流程 | 新 service + 新状态流转 | 业务流程 | 核心业务流程 |

**判断原则**：
- diff 只动了注释/格式/重构（不改业务逻辑）→ **不用更新任何文档**
- diff 动了业务逻辑 → 按上表找受影响文档
- 不确定是否影响业务 → 先更新 `business-knowledge.md` 对应段落，再看是否要改文档

---

## Step 3 · 执行增量更新

### 3.1 先更新分析笔记

```
读 git diff
  → 对照 business-knowledge.md 找到对应段落
  → 更新受影响的段落（标注 [增量更新 YYYY-MM-DD]）
  → 不动其他段落
```

### 3.2 再更新受影响的文档

只改受影响的 Section 文件，不碰其他 Section：

```
受影响文档 = 领域模型
  → 读 src/pages/DomainModel.tsx 确认结构
  → 读 src/sections/domain-model/*.tsx 找到对应 section
  → 只改受影响的 section 文件
  → 不动其他 section
```

**禁止**：
- 重写整个 Page 组件（除非新增了整个文档）
- 改不受影响的 Section 文件
- 重跑 Phase 2 全量分析

### 3.3 重新构建

```bash
npm run build
```

只构建一次，所有文档（改过的和没改的）都在同一个 dist/index.html。

---

## Step 4 · 交付说明

告诉用户：
- 改了哪些文档的哪些 section（具体到文件名）
- 为什么其他文档不用改（基于 git diff 判断）
- `business-knowledge.md` 更新了哪些段落

---

## 常见增量场景

### 场景 1：新增一个业务流程

```
git diff 显示：新增 OrderRefundService + refund_status ENUM + POST /api/orders/{id}/refund
  → 受影响：业务流程（新增退款子流程）、状态机（订单加 refunding/refunded）、入口点、业务规则
  → 更新：核心业务流程（加退款 section）、状态机手册（加退款状态）、业务全景图（能力树加退款）
  → 不动：领域模型（没新实体）、角色权限（没新角色）
```

### 场景 2：改了一个业务规则阈值

```
git diff 显示：if (amount > 5000) → if (amount > 10000)
  → 受影响：业务规则 BR-001
  → 更新：业务规则手册（改 BR-001 阈值）
  → 不动：其他所有文档
```

### 场景 3：纯技术重构

```
git diff 显示：OrderService 拆成 OrderCreateService + OrderQueryService，无业务逻辑变化
  → 受影响：无（代码结构变了，业务没变）
  → 不更新任何文档
  → 告诉用户：本次变更是技术重构，业务文档无需更新
```

---

## 判断：增量更新够了没？

- [ ] 读了 git diff（或用户口述的变更）
- [ ] 对照映射表识别了所有受影响的维度
- [ ] `business-knowledge.md` 受影响段落已更新
- [ ] 受影响文档的对应 Section 已更新
- [ ] 不受影响的文档/Section 未被改动
- [ ] `npm run build` 成功
- [ ] 向用户说明了改了什么、为什么没改其他的
