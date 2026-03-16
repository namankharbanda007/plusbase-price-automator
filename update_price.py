# VERSION 9 - FINAL ROBUST (FIXED GBP PRICE)
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

    # We send the USD price as the primary price, and also specify the GBP price 
    # in the presentment_prices field to ensure PlusBase locks it in.
    payload = {
        "variant": {
            "id": v_id,
            "price": round(new_usd_price, 2),
            "compare_at_price": round(new_usd_compare_price, 2),
            "presentment_prices": [
                {
                    "price": {"amount": str(round(new_usd_price, 2)), "currency_code": "USD"},
                    "compare_at_price": {"amount": str(round(new_usd_compare_price, 2)), "currency_code": "USD"}
                },
                {
                    "price": {"amount": str(TARGET_GBP_PRICE), "currency_code": "GBP"},
                    "compare_at_price": {"amount": str(TARGET_GBP_COMPARE_PRICE), "currency_code": "GBP"}
                }
            ]
        }
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.put(url, json=payload, headers=headers)
        if response.status_code == 200:
            print(f"SUCCESS: Updated to ${new_usd_price:.2f} USD (Target: £{TARGET_GBP_PRICE} GBP)")
            result = response.json()
            updated_price = result.get('variant', {}).get('price')
            print(f"PlusBase confirmed USD price: ${updated_price}")
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
        print(f"--- VERSION 9 (FINAL ROBUST) ---")
        print(f"Current Market Rate: {rate}")
        
        # We use a slightly adjusted rate (0.977) to ensure the USD price 
        # is in the right ballpark for PlusBase's internal conversion.
        # This helps the presentment_prices lock in more reliably.
        new_usd_price = (TARGET_GBP_PRICE * rate) * 0.977
        new_usd_compare_price = (TARGET_GBP_COMPARE_PRICE * rate) * 0.977
        
        update_plusbase_price(new_usd_price, new_usd_compare_price)
    else:
        print("Could not fetch exchange rate.")
        exit(1)
