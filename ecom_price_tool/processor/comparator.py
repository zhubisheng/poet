"""商品横向对比与价格分布统计模块."""

from __future__ import annotations

import statistics
from typing import Dict, List

from ..scraper.base import Product


def sort_by_price(products: List[Product], ascending: bool = True) -> List[Product]:
    """按价格排序，默认从低到高."""
    return sorted(products, key=lambda p: p.price, reverse=not ascending)


def compare_products(products: List[Product]) -> Dict:
    """生成横向对比统计指标.

    返回包含各平台对比、整体价格分布的结构化数据，供可视化与报告使用.
    """
    if not products:
        return {"total": 0, "platforms": {}, "overall": {}}

    # 按平台分组
    platforms: Dict[str, List[Product]] = {}
    for p in products:
        platforms.setdefault(p.platform, []).append(p)

    platform_stats: Dict[str, Dict] = {}
    for plat, items in platforms.items():
        prices = [p.price for p in items]
        sales = [p.sales for p in items]
        scores = [p.store_score for p in items if p.store_score > 0]
        platform_stats[plat] = {
            "count": len(items),
            "min_price": min(prices),
            "max_price": max(prices),
            "avg_price": round(statistics.mean(prices), 2),
            "median_price": round(statistics.median(prices), 2),
            "total_sales": sum(sales),
            "avg_score": round(statistics.mean(scores), 2) if scores else 0.0,
        }

    all_prices = [p.price for p in products]
    overall = {
        "total": len(products),
        "min_price": min(all_prices),
        "max_price": max(all_prices),
        "avg_price": round(statistics.mean(all_prices), 2),
        "median_price": round(statistics.median(all_prices), 2),
        "cheapest": min(products, key=lambda p: p.price).to_dict(),
        "best_seller": max(products, key=lambda p: p.sales).to_dict(),
    }

    return {
        "total": len(products),
        "platforms": platform_stats,
        "overall": overall,
        "price_distribution": build_price_distribution(products),
    }


def build_price_distribution(products: List[Product], bins: int = 8) -> List[Dict]:
    """构建价格区间分布，用于绘制价格分布图."""
    if not products:
        return []
    prices = sorted(p.price for p in products)
    lo, hi = prices[0], prices[-1]
    if lo == hi:
        return [{"range": f"{lo:.0f}", "count": len(prices)}]
    step = (hi - lo) / bins
    distribution: List[Dict] = []
    for i in range(bins):
        start = lo + i * step
        end = start + step
        if i == bins - 1:
            count = sum(1 for p in prices if start <= p <= end)
        else:
            count = sum(1 for p in prices if start <= p < end)
        distribution.append({
            "range": f"{start:.0f}-{end:.0f}",
            "start": round(start, 2),
            "end": round(end, 2),
            "count": count,
        })
    return distribution
