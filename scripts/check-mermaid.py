#!/usr/bin/env python3
"""
check-mermaid.py —— 批量校验文档项目里所有 Mermaid 图的语法（Phase 4 质检用）

背景：Mermaid 图在浏览器里渲染失败时只显示"图表渲染失败"（MermaidDiagram 组件兜底），
作者不易察觉。本脚本用 Node + jsdom + mermaid.parse 离线批量解析所有 Section 文件中的
模板字符串图，提前暴露语法错误（尤其是节点标签含半角括号/特殊字符未加引号的问题）。

用法：
    # 在文档项目根目录（含 src/sections/）下运行
    node scripts/check-mermaid.mjs [--dir src/sections]
    # 或经 python 包装（自动生成临时 mjs 并执行）
    python scripts/check-mermaid.py [src/sections]

依赖：项目内已装 jsdom（scaffold 会装 mermaid；jsdom 需 `npm install --no-save jsdom`，
或用系统已存在的 jsdom）。

输出：PASS: N graphs / FAIL: M graphs + 每个失败图的文件与错误信息。
退出码：0=全部通过，1=有失败。

常见失败原因（务必在写图时避免）：
  1. 节点标签含半角圆括号：(  ) —— 必须用引号包裹，如 S1["状态: 待生产(10)"]；
  2. 节点标签含未转义的特殊字符（{} | : 等）—— 同样加引号；
  3. 中文标点混用导致解析歧义 —— 用「」替代字符串内的中文引号。
"""

import subprocess
import sys
import tempfile
import os
from pathlib import Path

MJS_TEMPLATE = r'''
import { JSDOM } from "jsdom";
import { readFileSync, readdirSync } from "fs";
import path from "path";

const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", { pretendToBeVisual: true });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
Object.defineProperty(globalThis, "navigator", { value: dom.window.navigator, configurable: true });

const mermaid = (await import("mermaid")).default;
mermaid.initialize({ startOnLoad: false, theme: "neutral", securityLevel: "loose" });

const sectionsDir = process.argv[2] || "src/sections";
const files = [];
function walk(dir) {
  for (const f of readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, f.name);
    if (f.isDirectory()) walk(p);
    else if (f.name.endsWith(".tsx") || f.name.endsWith(".md")) files.push(p);
  }
}
walk(sectionsDir);

let pass = 0, fail = 0;
const failures = [];
for (const file of files) {
  const src = readFileSync(file, "utf8");
  const regex = /`([\s\S]*?)`/g;
  let m;
  while ((m = regex.exec(src)) !== null) {
    const content = m[1];
    if (/-->|stateDiagram|flowchart|sequenceDiagram|graph TB|graph LR|graph RL/.test(content) && content.length > 30) {
      try {
        await mermaid.parse(content);
        pass++;
      } catch (e) {
        fail++;
        failures.push({ file, error: String(e.message || e).slice(0, 300) });
      }
    }
  }
}
console.log(`PASS: ${pass} graphs`);
console.log(`FAIL: ${fail} graphs`);
if (failures.length) {
  for (const f of failures) console.log(`\n--- ${f.file} ---\n${f.error}`);
}
process.exit(fail > 0 ? 1 : 0);
'''


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "src/sections"
    # 允许同时传入 mjs 路径或目录；统一转成 Node 脚本的目标目录参数
    target = target if target != "scripts/check-mermaid.py" else "src/sections"

    # 临时 mjs 必须写在项目目录内（cwd），否则 node 从系统 temp 目录
    # 无法解析项目 node_modules 里的 jsdom/mermaid。
    cwd = Path.cwd()
    tmp_mjs = cwd / f".check-mermaid-{os.getpid()}.mjs"
    tmp_mjs.write_text(MJS_TEMPLATE, encoding="utf-8")

    try:
        result = subprocess.run(
            ["node", str(tmp_mjs), target],
            capture_output=True, text=True,
            cwd=cwd,
        )
        print(result.stdout)
        if result.stderr:
            print("stderr:", result.stderr[-2000:], file=sys.stderr)
        sys.exit(result.returncode)
    finally:
        tmp_mjs.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
