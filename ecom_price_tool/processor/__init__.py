"""数据处理模块：清洗、去重、排序、对比、性价比推荐."""

from .cleaner import clean_products, deduplicate_products
from .comparator import compare_products, build_price_distribution
from .recommender import recommend_cost_performance

__all__ = [
    "clean_products",
    "deduplicate_products",
    "compare_products",
    "build_price_distribution",
    "recommend_cost_performance",
]
