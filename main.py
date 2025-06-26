# main.py
import json
import time
import os
from gate_api import ApiClient, Configuration, SpotApi
from decimal import Decimal

# إعداد الاتصال بـ Gate.io
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
configuration = Configuration(key=api_key, secret=api_secret)
api_client = ApiClient(configuration)
spot_api = SpotApi(api_client)

# تحميل الإعدادات من ملف JSON
def load_settings():
    with open("settings.json", "r") as f:
        return json.load(f)

# تنفيذ أمر شراء Limit
def place_limit_order(symbol, price, amount):
    try:
        order = spot_api.create_order({
            "currency_pair": symbol,
            "type": "limit",
            "side": "buy",
            "amount": str(amount),
            "price": str(price),
            "time_in_force": "gtc"
        })
        print(f"وضع أمر شراء ل {symbol} عند {price} بمبلغ {amount}")
        return order
    except Exception as e:
        print("خطأ في أمر limit:", e)
        return None

# تنفيذ أمر Market
def place_market_order(symbol, amount):
    try:
        order = spot_api.create_order({
            "currency_pair": symbol,
            "type": "market",
            "side": "buy",
            "amount": str(amount)
        })
        print(f"تم شراء {symbol} ماركت بمبلغ {amount}")
        return order
    except Exception as e:
        print("خطأ في أمر market:", e)
        return None

# تنفيذ أمر بيع بربح محدد
def place_take_profit_order(symbol, buy_price, amount, profit_percent):
    try:
        target_price = Decimal(buy_price) * (1 + Decimal(profit_percent) / 100)
        order = spot_api.create_order({
            "currency_pair": symbol,
            "type": "limit",
            "side": "sell",
            "amount": str(amount),
            "price": str(target_price.quantize(Decimal("0.0000001"))),
            "time_in_force": "gtc"
        })
        print(f"أمر بيع بربح {profit_percent}% ل {symbol} عند {target_price}")
        return order
    except Exception as e:
        print("خطأ في أمر البيع:", e)
        return None

# دالة رئيسية لتكرار المراقبة والتنفيذ
def run_bot():
    while True:
        settings = load_settings()

        for coin in ["FARTCOIN5S", "FARTCOIN5L"]:
            opposite = "FARTCOIN5L" if coin == "FARTCOIN5S" else "FARTCOIN5S"
            levels = settings[coin]["levels"]
            amounts = settings[coin]["amounts"]
            profit = settings["take_profit_percent"]

            # جلب سعر السوق الحالي
            try:
                ticker = spot_api.list_tickers(currency_pair=coin + "_USDT")[0]
                current_price = Decimal(ticker.last)
            except:
                print(f"لم يتم جلب السعر الحالي لـ {coin}")
                continue

            for i in range(3):
                level_price = Decimal(str(levels[i]))
                amount = Decimal(str(amounts[i]))

                if current_price <= level_price:
                    print(f"السعر الحالي لـ {coin} = {current_price}, أقل من أو يساوي {level_price}")

                    # شراء العملة الحالية Limit
                    limit_order = place_limit_order(coin + "_USDT", level_price, amount)
                    if not limit_order:
                        continue

                    # شراء العملة المقابلة Market
                    market_order = place_market_order(opposite + "_USDT", amount)
                    if not market_order:
                        continue

                    # بيع العملة الثانية عند ربح معين
                    if hasattr(market_order, "avg_deal_price"):
                        place_take_profit_order(opposite + "_USDT", Decimal(market_order.avg_deal_price), amount, profit)

        time.sleep(30)

if __name__ == "__main__":
    run_bot()
