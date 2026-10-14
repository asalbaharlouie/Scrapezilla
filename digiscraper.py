import time
import random
import requests
import pandas as pd


CATEGORY = "mobile-phone"    
BRAND = "samsung"            
OUTPUT_FILE = "digikala_samsung.csv"
MAX_PAGES = None                              

SITE = "https://www.digikala.com"
URL = (
    "https://api.digikala.com/discovery/api/v1/"
    f"categories/{CATEGORY}/brands/{BRAND}/products"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64)"
        "AppleWebkit/537.36 (KHTML, like Gecko)"
        "Chrome/152.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*"
}

def get_page(page):
    params = {"page": page, "view_type": "listing"}

    for attempt in range(3):
        try:
            response = requests.get(URL,  params=params, headers=HEADERS, timeout=15)
        except requests.RequestException:
            print(" The internet is taking a little nap. Lets give it 10 minutes!:)")
            time.sleep(10)
            continue

        if response.status_code == 200:
            return response.json()

        if response.status_code in (403, 404):
            print("Status code", response.status_code, "- Stopping.")
            return None

        print("Status code", response.status_code, "-_Waiting 30 seconds before retrying.")
        time.sleep(30)

    print("All retry attempts failed for page", page)
    return None

def creat_product_row(product):
    product_variant = product.get("default_variant") or {}
    price = product_variant.get("price") or {}
    seller = product_variant.get("seller") or {}
    warranty = product_variant.get("warranty") or {}
    color = product_variant.get("color") or {}
    rating = product.get("rating") or {}
    url_info = product.get("url") or {}

    rial = price.get("selling_price")
    if rial is not None:
        toman = rial // 10
    else: 
        toman = None

    uri = url_info.get("uri")
    if uri:
        link = "https://www.digikala.com" + uri
    else: 
        link = None

    return {
    "id": product.get("id"),
    "title_fa": product.get("title_fa"),
    "title_en": product.get("title_en"),
    "price_rial": rial,
    "price_toman": toman,
    "discount_percent": price.get("discount_percent"),
    "rating_rate": rating.get("rate"),
    "seller": seller.get("title"),
    "warranty": warranty.get("title"),
    "color": color.get("title"),
    "url": link,
    "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
}

def save_files(collected_products):
    table = pd.DataFrame(list(collected_products.values()))
    table.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("Saved:", len(collected_products), "products")


def main():
    collected_products = {}  

    first_page = get_page(1)
    if first_page is None:
        print("Failed to retrieve the first page.")
        return

    total_pages = first_page.get("data", {}).get("pager", {}).get("total_pages", 1)
    print("Total pages:", total_pages)

    last_page = total_pages
    if MAX_PAGES is not None and MAX_PAGES < total_pages:
        last_page = MAX_PAGES

    for page in range(1, last_page + 1):
        if page == 1:
            data = first_page
        else:
            time.sleep(random.uniform(2, 4))
            data = get_page(page)

        if data is None:
            print("Failed to retrieve page", page, "- Stopping.")
            break

        products = data.get("data", {}).get("products", [])
        if len(products) == 0:
            print("The page is empty. Stopping.")
            break

        for product in products:
            properties = product.get("properties") or {}
            if properties.get("is_ad"):
                continue

            collected_products[product.get("id")] = creat_product_row(product)

        print(
            "Page", page, "of", last_page,
            "- Total products:", len(collected_products)
        )

        if page % 5 == 0:
            save_files(collected_products)

    if len(collected_products) > 0:
        save_files(collected_products)


main()