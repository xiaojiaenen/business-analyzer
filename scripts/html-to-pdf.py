#!/usr/bin/env python3
"""
html-to-pdf.py — 把文章 HTML 转成 PDF

用法：
  python scripts/html-to-pdf.py [input.html] [output.pdf]
  python scripts/html-to-pdf.py                              # article/article.html → article/article.pdf
  python scripts/html-to-pdf.py --help

前提：本机已装 Chromium / Google Chrome / Microsoft Edge 之一（脚本自动探测）。
无需 npm 包、无需 Node。

工作原理：
  1. 在 HTML 的 </head> 前注入 @media print CSS（pdf-print-overrides.css）
  2. 用 headless 浏览器 --print-to-pdf 渲染
  3. 输出标准 A4 PDF
"""

import argparse
import os
import shutil
import subprocess
import sys
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
    parser.add_argument("input", nargs="?", default="article/article.html",
                        help="输入 HTML 文件（默认: article/article.html）")
    parser.add_argument("output", nargs="?", default="article/article.pdf",
                        help="输出 PDF 文件（默认: article/article.pdf）")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    script_dir = get_script_dir()
    css_file = script_dir / "pdf-print-overrides.css"

    if not input_path.exists():
        print(f"✗ 输入文件不存在：{input_path}")
        print("  先在工作区跑 npm run html 产出 article/article.html。")
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

    # 渲染 PDF
    # 先试 --headless=new（新版 Chrome），失败回退 --headless
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
                    "--virtual-time-budget=5000",
                    f"--print-to-pdf={output_path}",
                    f"file:///{tmp_html.replace(os.sep, '/')}",
                ],
                capture_output=True,
                timeout=60,
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
