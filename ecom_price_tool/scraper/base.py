"""采集器基类：封装通用请求、解析与异常处理逻辑."""

from __future__ import annotations

import hashlib
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# 常用浏览器 UA 池，降低被风控概率
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]


@dataclass
class Product:
    """统一的商品数据结构，跨平台字段对齐."""

    platform: str
    name: str
    price: float
    sales: int
    store_score: float
    url: str
    store_name: str = ""
    comment_count: int = 0
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def uid(self) -> str:
        """基于平台+链接生成稳定唯一 ID，用于去重."""
        key = f"{self.platform}|{self.url}"
        return hashlib.md5(key.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "name": self.name,
            "price": self.price,
            "sales": self.sales,
            "store_score": self.store_score,
            "store_name": self.store_name,
            "comment_count": self.comment_count,
            "url": self.url,
            "uid": self.uid,
        }


class BaseScraper:
    """采集器基类，提供请求发送、解析、重试等通用能力."""

    platform: str = "base"

    def __init__(self, timeout: int = 15, max_retries: int = 3, delay: float = 1.0):
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(self._default_headers())

    def _default_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }

    def _request(self, url: str, params: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """带重试与随机延时的 GET 请求."""
        for attempt in range(1, self.max_retries + 1):
            try:
                # 每次请求更换 UA
                self.session.headers["User-Agent"] = random.choice(USER_AGENTS)
                resp = self.session.get(url, params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    resp.encoding = resp.apparent_encoding or "utf-8"
                    return resp.text
                logger.warning("[%s] HTTP %s on attempt %d", self.platform, resp.status_code, attempt)
            except requests.RequestException as exc:
                logger.warning("[%s] request error on attempt %d: %s", self.platform, attempt, exc)
            time.sleep(self.delay * attempt)
        logger.error("[%s] failed to fetch %s after %d retries", self.platform, url, self.max_retries)
        return None

    def _parse_soup(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    def search(self, keyword: str, page: int = 1) -> List[Product]:
        """按关键词搜索商品，子类必须实现."""
        raise NotImplementedError

    def collect(self, keyword: str, max_pages: int = 1) -> List[Product]:
        """采集多页搜索结果."""
        products: List[Product] = []
        for page in range(1, max_pages + 1):
            logger.info("[%s] collecting keyword=%r page=%d", self.platform, keyword, page)
            try:
                page_products = self.search(keyword, page)
            except Exception as exc:  # noqa: BLE001
                logger.exception("[%s] page %d parse failed: %s", self.platform, page, exc)
                page_products = []
            products.extend(page_products)
            if not page_products:
                break
            time.sleep(self.delay)
        return products

    @staticmethod
    def parse_price(text: str) -> float:
        """从文本中提取价格数值."""
        if not text:
            return 0.0
        # 移除货币符号与逗号
        cleaned = text.replace("¥", "").replace("￥", "").replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            # 尝试提取第一个浮点数
            import re

            m = re.search(r"\d+(\.\d+)?", cleaned)
            return float(m.group()) if m else 0.0

    @staticmethod
    def parse_sales(text: str) -> int:
        """从文本中提取销量，支持'万'单位."""
        if not text:
            return 0
        import re

        m = re.search(r"(\d+(?:\.\d+)?)\s*万?", text)
        if not m:
            return 0
        num = float(m.group(1))
        if "万" in text:
            num *= 10000
        return int(num)

    @staticmethod
    def parse_score(text: str) -> float:
        """提取店铺评分 (0-5)."""
        if not text:
            return 0.0
        import re

        m = re.search(r"(\d+(?:\.\d+)?)", text)
        return float(m.group(1)) if m else 0.0
