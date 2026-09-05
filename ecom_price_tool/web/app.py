"""Flask Web 演示应用.

启动后访问 http://localhost:5000 即可使用：
- 首页展示内置示例数据与对应结果（满足初始化示例要求）
- 输入关键词并选择模式后，现场运行采集对比脚本并展示结果
"""

from __future__ import annotations

import os
import sys
from flask import Flask, render_template, request, jsonify

# 允许以模块方式运行
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ..pipeline import run_pipeline  # noqa: E402

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

# 示例关键词（供首页初始化展示）
SAMPLE_KEYWORD = "手机"


def _build_result(keyword: str, demo: bool = True):
    """运行流水线并返回模板渲染所需的数据."""
    result = run_pipeline(keyword=keyword, demo=demo, top_n=5, render_charts=True)
    products = [p.to_dict() for p in result.sorted_products]
    return {
        "keyword": keyword,
        "source": result.source,
        "generated_at": result.generated_at,
        "total": result.comparison.get("total", 0),
        "overall": result.comparison.get("overall", {}),
        "platforms": result.comparison.get("platforms", {}),
        "price_distribution": result.comparison.get("price_distribution", []),
        "products": products,
        "recommendations": result.recommendations,
        "charts": result.charts,
        "text_report": result.text_report,
    }


@app.route("/")
def index():
    """首页：加载示例数据并展示结果示例."""
    sample = _build_result(SAMPLE_KEYWORD, demo=True)
    return render_template("index.html", result=sample, is_sample=True)


@app.route("/search", methods=["GET", "POST"])
def search():
    """搜索接口：根据关键词现场运行脚本."""
    keyword = request.values.get("keyword", "").strip()
    demo = request.values.get("mode", "demo") == "demo"
    if not keyword:
        return jsonify({"error": "请输入关键词"}), 400
    try:
        data = _build_result(keyword, demo=demo)
        return jsonify(data)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"运行失败: {exc}"}), 500


def main(host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
