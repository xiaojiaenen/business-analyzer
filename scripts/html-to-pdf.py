#!/usr/bin/env python3
"""
html-to-pdf.py — 把文章 HTML 转成 PDF

用法：
  python scripts/html-to-pdf.py [input.html] [output.pdf] [--route ROUTE]
  python scripts/html-to-pdf.py                              # dist/index.html → dist/index.pdf
  python scripts/html-to-pdf.py --route print-all            # 打印所有文档到一个 PDF
  python scripts/html-to-pdf.py --route business-overview    # 只打印某份文档
  python scripts/html-to-pdf.py --help

前提：本机已装 Chromium / Google Chrome / Microsoft Edge 之一（脚本自动探测）。
无需 npm 包、无需 Node。

工作原理：
  1. 在 HTML 的 </head> 前注入 @media print CSS（pdf-print-overrides.css）
  2. 用 headless 浏览器 --print-to-pdf 渲染
  3. 输出标准 A4 PDF

--route 参数：
  多文档 SPA 用 HashRouter 路由切换，默认只渲染首页。
  --route print-all      打开 index.html#/print-all，渲染所有文档到一个 PDF
  --route <doc-name>     打开 index.html#/<doc-name>，只打印指定文档
  不传 --route            打开 index.html，打印默认路由（导航首页）
"""

import argparse
import os
import shutil
import subprocess
import sys

# Windows: 强制 stdout/stderr 使用 UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import tempfile
from pathlib import Path


def get_script_dir() -> Path:
    return Path(__file__).resolve().parent


def find_browser() -> str | None:
    """自动探测 chromium-family 浏览器"""
    # Windows 优先
    if sys.platform == "win32":
        candidates = [
            # Chrome
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            # Edge
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            # Brave
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
        ]
    elif sys.platform == "darwin":
        candidates = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Arc.app/Contents/MacOS/Arc",
        ]
    else:
        candidates = [
            "google-chrome", "google-chrome-stable", "chromium",
            "chromium-browser", "chrome", "brave-browser",
            "microsoft-edge",
        ]

    for c in candidates:
        if shutil.which(c):
            return c
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c

    return None


def main():
    parser = argparse.ArgumentParser(description="HTML → PDF（headless 浏览器 + print CSS）")
    parser.add_argument("input", nargs="?", default="dist/index.html",
                        help="输入 HTML 文件（默认: dist/index.html）")
    parser.add_argument("output", nargs="?", default="dist/index.pdf",
                        help="输出 PDF 文件（默认: dist/index.pdf）")
    parser.add_argument("--route", default=None,
                        help="HashRouter 路由（如 print-all / business-overview），不传则打印默认路由")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    script_dir = get_script_dir()
    css_file = script_dir / "pdf-print-overrides.css"

    if not input_path.exists():
        print(f"✗ 输入文件不存在：{input_path}")
        print("  先在项目根目录跑 npm run build 产出 dist/index.html。")
        sys.exit(1)

    if not css_file.exists():
        print(f"✗ 找不到打印覆盖 CSS：{css_file}")
        print("  这个文件应跟脚本同目录（scripts/pdf-print-overrides.css）。")
        sys.exit(2)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 注入 print CSS
    with open(css_file, "r", encoding="utf-8") as f:
        print_css = f.read()

    with open(input_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    if "</head>" not in html_content:
        print("✗ 注入失败：未在输入 HTML 找到 </head>。")
        print("  你的 HTML 可能不是 Vite + reacticle 单页产物。")
        sys.exit(3)

    injected_html = html_content.replace(
        "</head>",
        f'<style id="ra-pdf-overrides">\n{print_css}\n</style>\n</head>',
        1
    )

    # 写入临时文件
    tmp_dir = tempfile.mkdtemp(prefix="article-pdf-")
    tmp_html = os.path.join(tmp_dir, "article-print.html")
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(injected_html)

    # 找浏览器
    browser = find_browser()
    if not browser:
        print("⚠ 未找到任何 chromium-family 浏览器（Chrome / Edge / Brave / Chromium）。")
        print(f"\n  回退方案：注入了打印 CSS 的 HTML 已经放在：")
        print(f"  {tmp_html}")
        print(f"\n  请用浏览器打开它 → Ctrl+P → 目标改为'另存为 PDF' → 保存。")
        print("  注入的 print 样式会让 TOC 在上、正文在下，与 PDF 阅读习惯对齐。")
        sys.exit(3)

    print(f"▸ 浏览器：{browser}")
    print(f"▸ 输入：{input_path}")
    print(f"▸ 输出：{output_path}")
    if args.route:
        print(f"▸ 路由：#{args.route if args.route.startswith('/') else '/' + args.route}")

    # 构建 file URL，附加 HashRouter 路由
    file_url = f"file:///{tmp_html.replace(os.sep, '/')}"
    if args.route:
        route = args.route if args.route.startswith("/") else "/" + args.route
        file_url += f"#{route}"

    # 渲染 PDF
    # 先试 --headless=new（新版 Chrome），失败回退 --headless
    # 多文档路由（print-all）需要更长渲染时间，提高 virtual-time-budget
    vtime = "15000" if args.route == "print-all" else "5000"
    for headless_flag in ["--headless=new", "--headless"]:
        try:
            result = subprocess.run(
                [
                    browser,
                    headless_flag,
                    "--disable-gpu",
                    "--no-sandbox",
                    "--hide-scrollbars",
                    "--no-pdf-header-footer",
                    f"--virtual-time-budget={vtime}",
                    f"--print-to-pdf={output_path}",
                    file_url,
                ],
                capture_output=True,
                timeout=120,
                check=False,
            )
            if output_path.exists() and output_path.stat().st_size > 0:
                break
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

    # 清理临时文件
    try:
        shutil.rmtree(tmp_dir)
    except Exception:
        pass

    if output_path.exists() and output_path.stat().st_size > 0:
        size_kb = output_path.stat().st_size / 1024
        print(f"✓ PDF 输出：{output_path} ({size_kb:.0f} KB)")
        print("\n  如果 TOC / 分页不理想，检查 pdf-print-overrides.css。")
    else:
        print(f"✗ 浏览器返回成功但输出文件不存在或为空：{output_path}")
        sys.exit(4)


if __name__ == "__main__":
    main()
