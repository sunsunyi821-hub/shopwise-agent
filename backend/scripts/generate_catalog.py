"""Generate the deterministic demo catalog.

Run from backend/:
    python scripts/generate_catalog.py

The output is committed to app/data/products.json so the app is reproducible
without a database dump. All products/brands/reviews are fictional.
"""

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "app" / "data" / "products.json"


def P(
    id: str,
    name: str,
    brand: str,
    category: str,
    price: float,
    original_price: float,
    rating: float,
    review_count: int,
    attributes: dict,
    pros: list[str],
    cons: list[str],
    tags: list[str],
) -> dict:
    return {
        "id": id,
        "name": name,
        "brand": brand,
        "category": category,
        "price": price,
        "original_price": original_price,
        "rating": rating,
        "review_count": review_count,
        "description": _description(name, brand, category, attributes),
        "attributes": attributes,
        "pros": pros,
        "cons": cons,
        "tags": tags,
        "image_key": id,
    }


def _description(name: str, brand: str, category: str, attrs: dict) -> str:
    parts = [f"{brand} {name}"]
    if "skin_type" in attrs:
        parts.append(f"适合{attrs['skin_type']}")
    if "hair_type" in attrs:
        parts.append(f"适合{attrs['hair_type']}发质")
    if "function" in attrs:
        parts.append(f"主打{attrs['function']}")
    if "volume_ml" in attrs:
        parts.append(f"{attrs['volume_ml']}ml")
    if "spf" in attrs:
        parts.append(f"SPF{attrs['spf']} PA{attrs.get('pa', '')}")
    return "，".join(parts) + "。演示数据，非真实商品。"


PRODUCTS = [
                                           
    P("bw-001", "氨基酸温和沐浴露", "清岚", "沐浴露", 69, 89, 4.7, 2380,
      {"skin_type": "敏感肌", "scent": "无香", "function": "保湿", "volume_ml": 500,
       "key_ingredients": ["氨基酸", "神经酰胺"]},
      ["洗后不紧绷", "泡沫细腻", "无香精"], ["泵头偏紧"], ["敏感肌", "无香", "保湿"]),
    P("bw-002", "净透控油沐浴露", "沐野", "沐浴露", 59, 79, 4.5, 1860,
      {"skin_type": "油性", "scent": "柑橘", "function": "控油", "volume_ml": 500,
       "key_ingredients": ["水杨酸", "茶树"]},
      ["清爽", "控油持久", "柑橘香清新"], ["干皮会紧绷"], ["油皮", "控油", "清爽"]),
    P("bw-003", "神经酰胺修护沐浴露", "简植", "沐浴露", 89, 109, 4.8, 960,
      {"skin_type": "敏感肌", "scent": "无香", "function": "修护", "volume_ml": 400,
       "key_ingredients": ["神经酰胺", "泛醇"]},
      ["修护屏障", "温和", "无香"], ["价格偏高"], ["敏感肌", "修护", "无香"]),
    P("bw-004", "海盐磨砂沐浴露", "海屿", "沐浴露", 79, 99, 4.3, 3200,
      {"skin_type": "中性", "scent": "木质", "function": "清洁", "volume_ml": 500,
       "key_ingredients": ["海盐", "甘油"]},
      ["磨砂细腻", "香味高级"], ["敏感肌慎用", "颗粒感明显"], ["磨砂", "木质香"]),
    P("bw-005", "氨基酸云朵沐浴露", "初本", "沐浴露", 49, 69, 4.4, 5200,
      {"skin_type": "干性", "scent": "花香", "function": "保湿", "volume_ml": 500,
       "key_ingredients": ["氨基酸", "玻尿酸"]},
      ["便宜大碗", "泡沫丰富", "花香淡雅"], ["留香一般"], ["干皮", "花香", "性价比"]),
    P("bw-006", "果酸焕肤沐浴露", "研白", "沐浴露", 99, 129, 4.2, 780,
      {"skin_type": "油性", "scent": "果香", "function": "去角质", "volume_ml": 300,
       "key_ingredients": ["果酸", "烟酰胺"]},
      ["去鸡皮", "果香清新"], ["需要防晒", "敏感肌刺痛"], ["油皮", "果酸", "去角质"]),
    P("bw-007", "婴儿级无泪沐浴露", "云栖", "沐浴露", 99, 119, 4.9, 1500,
      {"skin_type": "敏感肌", "scent": "无香", "function": "温和", "volume_ml": 400,
       "key_ingredients": ["氨基酸", "燕麦"]},
      ["婴儿可用", "无泪配方", "极简成分"], ["清洁力偏弱"], ["敏感肌", "婴童", "无香"]),
    P("bw-008", "咖啡因醒肤沐浴露", "素造", "沐浴露", 45, 59, 4.0, 2100,
      {"skin_type": "中性", "scent": "木质", "function": "清爽", "volume_ml": 500,
       "key_ingredients": ["咖啡因", "薄荷"]},
      ["提神", "便宜"], ["薄荷刺激", "冬天偏凉"], ["清爽", "薄荷", "性价比"]),

                                           
    P("hs-001", "氨基酸控油洗发水", "清岚", "洗发水", 79, 99, 4.6, 3100,
      {"hair_type": "油性", "function": "控油", "scent": "柑橘", "volume_ml": 500,
       "key_ingredients": ["氨基酸", "吡啶硫酮锌"]},
      ["控油两天", "蓬松", "柑橘香"], ["发尾略干"], ["油头", "控油", "蓬松"]),
    P("hs-002", "去屑净爽洗发水", "沐野", "洗发水", 69, 89, 4.5, 4200,
      {"hair_type": "油性", "function": "去屑", "scent": "薄荷", "volume_ml": 500,
       "key_ingredients": ["吡啶硫酮锌", "薄荷"]},
      ["去屑明显", "清凉"], ["薄荷味重"], ["去屑", "油头", "薄荷"]),
    P("hs-003", "敏感头皮修护洗发水", "简植", "洗发水", 99, 119, 4.7, 860,
      {"hair_type": "干性", "function": "修护", "scent": "无香", "volume_ml": 400,
       "key_ingredients": ["神经酰胺", "泛醇"]},
      ["头皮不痒", "无香", "温和"], ["起泡少"], ["敏感头皮", "修护", "无香"]),
    P("hs-004", "海盐蓬松洗发水", "海屿", "洗发水", 89, 109, 4.4, 1900,
      {"hair_type": "中性", "function": "蓬松", "scent": "木质", "volume_ml": 500,
       "key_ingredients": ["海盐", "水解蛋白"]},
      ["蓬松", "海盐香"], ["清洁力偏强"], ["蓬松", "中性发质"]),
    P("hs-005", "玻尿酸保湿洗发水", "初本", "洗发水", 59, 79, 4.3, 2800,
      {"hair_type": "干性", "function": "保湿", "scent": "花香", "volume_ml": 500,
       "key_ingredients": ["玻尿酸", "角蛋白"]},
      ["顺滑", "便宜", "花香"], ["油头不适用"], ["干发", "保湿", "性价比"]),
    P("hs-006", "咖啡因防脱洗发水", "研白", "洗发水", 119, 149, 4.2, 650,
      {"hair_type": "中性", "function": "修护", "scent": "木质", "volume_ml": 300,
       "key_ingredients": ["咖啡因", "生姜"]},
      ["掉发减少", "木质香"], ["价格高", "效果慢"], ["防脱", "修护"]),

                                          
    P("fc-001", "神经酰胺修护面霜", "简植", "面霜", 129, 159, 4.8, 1800,
      {"skin_type": "敏感肌", "function": "修护", "texture": "滋润", "volume_ml": 50,
       "key_ingredients": ["神经酰胺", "角鲨烷"]},
      ["修护泛红", "滋润不腻", "敏感肌友好"], ["夏天偏厚"], ["敏感肌", "修护", "滋润"]),
    P("fc-002", "清爽保湿面霜", "清岚", "面霜", 89, 109, 4.5, 2400,
      {"skin_type": "油性", "function": "保湿", "texture": "清爽", "volume_ml": 50,
       "key_ingredients": ["玻尿酸", "甘油"]},
      ["清爽", "不搓泥", "妆前可用"], ["冬天保湿不够"], ["油皮", "清爽", "保湿"]),
    P("fc-003", "烟酰胺提亮面霜", "研白", "面霜", 149, 189, 4.4, 920,
      {"skin_type": "中性", "function": "美白", "texture": "清爽", "volume_ml": 50,
       "key_ingredients": ["烟酰胺", "VC"]},
      ["提亮", "质地轻盈"], ["需建立耐受", "敏感肌慎用"], ["美白", "提亮"]),
    P("fc-004", "玻尿酸水润面霜", "云栖", "面霜", 69, 89, 4.3, 3600,
      {"skin_type": "干性", "function": "保湿", "texture": "滋润", "volume_ml": 50,
       "key_ingredients": ["玻尿酸", "泛醇"]},
      ["便宜", "补水明显"], ["香精味"], ["干皮", "保湿", "性价比"]),
    P("fc-005", "海藻舒缓面霜", "海屿", "面霜", 159, 199, 4.6, 540,
      {"skin_type": "敏感肌", "function": "修护", "texture": "清爽", "volume_ml": 50,
       "key_ingredients": ["海藻", "积雪草"]},
      ["舒缓", "清爽", "海洋香"], ["价格高", "评价少"], ["敏感肌", "舒缓"]),
    P("fc-006", "视黄醇抗初老面霜", "沐野", "面霜", 199, 239, 4.1, 310,
      {"skin_type": "中性", "function": "抗老", "texture": "滋润", "volume_ml": 50,
       "key_ingredients": ["视黄醇", "胜肽"]},
      ["细纹改善"], ["刺激", "需避光", "评价少"], ["抗老", "视黄醇"]),

                                           
    P("fs-001", "轻透防晒乳", "清岚", "防晒霜", 99, 129, 4.6, 2800,
      {"skin_type": "敏感肌", "texture": "清爽", "volume_ml": 50, "spf": 50, "pa": "++++",
       "key_ingredients": ["氧化锌", "烟酰胺"]},
      ["不假白", "成膜快", "敏感肌可用"], ["需卸妆"], ["敏感肌", "清爽", "SPF50"]),
    P("fs-002", "控油防晒霜", "沐野", "防晒霜", 79, 99, 4.4, 1900,
      {"skin_type": "油性", "texture": "清爽", "volume_ml": 50, "spf": 50, "pa": "+++",
       "key_ingredients": ["水杨酸", "硅石"]},
      ["控油", "哑光"], ["略搓泥"], ["油皮", "控油", "SPF50"]),
    P("fs-003", "物理防晒乳", "简植", "防晒霜", 119, 139, 4.7, 760,
      {"skin_type": "敏感肌", "texture": "滋润", "volume_ml": 40, "spf": 30, "pa": "+++",
       "key_ingredients": ["氧化锌", "二氧化钛"]},
      ["纯物理", "温和", "孕妇可用"], ["略泛白", "价格高"], ["敏感肌", "物理防晒", "SPF30"]),
    P("fs-004", "水感防晒喷雾", "海屿", "防晒霜", 69, 89, 4.2, 4100,
      {"skin_type": "中性", "texture": "清爽", "volume_ml": 150, "spf": 50, "pa": "++++",
       "key_ingredients": ["化学防晒剂"]},
      ["方便补涂", "清爽"], ["喷雾不均匀", "不能上飞机"], ["喷雾", "清爽", "SPF50"]),
    P("fs-005", "儿童防晒霜", "云栖", "防晒霜", 89, 109, 4.8, 1200,
      {"skin_type": "敏感肌", "texture": "滋润", "volume_ml": 50, "spf": 30, "pa": "+++",
       "key_ingredients": ["氧化锌", "燕麦"]},
      ["儿童可用", "温和", "无香"], ["泛白", "质地厚"], ["儿童", "敏感肌", "SPF30"]),
    P("fs-006", "美白防晒乳", "研白", "防晒霜", 129, 159, 4.3, 880,
      {"skin_type": "中性", "texture": "清爽", "volume_ml": 50, "spf": 50, "pa": "++++",
       "key_ingredients": ["烟酰胺", "VC"]},
      ["提亮", "不油腻"], ["敏感肌刺痛"], ["美白", "SPF50"]),

                                          
    P("tp-001", "抗敏修护牙膏", "清岚", "牙膏", 39, 49, 4.6, 3200,
      {"function": "抗敏", "flavor": "薄荷", "volume_ml": 120,
       "key_ingredients": ["硝酸钾", "氟化钠"]},
      ["抗敏明显", "泡沫适中"], ["薄荷偏辣"], ["抗敏", "薄荷"]),
    P("tp-002", "美白去渍牙膏", "沐野", "牙膏", 29, 39, 4.3, 5600,
      {"function": "美白", "flavor": "薄荷", "volume_ml": 120,
       "key_ingredients": ["水合硅石", "焦磷酸盐"]},
      ["去茶渍", "便宜"], ["敏感牙酸痛"], ["美白", "去渍", "性价比"]),
    P("tp-003", "益生菌清新牙膏", "简植", "牙膏", 49, 59, 4.5, 1400,
      {"function": "清新", "flavor": "蜜桃", "volume_ml": 100,
       "key_ingredients": ["益生菌", "木糖醇"]},
      ["口气清新", "蜜桃味"], ["泡沫少"], ["清新", "蜜桃"]),
    P("tp-004", "儿童防蛀牙膏", "云栖", "牙膏", 35, 45, 4.8, 2100,
      {"function": "防蛀", "flavor": "蜜桃", "volume_ml": 60,
       "key_ingredients": ["氟化钠", "木糖醇"]},
      ["儿童喜欢", "低氟安全"], ["容量小"], ["儿童", "防蛀", "蜜桃"]),
    P("tp-005", "酵素亮白牙膏", "研白", "牙膏", 59, 69, 4.1, 780,
      {"function": "美白", "flavor": "绿茶", "volume_ml": 100,
       "key_ingredients": ["酵素", "绿茶提取物"]},
      ["温和", "绿茶味"], ["美白慢", "价格高"], ["美白", "绿茶"]),

                                           
    P("ld-001", "除菌洗衣液", "清岚", "洗衣液", 59, 79, 4.7, 4800,
      {"function": "除菌", "scent": "花香", "volume_ml": 3000,
       "key_ingredients": ["除菌因子", "酶"]},
      ["除菌", "留香", "便宜"], ["花香偏浓"], ["除菌", "花香", "大容量"]),
    P("ld-002", "婴童洗衣液", "沐野", "洗衣液", 79, 99, 4.8, 2300,
      {"function": "除菌", "scent": "无香", "volume_ml": 2000,
       "key_ingredients": ["氨基酸表面活性剂"]},
      ["婴童可用", "无香", "温和"], ["价格偏高"], ["婴童", "无香", "温和"]),
    P("ld-003", "留香洗衣液", "简植", "洗衣液", 49, 69, 4.4, 3600,
      {"function": "留香", "scent": "花香", "volume_ml": 3000,
       "key_ingredients": ["香氛微胶囊"]},
      ["留香久", "便宜"], ["香味浓"], ["留香", "花香", "性价比"]),
    P("ld-004", "运动衣物洗衣液", "海屿", "洗衣液", 69, 89, 4.5, 1100,
      {"function": "除菌", "scent": "木质", "volume_ml": 2000,
       "key_ingredients": ["酶", "除菌因子"]},
      ["去汗味", "木质香"], ["去油一般"], ["运动", "除菌", "木质"]),
    P("ld-005", "内衣专用洗衣液", "云栖", "洗衣液", 45, 59, 4.6, 900,
      {"function": "除菌", "scent": "无香", "volume_ml": 500,
       "key_ingredients": ["蛋白酶", "茶树"]},
      ["内衣专用", "无香", "温和"], ["容量小"], ["内衣", "无香", "除菌"]),
]


def make_reviews() -> list[dict]:
    reviews: list[dict] = []
    authors = ["小*", "用户****", "匿*", "阿*", "木*"]
    for index, product in enumerate(PRODUCTS):
        pros = product["pros"]
        cons = product["cons"]
        contents = [
            f"{pros[0]}，{pros[1] if len(pros) > 1 else '整体满意'}，会回购。",
            f"整体不错，{pros[0]}；如果能改进{cons[0]}就更好了。",
            f"{cons[0]}，可能不适合我。",
        ]
        ratings = [5, 4, 3]
        for offset, (content, rating) in enumerate(zip(contents, ratings, strict=True)):
            reviews.append(
                {
                    "product_id": product["id"],
                    "rating": rating,
                    "content": content,
                    "author": authors[(index + offset) % len(authors)],
                }
            )
    return reviews


def main() -> None:
    payload = {"products": PRODUCTS, "reviews": make_reviews()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(PRODUCTS)} products and {len(payload['reviews'])} reviews to {OUT}")


if __name__ == "__main__":
    main()
