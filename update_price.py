import os
import requests
import json

# Configuration from Environment Variables (GitHub Secrets )
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
        response = requests.get("https://api.exchangerate-api.com/v4/latest/GBP" )
        data = response.json()
        return data['rates']['USD']
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
        return None

def update_plusbase_price(new_usd_price, new_usd_compare_price):
    """Update the product variant price via ShopBase/PlusBase Admin API."""
    # Ensure the domain doesn't have https:// prefix for the basic auth URL
    clean_domain = SHOP_DOMAIN.replace("https://", "" ).replace("http://", "" ).strip("/")
    url = f"https://{API_KEY}:{API_PASSWORD}@{clean_domain}/admin/variants/{VARIANT_ID}.json"
    
    payload = {
        "variant": {
            "id": VARIANT_ID,
            "price": round(new_usd_price, 2 ),
            "compare_at_price": round(new_usd_compare_price, 2)
        }
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"Sending request to: https://{clean_domain}/admin/variants/{VARIANT_ID}.json" )
    print(f"Payload: {json.dumps(payload)}")
    
    try:
        response = requests.put(url, json=payload, headers=headers)
        print(f"Response Status Code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            updated_price = result.get('variant', {}).get('price')
            print(f"Successfully updated price to ${updated_price} USD")
            print(f"Full Response: {json.dumps(result)}")
        else:
            print(f"Failed to update price. Status: {response.status_code}, Response: {response.text}")
            # Exit with error so GitHub Action shows as failed
            exit(1)
    except Exception as e:
        print(f"Error calling PlusBase API: {e}")
        exit(1)

if __name__ == "__main__":
    # Check if all environment variables are present
    missing_vars = []
    for var in ['SHOP_DOMAIN', 'API_KEY', 'API_PASSWORD', 'PRODUCT_ID', 'VARIANT_ID']:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"Error: Missing environment variables: {', '.join(missing_vars)}")
        exit(1)

    rate = get_exchange_rate()
    if rate:
        print(f"Current GBP/USD Rate: {rate}")
        # Calculate USD price needed to maintain the GBP price
        new_usd_price = TARGET_GBP_PRICE * rate
        new_usd_compare_price = TARGET_GBP_COMPARE_PRICE * rate
        
        print(f"Calculated USD Price: ${new_usd_price:.2f}")
        update_plusbase_price(new_usd_price, new_usd_compare_price)
    else:
        print("Could not proceed without exchange rate.")
        exit(1)
