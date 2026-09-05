"""演示数据生成模块.

当真实采集因反爬或网络问题失败时，使用该模块生成贴近真实场景的示例数据，
保证工具的演示网页与 CLI 流程始终可运行.
"""

from __future__ import annotations

import hashlib
import random
from typing import Dict, List

from .base import Product

# 关键词 -> 商品名称模板（用于生成贴合关键词的示例商品）
KEYWORD_TEMPLATES: Dict[str, List[str]] = {
    "手机": [
        "Apple iPhone 15 Pro Max 256GB 原色钛金属",
        "华为 Mate 60 Pro 12GB+512GB 雅丹黑",
        "小米 14 Ultra 16GB+1TB 黑色 徕卡光学",
        "OPPO Find X7 Ultra 16GB+512GB 海阔天空",
        "vivo X100 Pro 16GB+512GB 星迹蓝",
        "荣耀 Magic6 Pro 16GB+512GB 绒黑色",
        "三星 Galaxy S24 Ultra 12GB+256GB 钛灰",
        "Redmi K70 Pro 16GB+1TB 墨羽",
    ],
    "耳机": [
        "Apple AirPods Pro 2 第二代 USB-C 主动降噪",
        "索尼 WH-1000XM5 头戴式无线降噪耳机",
        "华为 FreeBuds Pro 3 真无线蓝牙降噪耳机",
        "小米 Buds 4 Pro 真无线蓝牙耳机",
        "Bose QuietComfort Ultra 头戴式降噪耳机",
        "漫步者 NeoBuds Pro 2 真无线降噪耳机",
    ],
    "笔记本": [
        "Apple MacBook Pro 14英寸 M3 Pro 18GB+512GB",
        "联想 ThinkPad X1 Carbon 2024 i7-1360P 16GB+1TB",
        "华为 MateBook X Pro 2024 Ultra7 32GB+2TB",
        "戴尔 XPS 13 Plus i7-1360P 16GB+1TB",
        "小米笔记本 Pro 14 2024 Ultra5 32GB+1TB",
        "ROG 幻16 Air 2024 Ultra9 RTX4060 32GB+1TB",
    ],
    "显示器": [
        "戴尔 U2723QE 27英寸 4K IPS 显示器",
        "LG 27GP950 27英寸 4K 144Hz Nano IPS",
        "三星 Odyssey G7 32英寸 2K 240Hz 曲面",
        "华为 MateView 28.2英寸 4K+ 无线投屏",
        "小米 27英寸 4K 显示器 IPS HDR400",
    ],
    "相机": [
        "索尼 A7M4 全画幅微单相机 单机身",
        "佳能 EOS R6 Mark II 全画幅微单相机",
        "尼康 Z6 III 全画幅微单相机 单机身",
        "富士 X-T5 复古微单相机 18-55mm套机",
        "理光 GR3x 街拍便携数码相机",
    ],
}

# 店铺名称池
STORE_NAMES = [
    "京东自营旗舰店", "天猫官方旗舰店", "拼多多百亿补贴",
    "品牌官方旗舰店", "京东国际自营", "苏宁易购官方旗舰店",
    "天猫超市", "拼多多品牌馆", "京东数码旗舰店",
]

PLATFORMS = ["京东", "淘宝", "拼多多"]


def _price_range(keyword: str) -> tuple:
    """根据关键词给出合理价格区间."""
    ranges = {
        "手机": (1299, 9999),
        "耳机": (99, 2999),
        "笔记本": (2999, 29999),
        "显示器": (799, 12999),
        "相机": (2999, 29999),
    }
    for k, rng in ranges.items():
        if k in keyword:
            return rng
    return (19, 9999)


def _gen_score() -> float:
    """生成 4.5 - 5.0 之间的店铺评分."""
    return round(random.uniform(4.5, 5.0), 2)


def _gen_sales() -> int:
    """生成销量，含 0 - 10万 级."""
    base = random.choice([100, 500, 1000, 5000, 10000, 50000, 100000])
    return base + random.randint(0, base // 2)


def generate_demo_products(keyword: str, count: int = 12) -> List[Product]:
    """根据关键词生成演示商品数据.

    生成逻辑：
    - 匹配内置关键词模板，生成贴合关键词的商品名称
    - 按关键词类型生成合理价格区间
    - 随机分配平台、店铺、评分、销量
    """
    templates = None
    for key, names in KEYWORD_TEMPLATES.items():
        if key in keyword:
            templates = names
            break
    if templates is None:
        # 未命中内置模板，基于关键词生成通用名称
        templates = [
            f"{keyword} 标准版 热销款",
            f"{keyword} 旗舰版 新品上市",
            f"{keyword} 尊享版 官方正品",
            f"{keyword} 入门版 性价比之选",
            f"{keyword} Pro 专业版",
            f"{keyword} 套装版 含配件",
            f"{keyword} 豪华版 顺丰包邮",
            f"{keyword} 经典版 好评如潮",
        ]

    low, high = _price_range(keyword)
    products: List[Product] = []

    for i in range(count):
        name = random.choice(templates)
        platform = random.choice(PLATFORMS)
        store = random.choice(STORE_NAMES)
        # 同平台同名称不重复过多
        price = round(random.uniform(low, high), 2)
        sales = _gen_sales()
        score = _gen_score()
        # 构造真实感 URL
        if platform == "京东":
            url = f"https://item.jd.com/{random.randint(10000000, 99999999)}.html"
        elif platform == "淘宝":
            url = f"https://item.taobao.com/item.htm?id={random.randint(100000000000, 999999999999)}"
        else:
            url = f"https://mobile.yangkeduo.com/goods.html?goods_id={random.randint(100000000, 999999999)}"
        products.append(Product(
            platform=platform,
            name=name,
            price=price,
            sales=sales,
            store_score=score,
            url=url,
            store_name=store,
            comment_count=sales,
        ))
    return products
