"""文本/Markdown 报告生成模块."""

from __future__ import annotations

from typing import Dict, List

from ..scraper.base import Product


def _format_sales(n: int) -> str:
    if n >= 10000:
        return f"{n / 10000:.1f}万"
    return str(n)


def generate_text_report(
    keyword: str,
    products: List[Product],
    comparison: Dict,
    recommendations: List[Dict],
) -> str:
    """生成纯文本终端报告."""
    lines = []
    lines.append("=" * 72)
    lines.append(f"  电商商品价格采集与对比报告  |  关键词：{keyword}")
    lines.append("=" * 72)

    ov = comparison.get("overall", {})
    lines.append(f"\n【整体统计】共采集 {comparison.get('total', 0)} 件商品")
    if ov:
        lines.append(f"  最低价: ¥{ov.get('min_price', 0):.2f}  |  最高价: ¥{ov.get('max_price', 0):.2f}  |  均价: ¥{ov.get('avg_price', 0):.2f}  |  中位价: ¥{ov.get('median_price', 0):.2f}")

    lines.append("\n【各平台对比】")
    lines.append(f"{'平台':<8}{'数量':>6}{'最低价':>10}{'最高价':>10}{'均价':>10}{'总销量':>12}{'均分':>8}")
    lines.append("-" * 72)
    for plat, stat in comparison.get("platforms", {}).items():
        lines.append(
            f"{plat:<8}{stat['count']:>6}"
            f"{stat['min_price']:>10.2f}{stat['max_price']:>10.2f}"
            f"{stat['avg_price']:>10.2f}{_format_sales(stat['total_sales']):>12}"
            f"{stat['avg_score']:>8.2f}"
        )

    lines.append("\n【价格排序（从低到高，前 10 件）】")
    sorted_products = sorted(products, key=lambda p: p.price)[:10]
    lines.append(f"{'价格':>8}  {'销量':>8}  {'评分':>5}  平台  商品名称")
    lines.append("-" * 72)
    for p in sorted_products:
        lines.append(f"¥{p.price:>7.2f}  {_format_sales(p.sales):>8}  {p.store_score:>5.2f}  {p.platform}  {p.name[:40]}")

    lines.append("\n【性价比推荐 Top 5】")
    lines.append("-" * 72)
    for i, r in enumerate(recommendations[:5], 1):
        lines.append(f"  {i}. [{r['platform']}] {r['name'][:45]}")
        lines.append(f"     价格 ¥{r['price']:.2f} | 销量 {_format_sales(r['sales'])} | 评分 {r['store_score']:.2f}")
        lines.append(f"     {r['recommendation']}")
        lines.append(f"     链接: {r['url']}")
        lines.append("")

    lines.append("=" * 72)
    return "\n".join(lines)


def generate_markdown_report(
    keyword: str,
    products: List[Product],
    comparison: Dict,
    recommendations: List[Dict],
) -> str:
    """生成 Markdown 格式报告，便于保存为文件."""
    lines = [f"# 电商商品价格采集与对比报告 — {keyword}\n"]

    ov = comparison.get("overall", {})
    lines.append("## 整体统计\n")
    lines.append(f"- 采集商品总数：**{comparison.get('total', 0)}** 件")
    if ov:
        lines.append(f"- 最低价：¥{ov.get('min_price', 0):.2f}")
        lines.append(f"- 最高价：¥{ov.get('max_price', 0):.2f}")
        lines.append(f"- 平均价：¥{ov.get('avg_price', 0):.2f}")
        lines.append(f"- 中位价：¥{ov.get('median_price', 0):.2f}\n")

    lines.append("## 各平台对比\n")
    lines.append("| 平台 | 数量 | 最低价 | 最高价 | 均价 | 总销量 | 平均评分 |")
    lines.append("|------|------|--------|--------|------|--------|----------|")
    for plat, stat in comparison.get("platforms", {}).items():
        lines.append(
            f"| {plat} | {stat['count']} | ¥{stat['min_price']:.2f} | ¥{stat['max_price']:.2f} | "
            f"¥{stat['avg_price']:.2f} | {_format_sales(stat['total_sales'])} | {stat['avg_score']:.2f} |"
        )

    lines.append("\n## 价格排序（从低到高，前 10 件）\n")
    lines.append("| 价格 | 销量 | 评分 | 平台 | 商品名称 | 链接 |")
    lines.append("|------|------|------|------|----------|------|")
    for p in sorted(products, key=lambda p: p.price)[:10]:
        lines.append(
            f"| ¥{p.price:.2f} | {_format_sales(p.sales)} | {p.store_score:.2f} | {p.platform} | "
            f"{p.name[:40]} | [链接]({p.url}) |"
        )

    lines.append("\n## 性价比推荐 Top 5\n")
    for i, r in enumerate(recommendations[:5], 1):
        lines.append(f"### {i}. {r['name'][:50]}")
        lines.append(f"- 平台：{r['platform']}")
        lines.append(f"- 价格：¥{r['price']:.2f}")
        lines.append(f"- 销量：{_format_sales(r['sales'])}")
        lines.append(f"- 店铺评分：{r['store_score']:.2f}")
        lines.append(f"- 性价比评分：{r['cost_performance_score']:.4f}")
        lines.append(f"- 推荐：{r['recommendation']}")
        lines.append(f"- 链接：{r['url']}\n")

    return "\n".join(lines)
