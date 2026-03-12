import os
import requests
import json

# Configuration from Environment Variables (GitHub Secrets)
SHOP_DOMAIN = os.environ.get('SHOP_DOMAIN') # e.g., your-store.onshopbase.com
API_KEY = os.environ.get('API_KEY')
API_PASSWORD = os.environ.get('API_PASSWORD')
PRODUCT_ID = os.environ.get('PRODUCT_ID')
VARIANT_ID = os.environ.get('VARIANT_ID')
TARGET_GBP_PRICE = 179.00  # Your fixed GBP price
TARGET_GBP_COMPARE_PRICE = 449.00 # Your fixed GBP compare-at price

def get_exchange_rate():
    """Fetch the current GBP to USD exchange rate from a free API."""
    try:
        # Using a reliable free API (no key required for basic use)
        response = requests.get("https://api.exchangerate-api.com/v4/latest/GBP")
        data = response.json()
        return data['rates']['USD']
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
        return None

def update_plusbase_price(new_usd_price, new_usd_compare_price):
    """Update the product variant price via ShopBase/PlusBase Admin API."""
    url = f"https://{API_KEY}:{API_PASSWORD}@{SHOP_DOMAIN}/admin/variants/{VARIANT_ID}.json"
    
    payload = {
        "variant": {
            "id": VARIANT_ID,
            "price": round(new_usd_price, 2),
            "compare_at_price": round(new_usd_compare_price, 2)
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.put(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"Successfully updated price to ${new_usd_price:.2f} USD")
        else:
            print(f"Failed to update price. Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error calling PlusBase API: {e}")

if __name__ == "__main__":
    rate = get_exchange_rate()
    if rate:
        print(f"Current GBP/USD Rate: {rate}")
        # Calculate USD price needed to maintain the GBP price
        # If 1 GBP = X USD, then Y GBP = Y * X USD
        new_usd_price = TARGET_GBP_PRICE * rate
        new_usd_compare_price = TARGET_GBP_COMPARE_PRICE * rate
        
        print(f"Calculated USD Price: ${new_usd_price:.2f}")
        update_plusbase_price(new_usd_price, new_usd_compare_price)
    else:
        print("Could not proceed without exchange rate.")
