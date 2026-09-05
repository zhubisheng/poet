"""淘宝/天猫商品采集器."""

from __future__ import annotations

import re
from typing import List
from urllib.parse import quote

from .base import BaseScraper, Product


class TaobaoScraper(BaseScraper):
    """淘宝搜索页采集.

    淘宝搜索结果主要通过前端渲染，HTML 中常包含 window.__INITIAL_STATE__
    或 mtop 接口数据. 此处实现基于 HTML 文本正则提取的轻量解析.
    """

    platform = "淘宝"

    SEARCH_URL = "https://s.taobao.com/search"

    def search(self, keyword: str, page: int = 1) -> List[Product]:
        params = {
            "q": keyword,
            "imgfile": "",
            "js": "1",
            "stats_click": "search_radio_all:1",
            "initiative_id": "staobaoz_20240101",
            "ie": "utf8",
            "s": (page - 1) * 44,
        }
        html = self._request(self.SEARCH_URL, params=params)
        if not html:
            return []
        return self._parse_search(html)

    def _parse_search(self, html: str) -> List[Product]:
        products: List[Product] = []
        # 淘宝搜索结果常以 window.__INITIAL_STATE__ = {...} 形式内嵌
        match = re.search(r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;", html, re.S)
        if match:
            import json

            try:
                data = json.loads(match.group(1))
                items = (
                    data.get("mods", {})
                    .get("itemlist", {})
                    .get("data", {})
                    .get("auctions", [])
                )
                for it in items:
                    products.append(self._item_to_product(it))
                return products
            except json.JSONDecodeError:
                pass

        # 降级：用 BeautifulSoup 解析卡片结构
        soup = self._parse_soup(html)
        for item in soup.select(".item.J_MouserOnverReq"):
            try:
                name_el = item.select_one(".title a") or item.select_one(".J_ClickStat")
                name = name_el.get_text(strip=True) if name_el else ""
                price_el = item.select_one(".price strong") or item.select_one(".price")
                price = self.parse_price(price_el.get_text()) if price_el else 0.0
                deal_el = item.select_one(".deal-cnt")
                sales = self.parse_sales(deal_el.get_text()) if deal_el else 0
                shop_el = item.select_one(".shop a") or item.select_one(".shop")
                store_name = shop_el.get_text(strip=True) if shop_el else "淘宝店铺"
                link_el = item.select_one(".J_ClickStat") or item.select_one("a[href]")
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
                    store_name=store_name,
                ))
            except Exception:  # noqa: BLE001
                continue
        return products

    def _item_to_product(self, item: dict) -> Product:
        raw_url = item.get("detail_url", "")
        if raw_url.startswith("//"):
            raw_url = "https:" + raw_url
        elif raw_url.startswith("/"):
            raw_url = "https://item.taobao.com" + raw_url
        return Product(
            platform=self.platform,
            name=item.get("raw_title", item.get("title", "")),
            price=self.parse_price(str(item.get("view_price", 0))),
            sales=self.parse_sales(str(item.get("view_sales", "0"))),
            store_score=0.0,
            url=raw_url,
            store_name=item.get("nick", "淘宝店铺"),
        )
