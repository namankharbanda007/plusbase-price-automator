# VERSION 3 - FINAL ROBUST UPDATE
import os
import requests
import json

# Configuration from Environment Variables (GitHub Secrets)
SHOP_DOMAIN = os.environ.get('SHOP_DOMAIN')
API_KEY = os.environ.get('API_KEY')
API_PASSWORD = os.environ.get('API_PASSWORD')
PRODUCT_ID = os.environ.get('PRODUCT_ID')
VARIANT_ID = os.environ.get('VARIANT_ID')
TARGET_GBP_PRICE = 179.00  # Your fixed GBP price
TARGET_GBP_COMPARE_PRICE = 449.00 # Your fixed GBP compare-at price

def get_exchange_rate():
    """Fetch the current GBP to USD exchange rate from a free API."""
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
    
    # Using the most robust endpoint: /admin/products/{product_id}/variants/{variant_id}.json
    url = f"https://{API_KEY}:{API_PASSWORD}@{clean_domain}/admin/products/{PRODUCT_ID}/variants/{VARIANT_ID}.json"
    
    try:
        v_id = int(str(VARIANT_ID ).strip())
    except Exception as e:
        print(f"Error: VARIANT_ID '{VARIANT_ID}' is not a valid number: {e}")
        exit(1)

    payload = {
        "variant": {
            "id": v_id,
            "price": round(new_usd_price, 2),
            "compare_at_price": round(new_usd_compare_price, 2)
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"--- VERSION 3 START ---")
    print(f"Updating Product: {PRODUCT_ID}, Variant: {v_id}")
    print(f"Calculated USD Price: ${new_usd_price:.2f}")
    
    try:
        response = requests.put(url, json=payload, headers=headers)
        print(f"Response Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            updated_price = result.get('variant', {}).get('price')
            print(f"SUCCESS: Updated price to ${updated_price} USD")
        else:
            print(f"FAILED: {response.status_code} - {response.text}")
            # If the product-specific URL fails, try the direct variant URL as a backup
            print("Trying backup URL...")
            backup_url = f"https://{API_KEY}:{API_PASSWORD}@{clean_domain}/admin/variants/{VARIANT_ID}.json"
            response = requests.put(backup_url, json=payload, headers=headers )
            if response.status_code == 200:
                print("SUCCESS via backup URL")
            else:
                print(f"BACKUP FAILED: {response.status_code} - {response.text}")
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
        print(f"Current GBP/USD Rate: {rate}")
        new_usd_price = TARGET_GBP_PRICE * rate
        new_usd_compare_price = TARGET_GBP_COMPARE_PRICE * rate
        update_plusbase_price(new_usd_price, new_usd_compare_price)
    else:
        print("Could not fetch exchange rate.")
        exit(1)
