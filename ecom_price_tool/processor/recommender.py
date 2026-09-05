"""性价比推荐模块.

基于价格、销量、店铺评分构建综合性价比评分，给出推荐标注.
"""

from __future__ import annotations

from typing import Dict, List

from ..scraper.base import Product


def _minmax(values: List[float]) -> List[float]:
    """Min-Max 归一化到 0-1."""
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [1.0] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def recommend_cost_performance(products: List[Product], top_n: int = 5) -> List[Dict]:
    """计算性价比评分并返回 Top-N 推荐.

    评分维度与权重：
    - 价格越低越好（权重 0.4）
    - 销量越高越好（权重 0.35，反映市场认可度）
    - 店铺评分越高越好（权重 0.25，反映品质保障）
    """
    if not products:
        return []

    prices = [p.price for p in products]
    sales = [p.sales for p in products]
    scores = [p.store_score for p in products]

    # 价格反向归一化（越便宜分越高）
    norm_price = [1.0 - x for x in _minmax(prices)]
    norm_sales = _minmax([float(s) for s in sales])
    norm_score = _minmax(scores)

    scored: List[Dict] = []
    for i, p in enumerate(products):
        cp_score = round(
            norm_price[i] * 0.4 + norm_sales[i] * 0.35 + norm_score[i] * 0.25,
            4,
        )
        scored.append({
            **p.to_dict(),
            "cost_performance_score": cp_score,
            "recommendation": _build_recommendation(cp_score, p),
        })

    scored.sort(key=lambda x: x["cost_performance_score"], reverse=True)
    return scored[:top_n]


def _build_recommendation(score: float, p: Product) -> str:
    """根据性价比分值给出推荐等级与推荐语."""
    if score >= 0.75:
        level = "⭐⭐⭐⭐⭐ 强烈推荐"
        reason = f"价格亲民({p.price:.0f}元)、销量可观、口碑上佳，综合性价比最优"
    elif score >= 0.6:
        level = "⭐⭐⭐⭐ 值得入手"
        reason = f"价格适中({p.price:.0f}元)、销量与口碑表现良好"
    elif score >= 0.4:
        level = "⭐⭐⭐ 可考虑"
        reason = f"价格 {p.price:.0f} 元，销量或评分有提升空间"
    else:
        level = "⭐⭐ 谨慎选择"
        reason = f"价格 {p.price:.0f} 元偏高，综合竞争力一般"
    return f"{level} - {reason}"
