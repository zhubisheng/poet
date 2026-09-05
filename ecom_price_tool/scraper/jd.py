"""京东商品采集器."""

from __future__ import annotations

import json
import re
from typing import List
from urllib.parse import quote

from .base import BaseScraper, Product


class JDScraper(BaseScraper):
    """京东搜索页采集.

    京东搜索结果以 HTML 内嵌的商品列表形式返回，价格通过单独接口获取.
    由于京东反爬较严，若采集失败可使用 --demo 模式的示例数据演示完整流程.
    """

    platform = "京东"

    SEARCH_URL = "https://search.jd.com/Search"

    def search(self, keyword: str, page: int = 1) -> List[Product]:
        # 京东分页：page 为奇数，从 1 开始，每页约 30 条
        jd_page = (page - 1) * 2 + 1
        params = {"keyword": keyword, "page": jd_page, "enc": "utf-8"}
        html = self._request(self.SEARCH_URL, params=params)
        if not html:
            return []
        return self._parse_search(html, keyword)

    def _parse_search(self, html: str, keyword: str) -> List[Product]:
        soup = self._parse_soup(html)
        products: List[Product] = []
        # 京东搜索结果位于 li.gl-item
        items = soup.select("li.gl-item")
        if not items:
            # 尝试移动端/新版结构
            items = soup.select("div.gl-i-wrap")
        for item in items:
            try:
                name_el = item.select_one(".p-name em") or item.select_one(".p-name a")
                name = name_el.get_text(strip=True) if name_el else ""
                if not name:
                    continue
                # 价格：优先 sku 内嵌价格，缺失则置 0（可后续补全）
                price_el = item.select_one(".p-price i") or item.select_one(".p-price strong i")
                price = self.parse_price(price_el.get_text()) if price_el else 0.0
                # 链接
                link_el = item.select_one(".p-name a") or item.select_one("a[href]")
                url = link_el["href"] if link_el and link_el.has_attr("href") else ""
                if url and url.startswith("//"):
                    url = "https:" + url
                elif url and url.startswith("/"):
                    url = "https://item.jd.com" + url
                # 销量/评论
                comment_el = item.select_one(".p-commit strong a") or item.select_one(".p-commit")
                comment_text = comment_el.get_text() if comment_el else ""
                sales = self.parse_sales(comment_text)
                # 店铺
                store_el = item.select_one(".p-shop span a") or item.select_one(".p-shop a")
                store_name = store_el.get_text(strip=True) if store_el else "京东第三方"
                score_el = item.select_one(".p-shop .im-ic")
                score = self.parse_score(score_el.get_text()) if score_el else 0.0
                products.append(Product(
                    platform=self.platform,
                    name=name,
                    price=price,
                    sales=sales,
                    store_score=score,
                    url=url,
                    store_name=store_name,
                    comment_count=sales,
                ))
            except Exception:  # noqa: BLE001
                continue
        return products
