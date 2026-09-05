"""命令行入口：ecom-price 工具.

用法示例:
    python -m ecom_price_tool.cli search 手机 --demo
    python -m ecom_price_tool.cli search 耳机 --platforms 京东,淘宝 --pages 1 --output report.json
    python -m ecom_price_tool.cli search 笔记本 --demo --markdown report.md
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import List

from .pipeline import run_pipeline


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ecom-price",
        description="电商商品价格自动化采集与对比工具（支持京东/淘宝/拼多多）",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # search 子命令
    search_p = sub.add_parser("search", help="按关键词采集并对比商品价格")
    search_p.add_argument("keyword", help="搜索关键词，如：手机、耳机")
    search_p.add_argument(
        "--platforms", "-p",
        default="京东,淘宝,拼多多",
        help="采集平台，逗号分隔，默认全部（京东,淘宝,拼多多）",
    )
    search_p.add_argument("--pages", type=int, default=1, help="每个平台采集页数，默认 1")
    search_p.add_argument("--demo", action="store_true", help="使用演示数据（不实际请求电商网站）")
    search_p.add_argument("--top", type=int, default=5, help="性价比推荐数量，默认 5")
    search_p.add_argument("--output", "-o", help="输出 JSON 结果文件路径")
    search_p.add_argument("--markdown", "-m", help="输出 Markdown 报告文件路径")
    search_p.add_argument("--no-charts", action="store_true", help="不渲染图表（加速 CLI 输出）")
    search_p.add_argument("--verbose", "-v", action="store_true", help="显示详细日志")

    # demo 子命令：一键演示
    demo_p = sub.add_parser("demo", help="使用内置示例数据一键演示完整流程")
    demo_p.add_argument("--keyword", default="手机", help="演示关键词，默认 手机")

    return parser


def cmd_search(args: argparse.Namespace) -> int:
    _setup_logging(args.verbose)
    platforms = [p.strip() for p in args.platforms.split(",") if p.strip()]

    result = run_pipeline(
        keyword=args.keyword,
        platforms=platforms,
        max_pages=args.pages,
        demo=args.demo,
        top_n=args.top,
        render_charts=not args.no_charts,
    )

    # 终端输出文本报告
    print(result.text_report)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result.to_json())
        print(f"\n[已保存 JSON 结果] -> {args.output}")

    if args.markdown:
        with open(args.markdown, "w", encoding="utf-8") as f:
            f.write(result.markdown_report)
        print(f"[已保存 Markdown 报告] -> {args.markdown}")

    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    _setup_logging(False)
    print(f"[演示模式] 关键词：{args.keyword}（使用内置示例数据）\n")
    result = run_pipeline(
        keyword=args.keyword,
        demo=True,
        top_n=5,
        render_charts=True,
    )
    print(result.text_report)
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "search":
        return cmd_search(args)
    if args.command == "demo":
        return cmd_demo(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
