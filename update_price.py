# VERSION 10 - SMART-CORRECTING (CLOSED-LOOP VERIFICATION)
import os
import requests
import json
import re
import time

# Configuration from Environment Variables (GitHub Secrets)
SHOP_DOMAIN = os.environ.get('SHOP_DOMAIN')
API_KEY = os.environ.get('API_KEY')
API_PASSWORD = os.environ.get('API_PASSWORD')
PRODUCT_ID = os.environ.get('PRODUCT_ID')
VARIANT_ID = os.environ.get('VARIANT_ID')

TARGET_GBP_PRICE = 179.00
TARGET_GBP_COMPARE_PRICE = 449.00
PRODUCT_URL = "https://buudy.com/products/buudy-led-mask"

def get_exchange_rate( ):
    """Fetch the current mid-market GBP to USD exchange rate."""
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/GBP" )
        data = response.json()
        return data['rates']['USD']
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
        return None

def check_live_gbp_price():
    """Check the actual GBP price shown on the live product page."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-GB,en;q=0.9" # Request UK version
    }
    try:
        # We add a timestamp to the URL to bypass any caching
        response = requests.get(f"{PRODUCT_URL}?t={int(time.time())}", headers=headers, timeout=15)
        if response.status_code == 200:
            # Search for £ followed by numbers in the page source
            matches = re.findall(r'£\s?(\d+\.?\d*)', response.text)
            if matches:
                # Filter out small numbers and look for something near 179
                potential_prices = [float(m) for m in matches if 150 < float(m) < 250]
                if potential_prices:
                    return potential_prices[0]
        print(f"Could not find GBP price on page. Status: {response.status_code}")
        return None
    except Exception as e:
        print(f"Error checking live price: {e}")
        return None

def update_plusbase_price(new_usd_price, new_usd_compare_price, attempt_name="Initial"):
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
            print(f"{attempt_name} Update SUCCESS: Set USD to ${new_usd_price:.2f}")
            return True
        else:
            print(f"{attempt_name} Update FAILED: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error calling PlusBase API: {e}")
        return False

if __name__ == "__main__":
    # Check for missing variables
    for var in ['SHOP_DOMAIN', 'API_KEY', 'API_PASSWORD', 'PRODUCT_ID', 'VARIANT_ID']:
        if not os.environ.get(var):
            print(f"Error: Missing secret {var}")
            exit(1)

    rate = get_exchange_rate()
    if not rate:
        exit(1)

    print(f"--- VERSION 10 (SMART-CORRECTING) ---")
    print(f"Current Market Rate: {rate}")
    
    # 1. Initial Update (using the last known good factor 0.977)
    initial_usd_price = (TARGET_GBP_PRICE * rate) * 0.977
    initial_usd_compare = (TARGET_GBP_COMPARE_PRICE * rate) * 0.977
    
    if update_plusbase_price(initial_usd_price, initial_usd_compare, "Initial"):
        # 2. Wait for PlusBase to process (5 seconds)
        print("Waiting 5 seconds for PlusBase to update...")
        time.sleep(5)
        
        # 3. Verify the result on the live website
        live_price = check_live_gbp_price()
        if live_price:
            print(f"Live Price on Website: £{live_price}")
            
            if abs(live_price - TARGET_GBP_PRICE) > 0.1:
                print(f"Price is OFF by £{live_price - TARGET_GBP_PRICE}. Correcting...")
                
                # 4. Calculate the exact correction needed
                effective_rate = initial_usd_price / live_price
                corrected_usd_price = TARGET_GBP_PRICE * effective_rate
                corrected_usd_compare = TARGET_GBP_COMPARE_PRICE * effective_rate
                
                print(f"New Corrected USD Price: ${corrected_usd_price:.2f}")
                update_plusbase_price(corrected_usd_price, corrected_usd_compare, "Correction")
            else:
                print("Price is PERFECT at £179.00. No correction needed.")
        else:
            print("Could not verify live price. Skipping correction.")
    else:
        exit(1)
