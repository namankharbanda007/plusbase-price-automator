# VERSION 5 - FINAL CALIBRATION
import os
import requests
import json

# Configuration
SHOP_DOMAIN = os.environ.get('SHOP_DOMAIN')
API_KEY = os.environ.get('API_KEY')
API_PASSWORD = os.environ.get('API_PASSWORD')
PRODUCT_ID = os.environ.get('PRODUCT_ID')
VARIANT_ID = os.environ.get('VARIANT_ID')

TARGET_GBP_PRICE = 179.00
TARGET_GBP_COMPARE_PRICE = 449.00

# ADJUSTMENT FACTOR: PlusBase adds a fee to the exchange rate. 
# We multiply by 0.972 to offset their ~2.8% fee and hit exactly £179.
FEE_ADJUSTMENT = 0.972 

def get_exchange_rate():
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/GBP" )
        data = response.json()
        return data['rates']['USD']
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
        return None

def update_plusbase_price(new_usd_price, new_usd_compare_price):
    clean_domain = SHOP_DOMAIN.replace("https://", "" ).replace("http://", "" ).strip("/")
    url = f"https://{API_KEY}:{API_PASSWORD}@{clean_domain}/admin/products/{PRODUCT_ID}/variants/{VARIANT_ID}.json"
    
    try:
        v_id = int(str(VARIANT_ID ).strip())
    except:
        exit(1)

    payload = {
        "variant": {
            "id": v_id,
            "price": round(new_usd_price, 2),
            "compare_at_price": round(new_usd_compare_price, 2)
        }
    }
    
    print(f"--- VERSION 5 (CALIBRATED) ---")
    print(f"Calculated USD Price (with fee offset): ${new_usd_price:.2f}")
    
    try:
        response = requests.put(url, json=payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            print(f"SUCCESS: Updated to ${new_usd_price:.2f} USD")
        else:
            print(f"FAILED: {response.text}")
            exit(1)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    rate = get_exchange_rate()
    if rate:
        # Apply the adjustment factor to the USD price
        new_usd_price = (TARGET_GBP_PRICE * rate) * FEE_ADJUSTMENT
        new_usd_compare_price = (TARGET_GBP_COMPARE_PRICE * rate) * FEE_ADJUSTMENT
        update_plusbase_price(new_usd_price, new_usd_compare_price)
