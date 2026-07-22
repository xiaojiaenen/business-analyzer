#!/usr/bin/env python3
"""
scaffold.py — 创建文章工作区（Vite + React + TypeScript + reacticle）

用法：
  python scripts/scaffold.py <target-dir> [--theme=<id>] [--no-cover]
  python scripts/scaffold.py --list-themes

示例：
  python scripts/scaffold.py ./my-article --theme=tufte
  python scripts/scaffold.py ./brief --theme=press --no-cover

工作区从 npm 安装最新发布版 reacticle。
"""

import argparse
import json
import os
import re
import shutil
import sys

# Windows: 强制 stdout/stderr 使用 UTF-8，避免中文乱码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import subprocess
import sys
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
    print(f"\n用 --theme=<id> 选定一个。默认：tufte。")


def theme_exists(profiles_path: Path, theme_id: str) -> bool:
    """校验主题是否存在"""
    if not profiles_path.exists():
        return False
    with open(profiles_path, "r", encoding="utf-8") as f:
        themes = json.load(f)
    return any(t["id"] == theme_id for t in themes)


def check_npm() -> bool:
    """检查 npm 是否可用"""
    try:
        subprocess.run(["npm", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def process_cover_in_main_tsx(main_tsx_path: Path, cover_enabled: bool):
    """处理 main.tsx 中的封面标记"""
    content = main_tsx_path.read_text(encoding="utf-8")

    if cover_enabled:
        # 删除标记行，保留中间的 import 和 <Cover/>
        lines = content.split("\n")
        filtered = [
            line for line in lines
            if "__COVER_IMPORT_BEGIN__" not in line
            and "__COVER_IMPORT_END__" not in line
            and "__COVER_RENDER_BEGIN__" not in line
            and "__COVER_RENDER_END__" not in line
        ]
        content = "\n".join(filtered)
    else:
        # 删除 BEGIN..END 之间的整段（含标记行）
        content = re.sub(
            r'[^\n]*__COVER_IMPORT_BEGIN__.*?__COVER_IMPORT_END__[^\n]*\n',
            '', content, flags=re.DOTALL
        )
        content = re.sub(
            r'[^\n]*__COVER_RENDER_BEGIN__.*?__COVER_RENDER_END__[^\n]*\n',
            '', content, flags=re.DOTALL
        )

    main_tsx_path.write_text(content, encoding="utf-8")


def main():
    skill_dir = get_skill_dir()
    template_dir = skill_dir / "assets" / "scaffold-template"
    profiles_path = skill_dir / "references" / "themes" / "index.json"
    default_theme = "tufte"

    parser = argparse.ArgumentParser(
        description="创建文章工作区（Vite + React + TypeScript + reacticle）"
    )
    parser.add_argument("target", nargs="?", help="目标目录")
    parser.add_argument("--theme", default=default_theme, help=f"主题 ID（默认: {default_theme}）")
    parser.add_argument("--no-cover", action="store_true", help="禁用封面")
    parser.add_argument("--list-themes", action="store_true", help="列出可用主题")

    args = parser.parse_args()

    if args.list_themes:
        list_themes(profiles_path)
        return

    if not args.target:
        parser.print_help()
        print("\n请指定目标目录，例如: python scripts/scaffold.py ./my-article --theme=press")
        sys.exit(1)

    theme = args.theme
    cover = not args.no_cover
    target = Path(args.target).resolve()

    # 校验主题
    if not theme_exists(profiles_path, theme):
        print(f"✗ 未知主题 '{theme}'。可用主题：\n")
        list_themes(profiles_path)
        sys.exit(1)

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

    print(f"▸ 在 {target} 创建工作区")
    print(f"▸ 主题：{theme}")
    print(f"▸ 封面：{'开（屏幕 3:4 / PDF 独占首页）' if cover else '关'}")
    print(f"▸ reacticle：从 npm 安装最新发布版")

    # 创建目录结构
    target.mkdir(parents=True, exist_ok=True)
    (target / "source").mkdir(exist_ok=True)
    (target / "plan").mkdir(exist_ok=True)
    (target / "review").mkdir(exist_ok=True)
    (target / "article" / "sections").mkdir(parents=True, exist_ok=True)
    (target / "article" / "raw-blocks").mkdir(parents=True, exist_ok=True)
    (target / "article" / "assets").mkdir(parents=True, exist_ok=True)

    # 复制工程模板文件
    for filename in ["package.json", "vite.config.ts", "tsconfig.json",
                     "tsconfig.node.json", "index.html"]:
        src = template_dir / filename
        if src.exists():
            shutil.copy2(src, target / filename)

    # 复制 article 文件
    article_template = template_dir / "article"
    shutil.copy2(article_template / "main.tsx", target / "article" / "main.tsx")
    shutil.copy2(article_template / "Article.tsx", target / "article" / "Article.tsx")
    shutil.copy2(
        article_template / "sections" / "01-opening.tsx",
        target / "article" / "sections" / "01-opening.tsx"
    )

    # 封面
    if cover:
        shutil.copy2(article_template / "Cover.tsx", target / "article" / "Cover.tsx")

    # gitkeep
    (target / "article" / "raw-blocks" / ".gitkeep").touch()
    (target / "article" / "assets" / ".gitkeep").touch()

    # 注入主题 id
    main_tsx = target / "article" / "main.tsx"
    article_tsx = target / "article" / "Article.tsx"

    for fpath in [main_tsx, article_tsx]:
        content = fpath.read_text(encoding="utf-8")
        content = content.replace("__THEME__", theme)
        fpath.write_text(content, encoding="utf-8")

    # 处理封面标记
    process_cover_in_main_tsx(main_tsx, cover)

    # 记录主题
    (target / ".theme").write_text(theme, encoding="utf-8")

    # 安装依赖
    os.chdir(target)
    print("▸ 安装依赖（含 reacticle 最新版，可能要等一会）...")

    # 支持 NPM_REGISTRY 环境变量（国内镜像）
    npm_base = ["npm"]
    registry = os.environ.get("NPM_REGISTRY", "")
    if registry:
        print(f"▸ 使用 registry: {registry}")
        npm_base.extend(["--registry", registry])

    subprocess.run([*npm_base, "install"], capture_output=True, check=False)
    subprocess.run([*npm_base, "install", "reacticle@latest"], capture_output=True, check=False)

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
        subprocess.run(["npx", "tsc", "--noEmit"], check=True)
        print("✓ typecheck 通过")
    except subprocess.CalledProcessError:
        print("⚠ typecheck 有问题（见上），dev / build 仍可能正常 —— 请人工确认。")

    cover_hint = (
        "封面：替换 article/Cover.tsx 里的 <CoverPlaceholder />，按文章+主题做定制。"
        if cover
        else "封面：已关闭。如需打开，重新跑 scaffold 时去掉 --no-cover。"
    )

    print(f"""
✓ 完成。工作区：{target}（主题 {theme}）

下一步：
  1. cd {target}
  2. npm run dev      # 预览（先写首屏 + 第一个 Section）
  3. 首屏（Hero/Lead）写进 article/Article.tsx（assembler）；
     第一个 Section 写进 article/sections/01-opening.tsx
     —— 铁律：一个 Section 一个文件。
  4. {cover_hint}
  5. 把决策落盘到 source/ plan/ review/（长期记忆）

构建交付：
  • npm run build     # 类型检查 + 单页 HTML → dist/index.html
  • npm run html      # 复用 build，复制为交付物 article/article.html

切主题：改 article/main.tsx 的 <ThemeProvider theme="..."> 一个字即可。
升级组件库：npm install reacticle@latest
""")


if __name__ == "__main__":
    main()
