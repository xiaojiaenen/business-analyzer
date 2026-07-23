# Harness 视角

本 Skill 的重点不是"提示词"，而是一个小型 harness。它要回答六个问题：

| Harness 部分 | 本 Skill 解决的问题 | 设计手段 |
|---|---|---|
| 上下文管理 | 模型到底看到了什么 | 代码扫描结果统一写 `analysis/business-knowledge.md`，阶段化读取 reference |
| 工具系统 | 能处理什么输入 / 输出 | 代码仓库 / 数据库 Schema / 本地构建 / 浏览器检查 |
| 执行编排 | 下一步该做什么 | 分 Phase、检查点、首屏样张、完整生成、验收修复 |
| 状态与记忆 | 决策如何跨步骤保持 | `analysis/business-knowledge.md`、`plan/plan.md`（Brief/Outline/Theme/Assets 四段合一）、`review/first-spread-review.md`、`review/final-review.md` |
| 评估与观测 | 怎么知道文章好不好 | Plan 主 Agent 内联自查；First Spread / Final 用 SubAgent + 写文件；Section 用 SubAgent + 消息返回 |
| 约束与恢复 | 跑偏后怎么修 | 最小切片修复，禁止整篇无脑重写 |

## 状态文件是长期记忆

Agent **不应依赖聊天上下文记住关键决策**。跨阶段决策落盘到下列文件 —— 比原先精简了 ~5 份：

```text
analysis/business-knowledge.md  # Phase 2 分析笔记（事实底座，Phase 4 写文档时读它）
plan/plan.md                     # 唯一规划文件：Brief / Outline / Theme / Assets 四段合一
review/first-spread-review.md    # First Spread SubAgent 结论（首屏验收依据）
review/final-review.md           # 终审三视角结论（交付物的一部分）
review/repair-log.md             # 仅有修复时
```


长会话中如果不确定某个已确认的决策，**回读这些文件**，不要凭记忆重新发明。

## 一句话定位

> Business Analyzer 把代码仓库和数据库编辑成一套面向零基础读者的精美 HTML 业务文档；
> 它首先是**业务文档**，不是网页应用。交互、Raw、配图都服务业务理解。
