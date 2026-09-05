"""数据清洗与去重模块."""

from __future__ import annotations

import re
from typing import List

from ..scraper.base import Product


def _normalize_name(name: str) -> str:
    """标准化商品名称：去除多余空白、统一全角半角、移除促销标签."""
    if not name:
        return ""
    # 全角转半角
    name = name.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    # 移除常见促销标签
    name = re.sub(r"【.*?】|\[.*?\]|\(.*?\)|\（.*?\）", "", name)
    # 合并空白
    name = re.sub(r"\s+", " ", name).strip()
    return name


def clean_products(products: List[Product]) -> List[Product]:
    """清洗商品数据：

    - 去除名称为空或价格无效的记录
    - 标准化商品名称
    - 修正销量、评分范围
    """
    cleaned: List[Product] = []
    for p in products:
        if not p.name or p.price <= 0:
            continue
        p.name = _normalize_name(p.name)
        if not p.name:
            continue
        # 销量限制为非负
        p.sales = max(0, int(p.sales))
        # 评分限制在 0-5
        p.store_score = max(0.0, min(5.0, float(p.store_score)))
        cleaned.append(p)
    return cleaned


def deduplicate_products(products: List[Product]) -> List[Product]:
    """去重：

    1. 先按 uid (平台+url) 去重，保留首次出现
    2. 再按"平台 + 标准化商品名 + 价格"组合去重，避免同店同价重复
    """
    seen_uids = set()
    unique: List[Product] = []
    for p in products:
        if p.uid in seen_uids:
            continue
        seen_uids.add(p.uid)
        unique.append(p)

    # 第二重：名称+价格维度去重（同平台内）
    seen_keys = set()
    result: List[Product] = []
    for p in unique:
        key = f"{p.platform}|{p.name[:30]}|{p.price:.2f}"
        if key in seen_keys:
            continue
        seen_keys.add(key)
        result.append(p)
    return result
