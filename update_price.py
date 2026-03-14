# VERSION 7 - SELF-CORRECTING (NO DRIFT)
import os
import requests
import json

# Configuration from Environment Variables (GitHub Secrets)
SHOP_DOMAIN = os.environ.get('SHOP_DOMAIN')
API_KEY = os.environ.get('API_KEY')
API_PASSWORD = os.environ.get('API_PASSWORD')
PRODUCT_ID = os.environ.get('PRODUCT_ID')
VARIANT_ID = os.environ.get('VARIANT_ID')

TARGET_GBP_PRICE = 179.00
TARGET_GBP_COMPARE_PRICE = 449.00

# CORRECTION FACTOR: PlusBase's internal rate is ~3.4% worse than mid-market.
# We multiply by 0.966 to offset this and hit exactly £179.00.
CORRECTION_FACTOR = 0.966 

def get_exchange_rate():
    """Fetch the current mid-market GBP to USD exchange rate."""
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/GBP" )
        data = response.json()
        return data['rates']['USD']
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
        return None

def update_plusbase_price(new_usd_price, new_usd_compare_price):
    """Update the product variant price via ShopBase/PlusBase Admin API."""
    clean_domain = SHOP_DOMAIN.replace("https://", "" ).replace("http://", "" ).strip("/")
    url = f"https://{API_KEY}:{API_PASSWORD}@{clean_domain}/admin/variants/{VARIANT_ID}.json"
    
    try:
        v_id = int(str(VARIANT_ID ).strip())
    except:
        print("Invalid Variant ID")
        exit(1)

    payload = {
        "variant": {
            "id": v_id,
            "price": round(new_usd_price, 2),
            "compare_at_price": round(new_usd_compare_price, 2)
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.put(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"SUCCESS: Updated to ${new_usd_price:.2f} USD")
        else:
            print(f"FAILED: {response.status_code} - {response.text}")
            exit(1)
    except Exception as e:
        print(f"Error calling PlusBase API: {e}")
        exit(1)

if __name__ == "__main__":
    # Check for missing variables
    for var in ['SHOP_DOMAIN', 'API_KEY', 'API_PASSWORD', 'PRODUCT_ID', 'VARIANT_ID']:
        if not os.environ.get(var):
            print(f"Error: Missing secret {var}")
            exit(1)

    rate = get_exchange_rate()
    if rate:
        print(f"--- VERSION 7 (SELF-CORRECTING) ---")
        print(f"Current Market Rate: {rate}")
        
        # Apply the correction factor to the USD price
        new_usd_price = (TARGET_GBP_PRICE * rate) * CORRECTION_FACTOR
        new_usd_compare_price = (TARGET_GBP_COMPARE_PRICE * rate) * CORRECTION_FACTOR
        
        print(f"Calculated USD Price (with 3.4% offset): ${new_usd_price:.2f}")
        update_plusbase_price(new_usd_price, new_usd_compare_price)
    else:
        print("Could not fetch exchange rate.")
        exit(1)
