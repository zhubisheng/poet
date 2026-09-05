"""电商数据采集模块."""

from .base import BaseScraper
from .jd import JDScraper
from .taobao import TaobaoScraper
from .pinduoduo import PinduoduoScraper
from .demo_data import generate_demo_products

__all__ = [
    "BaseScraper",
    "JDScraper",
    "TaobaoScraper",
    "PinduoduoScraper",
    "generate_demo_products",
]
