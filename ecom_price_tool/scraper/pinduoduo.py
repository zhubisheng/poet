"""拼多多商品采集器."""

from __future__ import annotations

import re
from typing import List

from .base import BaseScraper, Product


class PinduoduoScraper(BaseScraper):
    """拼多多搜索页采集.

    拼多多移动端页面 (mobile.yangkeduo.com) 数据通过接口返回，
    此处实现基于 HTML 文本的解析，并对反爬策略做了基础 UA 伪装.
    """

    platform = "拼多多"

    SEARCH_URL = "https://mobile.yangkeduo.com/search_result.html"

    def search(self, keyword: str, page: int = 1) -> List[Product]:
        params = {"search_key": keyword, "page": page}
        html = self._request(self.SEARCH_URL, params=params)
        if not html:
            return []
        return self._parse_search(html)

    def _parse_search(self, html: str) -> List[Product]:
        products: List[Product] = []
        # 拼多多页面数据常以 window.rawData = {...} 形式内嵌
        match = re.search(r"window\.rawData\s*=\s*(\{.*?\})\s*;", html, re.S)
        if match:
            import json

            try:
                data = json.loads(match.group(1))
                items = (
                    data.get("store", {})
                    .get("searchResult", {})
                    .get("goodsList", [])
                )
                for it in items:
                    products.append(self._item_to_product(it))
                return products
            except json.JSONDecodeError:
                pass

        # 降级：CSS 选择器解析
        soup = self._parse_soup(html)
        for item in soup.select(".goods-item, .search-result-item"):
            try:
                name_el = item.select_one(".goods-name, .title")
                name = name_el.get_text(strip=True) if name_el else ""
                price_el = item.select_one(".price, .goods-price")
                price = self.parse_price(price_el.get_text()) if price_el else 0.0
                sales_el = item.select_one(".sales, .sold")
                sales = self.parse_sales(sales_el.get_text()) if sales_el else 0
                link_el = item.select_one("a[href]")
                url = link_el["href"] if link_el and link_el.has_attr("href") else ""
                if url and url.startswith("//"):
                    url = "https:" + url
                products.append(Product(
                    platform=self.platform,
                    name=name,
                    price=price,
                    sales=sales,
                    store_score=0.0,
                    url=url,
                    store_name="拼多多店铺",
                ))
            except Exception:  # noqa: BLE001
                continue
        return products

    def _item_to_product(self, item: dict) -> Product:
        goods_id = item.get("goods_id", "")
        url = f"https://mobile.yangkeduo.com/goods.html?goods_id={goods_id}" if goods_id else ""
        return Product(
            platform=self.platform,
            name=item.get("goods_name", ""),
            price=self.parse_price(str(item.get("min_group_price", 0))) / 100.0 if item.get("min_group_price") else 0.0,
            sales=int(item.get("cnt", 0)),
            store_score=float(item.get("mall_rate", 0) or 0) / 100.0 if item.get("mall_rate") else 0.0,
            url=url,
            store_name=item.get("mall_name", "拼多多店铺"),
        )
