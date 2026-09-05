"""数据可视化模块：价格分布图、平台对比图、性价比推荐图与文本报告."""

from .charts import (
    plot_price_distribution,
    plot_platform_comparison,
    plot_cost_performance,
    render_all_charts_base64,
)
from .report import generate_text_report, generate_markdown_report

__all__ = [
    "plot_price_distribution",
    "plot_platform_comparison",
    "plot_cost_performance",
    "render_all_charts_base64",
    "generate_text_report",
    "generate_markdown_report",
]
