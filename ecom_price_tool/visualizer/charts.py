"""图表绘制模块.

使用 matplotlib 绘制价格分布图、平台对比图、性价比推荐图.
所有图表均支持保存为 PNG 文件或以 base64 字符串返回（供网页嵌入）.
"""

from __future__ import annotations

import base64
import io
from typing import Dict, List, Optional

import matplotlib

matplotlib.use("Agg")  # 非交互式后端，适配无 GUI 环境
import matplotlib.pyplot as plt

# 中文字体配置（优先尝试常见中文字体，避免中文乱码）
plt.rcParams["font.sans-serif"] = [
    "Noto Sans CJK SC",
    "Noto Sans CJK JP",
    "WenQuanYi Zen Hei",
    "SimHei",
    "Microsoft YaHei",
    "Arial Unicode MS",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False

PLATFORM_COLORS = {"京东": "#E1251B", "淘宝": "#FF6A00", "拼多多": "#E02E24"}


def _fig_to_base64(fig) -> str:
    """将 matplotlib figure 转为 base64 PNG 字符串."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return b64


def plot_price_distribution(products: List, save_path: Optional[str] = None) -> Optional[str]:
    """绘制价格分布直方图."""
    if not products:
        return None
    prices = [p.price for p in products]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(prices, bins=10, color="#4C72B0", edgecolor="white", alpha=0.85)
    ax.set_title("商品价格分布", fontsize=14, fontweight="bold")
    ax.set_xlabel("价格 (元)")
    ax.set_ylabel("商品数量")
    ax.axvline(sum(prices) / len(prices), color="red", linestyle="--", linewidth=1.5, label="平均价")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    if save_path:
        fig.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close(fig)
        return save_path
    return _fig_to_base64(fig)


def plot_platform_comparison(comparison: Dict, save_path: Optional[str] = None) -> Optional[str]:
    """绘制各平台平均价格对比柱状图."""
    platforms = comparison.get("platforms", {})
    if not platforms:
        return None
    names = list(platforms.keys())
    avg_prices = [platforms[n]["avg_price"] for n in names]
    colors = [PLATFORM_COLORS.get(n, "#4C72B0") for n in names]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    # 平均价格对比
    axes[0].bar(names, avg_prices, color=colors, alpha=0.85, edgecolor="white")
    axes[0].set_title("各平台平均价格对比", fontsize=13, fontweight="bold")
    axes[0].set_ylabel("平均价格 (元)")
    for i, v in enumerate(avg_prices):
        axes[0].text(i, v, f"¥{v:.0f}", ha="center", va="bottom", fontsize=10)
    axes[0].grid(axis="y", alpha=0.3)

    # 各平台商品数量占比
    counts = [platforms[n]["count"] for n in names]
    axes[1].pie(counts, labels=names, autopct="%1.1f%%", colors=colors, startangle=90, textprops={"fontsize": 10})
    axes[1].set_title("各平台商品数量占比", fontsize=13, fontweight="bold")

    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close(fig)
        return save_path
    return _fig_to_base64(fig)


def plot_cost_performance(recommendations: List[Dict], save_path: Optional[str] = None) -> Optional[str]:
    """绘制 Top-N 性价比推荐横向条形图."""
    if not recommendations:
        return None
    # 取前 8 条，避免标签过长
    top = recommendations[:8]
    labels = [f"{r['name'][:18]}..." if len(r["name"]) > 18 else r["name"] for r in top]
    scores = [r["cost_performance_score"] for r in top]
    colors = [PLATFORM_COLORS.get(r["platform"], "#4C72B0") for r in top]

    fig, ax = plt.subplots(figsize=(10, 5))
    y_pos = range(len(top) - 1, -1, -1)
    bars = ax.barh(list(y_pos), scores, color=colors, alpha=0.85, edgecolor="white")
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(labels, fontsize=9)
    ax.set_xlabel("性价比评分")
    ax.set_title("性价比推荐 Top (满分 1.0)", fontsize=13, fontweight="bold")
    ax.set_xlim(0, 1.05)
    for bar, score in zip(bars, scores):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height() / 2,
                f"{score:.2f}", va="center", fontsize=9)
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    if save_path:
        fig.savefig(save_path, dpi=120, bbox_inches="tight")
        plt.close(fig)
        return save_path
    return _fig_to_base64(fig)


def render_all_charts_base64(products: List, comparison: Dict, recommendations: List[Dict]) -> Dict[str, str]:
    """一次性渲染所有图表，返回 base64 字符串字典（供网页嵌入）."""
    return {
        "price_distribution": plot_price_distribution(products),
        "platform_comparison": plot_platform_comparison(comparison),
        "cost_performance": plot_cost_performance(recommendations),
    }
