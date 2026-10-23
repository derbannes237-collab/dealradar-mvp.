
from datetime import datetime, timezone

DEFAULT_SETTINGS = {
    "capital": 1000,
    "max_buy": 500,
    "min_roi": 40,
    "max_age": 4,
}


def _num(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def enrich_listing(item):
    item = dict(item)
    buy = _num(item.get("buy_price"))
    buy_fees = _num(item.get("buy_fees"))
    repair = _num(item.get("repair_cost"))
    resale = _num(item.get("resale_price"))
    sell_fees = _num(item.get("sell_fees"))
    shipping = _num(item.get("outbound_shipping"))

    total_cost = buy + buy_fees + repair
    net_profit = resale - sell_fees - shipping - total_cost
    roi = (net_profit / total_cost * 100) if total_cost > 0 else -100.0
    max_buy = (resale - sell_fees - shipping) / 1.4 - buy_fees - repair

    item.update({
        "buy_price": buy,
        "buy_fees": buy_fees,
        "repair_cost": repair,
        "resale_price": resale,
        "sell_fees": sell_fees,
        "outbound_shipping": shipping,
        "total_cost": round(total_cost, 2),
        "net_profit": round(net_profit, 2),
        "roi_net_pct": round(roi, 2),
        "max_buy_price_for_40pct_roi": round(max_buy, 2),
        "data_origin": str(item.get("data_origin") or "IMPORTED").upper(),
    })
    return item


def validate_listing(item, max_buy=500, min_roi=40, max_age=4):
    try:
        age = float(item.get("model_age_years"))
    except (TypeError, ValueError):
        return False

    return (
        item.get("data_origin") != "DEMO"
        and 0 < float(item.get("buy_price", 0)) <= float(max_buy)
        and age >= 0
        and age <= float(max_age)
        and float(item.get("roi_net_pct", -100)) >= float(min_roi)
        and float(item.get("total_cost", 0)) <= 1000
    )

