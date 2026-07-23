#!/usr/bin/env python3
"""
scaffold.py — 创建文档项目工作区（单项目 SPA：Vite + React + TypeScript + reacticle + react-router）

用法：
  python scripts/scaffold.py <target-dir>
  python scripts/scaffold.py --list-themes

示例：
  python scripts/scaffold.py ./business-docs

所有文档页面共享一个项目，通过 HashRouter 路由切换。
每个页面自行声明主题（ThemeProvider），不再需要每份文档单独 scaffold。
"""

import argparse
import json
import os
import shutil
import sys

# Windows: 强制 stdout/stderr 使用 UTF-8，避免中文乱码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import subprocess
from pathlib import Path


def get_skill_dir() -> Path:
    """获取 skill 根目录"""
    return Path(__file__).resolve().parent.parent


def list_themes(profiles_path: Path):
    """列出所有可用主题"""
    if not profiles_path.exists():
        print(f"✗ 主题索引不存在: {profiles_path}")
        sys.exit(1)

    with open(profiles_path, "r", encoding="utf-8") as f:
        themes = json.load(f)

    print(f"可用主题（来自 {profiles_path}）：\n")
    for t in themes:
        print(f"  • {t['id']}")
        print(f"      {t['label']}")
        print(f"      {t['mood']}")
    print(f"\n主题在各页面组件内通过 <ThemeProvider theme=\"...\"> 声明，不同页面可用不同主题。")


def check_npm() -> bool:
    """检查 npm 是否可用"""
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    try:
        subprocess.run([npm_cmd, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def main():
    skill_dir = get_skill_dir()
    template_dir = skill_dir / "assets" / "scaffold-template"
    profiles_path = skill_dir / "references" / "themes" / "index.json"

    parser = argparse.ArgumentParser(
        description="创建文档项目工作区（单项目 SPA：Vite + React + TypeScript + reacticle + react-router）"
    )
    parser.add_argument("target", nargs="?", help="目标目录")
    parser.add_argument("--list-themes", action="store_true", help="列出可用主题")

    args = parser.parse_args()

    if args.list_themes:
        list_themes(profiles_path)
        return

    if not args.target:
        parser.print_help()
        print("\n请指定目标目录，例如: python scripts/scaffold.py ./business-docs")
        sys.exit(1)

    target = Path(args.target).resolve()

    # 检查目标目录
    if target.exists() and any(target.iterdir()):
        print(f"✗ 目标目录 '{target}' 已存在且非空，已中止。")
        sys.exit(1)

    # 检查 npm
    if not check_npm():
        print("✗ 需要 npm，但在 PATH 里没找到。")
        sys.exit(1)

    if not template_dir.exists():
        print(f"✗ 模板目录不存在: {template_dir}")
        sys.exit(1)

    print(f"▸ 在 {target} 创建文档项目")
    print(f"▸ 架构：单项目 SPA（HashRouter，所有文档共享一个项目）")
    print(f"▸ 主题：每页独立声明（IndexPage=press, SampleDoc=tufte）")
    print(f"▸ reacticle：从 npm 安装最新发布版")
    print(f"▸ business-analyzer by xiaojiaenen · https://github.com/xiaojiaenen/business-analyzer")

    # ── 创建目录结构 ──
    dirs = [
        "src/components",
        "src/pages",
        "src/sections/sample",
        "src/raw-blocks",
        "plan",
        "review",
        "analysis",
    ]
    for d in dirs:
        (target / d).mkdir(parents=True, exist_ok=True)

    # ── 复制工程模板文件 ──
    root_files = [
        "package.json", "vite.config.ts", "tsconfig.json",
        "tsconfig.node.json", "index.html", ".npmrc",
        "src/print-overrides.css",
        "src/mermaid-overrides.css",
    ]
    for filename in root_files:
        src = template_dir / filename
        if src.exists():
            dst = target / filename
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    # ── 复制 src/ 文件 ──
    src_files = [
        "src/main.tsx",
        "src/App.tsx",
        "src/components/Cover.tsx",
        "src/components/Colophon.tsx",
        "src/components/BackLink.tsx",
        "src/components/MermaidDiagram.tsx",
        "src/pages/IndexPage.tsx",
        "src/pages/SampleDoc.tsx",
        "src/pages/PrintAllPage.tsx",
        "src/sections/sample/01-opening.tsx",
    ]
    for filepath in src_files:
        src = template_dir / filepath
        if src.exists():
            dst = target / filepath
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    # gitkeep
    (target / "plan" / ".gitkeep").touch()
    (target / "review" / ".gitkeep").touch()
    (target / "analysis" / ".gitkeep").touch()

    # ── 安装依赖 ──
    os.chdir(target)
    print("▸ 安装依赖（含 reacticle 最新版，可能要等一会）...")

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    npm_base = [npm_cmd]
    registry = os.environ.get("NPM_REGISTRY", "")
    if registry:
        print(f"▸ 使用 registry: {registry}")
        npm_base.extend(["--registry", registry])

    subprocess.run([*npm_base, "install"], capture_output=True, check=False)
    subprocess.run([*npm_base, "install", "reacticle@latest"], capture_output=True, check=False)
    subprocess.run([*npm_base, "install", "mermaid"], capture_output=True, check=False)

    # 获取版本
    try:
        result = subprocess.run(
            ["node", "-e",
             "console.log(JSON.parse(require('fs').readFileSync("
             "'node_modules/reacticle/package.json','utf8')).version)"],
            capture_output=True, text=True, check=False
        )
        version = result.stdout.strip() or "?"
    except Exception:
        version = "?"
    print(f"▸ reacticle 版本：{version}")

    # typecheck
    print("▸ 跑一次 typecheck 确认接线 OK ...")
    try:
        npx_cmd = "npx.cmd" if sys.platform == "win32" else "npx"
        subprocess.run([npx_cmd, "tsc", "--noEmit"], check=True)
        print("✓ typecheck 通过")
    except subprocess.CalledProcessError:
        print("⚠ typecheck 有问题（见上），dev / build 仍可能正常 —— 请人工确认。")

    print(f"""
✓ 完成。文档项目：{target}

项目结构：
  {target}/
  ├── src/
  │   ├── main.tsx              # 入口（HashRouter + file:// 锚点修复 + import print/mermaid-overrides.css）
  │   ├── App.tsx               # 路由定义（含 /print-all 打印路由）
  │   ├── print-overrides.css   # 打印 CSS（PDF 导出用，已内联）
  │   ├── mermaid-overrides.css # Mermaid 图表样式覆盖（用 --ra-* token 让图表跟随文章主题）
  │   ├── components/           # 共享组件（Cover, Colophon, BackLink, MermaidDiagram）
  │   ├── pages/
  │   │   ├── IndexPage.tsx     # 导航首页（导出 PDF 按钮 + 搜索 + 按域分组）
  │   │   ├── SampleDoc.tsx     # 示例文档
  │   │   └── PrintAllPage.tsx  # 打印专用页（所有文档连排，PDF 导出用）
  │   ├── sections/             # Section 组件（按文档分组）
  │   │   └── sample/
  │   │       └── 01-opening.tsx
  │   └── raw-blocks/           # Raw 块素材（自定义 HTML/SVG，见 references/raw-policy.md）
  ├── plan/                     # 规划文件（plan.md）
  ├── review/                   # 审查文件（first-spread-review.md / final-review.md / repair-log.md）
  └── analysis/                 # 工作记忆（business-knowledge.md 是事实底座，db-schema/ 是数据库 Schema 抽取产物）
  └── package.json

下一步：
  1. cd {target}
  2. npm run dev      # 预览（默认在 localhost:5173）
  3. 添加新文档：
     a. 在 src/pages/ 创建新页面组件（复制 SampleDoc.tsx 模式）
     b. 在 src/sections/<doc-name>/ 创建 Section 组件
     c. 在 src/App.tsx 添加 <Route>
     d. 在 src/pages/IndexPage.tsx 的 DOCS 数组添加一条（含 domain/related 字段）
     e. 在 src/pages/PrintAllPage.tsx import 新页面组件并排列（PDF 导出需要）
  4. 每个页面通过 <ThemeProvider theme="..."> 声明自己的主题

构建交付：
  • npm run build     # 类型检查 + 单页 HTML → dist/index.html（所有文档在一个文件里）
  • 交付物：dist/index.html（离线可打开、可分享）
  • 导出 PDF：首页点「导出 PDF」按钮，或 python scripts/html-to-pdf.py --route print-all
""")


if __name__ == "__main__":
    main()
