"""采集与对比主流程：串联采集、清洗、去重、排序、对比、推荐、可视化."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from .scraper.base import Product
from .scraper.jd import JDScraper
from .scraper.taobao import TaobaoScraper
from .scraper.pinduoduo import PinduoduoScraper
from .scraper.demo_data import generate_demo_products
from .processor.cleaner import clean_products, deduplicate_products
from .processor.comparator import compare_products, sort_by_price
from .processor.recommender import recommend_cost_performance
from .visualizer.charts import render_all_charts_base64
from .visualizer.report import generate_text_report, generate_markdown_report

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """采集与对比全流程结果."""

    keyword: str
    products: List[Product]
    sorted_products: List[Product]
    comparison: Dict
    recommendations: List[Dict]
    charts: Dict[str, str] = field(default_factory=dict)
    text_report: str = ""
    markdown_report: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    source: str = "real"  # real / demo

    def to_dict(self) -> Dict:
        return {
            "keyword": self.keyword,
            "source": self.source,
            "generated_at": self.generated_at,
            "total": len(self.products),
            "products": [p.to_dict() for p in self.sorted_products],
            "comparison": self.comparison,
            "recommendations": self.recommendations,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


def collect(
    keyword: str,
    platforms: Optional[List[str]] = None,
    max_pages: int = 1,
    demo: bool = False,
    demo_count: int = 12,
) -> List[Product]:
    """采集指定平台的商品数据.

    Args:
        keyword: 搜索关键词
        platforms: 平台列表，可选 京东/淘宝/拼多多，默认全部
        max_pages: 每个平台采集页数
        demo: 是否使用演示数据（真实采集失败或演示用）
        demo_count: 演示数据数量
    """
    if platforms is None:
        platforms = ["京东", "淘宝", "拼多多"]

    scraper_map = {
        "京东": JDScraper,
        "淘宝": TaobaoScraper,
        "拼多多": PinduoduoScraper,
    }

    if demo:
        logger.info("使用演示数据模式，关键词=%s", keyword)
        return generate_demo_products(keyword, count=demo_count)

    all_products: List[Product] = []
    for plat in platforms:
        scraper_cls = scraper_map.get(plat)
        if not scraper_cls:
            logger.warning("未知平台: %s，跳过", plat)
            continue
        scraper = scraper_cls()
        try:
            items = scraper.collect(keyword, max_pages=max_pages)
            logger.info("[%s] 采集到 %d 条商品", plat, len(items))
            all_products.extend(items)
        except Exception as exc:  # noqa: BLE001
            logger.exception("[%s] 采集异常: %s", plat, exc)

    # 真实采集为空时，自动降级到演示数据，保证流程可演示
    if not all_products:
        logger.warning("真实采集结果为空，自动降级为演示数据")
        return generate_demo_products(keyword, count=demo_count)
    return all_products


def run_pipeline(
    keyword: str,
    platforms: Optional[List[str]] = None,
    max_pages: int = 1,
    demo: bool = False,
    top_n: int = 5,
    render_charts: bool = True,
) -> PipelineResult:
    """运行完整采集对比流程.

    1. 采集 -> 2. 清洗 -> 3. 去重 -> 4. 排序 -> 5. 对比统计 -> 6. 性价比推荐 -> 7. 可视化
    """
    logger.info("开始处理关键词: %s", keyword)
    products = collect(keyword, platforms=platforms, max_pages=max_pages, demo=demo)
    source = "demo" if (demo or not products) else "real"

    products = clean_products(products)
    products = deduplicate_products(products)
    sorted_products = sort_by_price(products, ascending=True)

    comparison = compare_products(sorted_products)
    recommendations = recommend_cost_performance(sorted_products, top_n=top_n)

    charts: Dict[str, str] = {}
    if render_charts:
        try:
            charts = render_all_charts_base64(sorted_products, comparison, recommendations)
        except Exception as exc:  # noqa: BLE001
            logger.exception("图表渲染失败: %s", exc)

    text_report = generate_text_report(keyword, sorted_products, comparison, recommendations)
    markdown_report = generate_markdown_report(keyword, sorted_products, comparison, recommendations)

    return PipelineResult(
        keyword=keyword,
        products=products,
        sorted_products=sorted_products,
        comparison=comparison,
        recommendations=recommendations,
        charts=charts,
        text_report=text_report,
        markdown_report=markdown_report,
        source=source,
    )
