import time
import random
import requests
import pandas as pd


CATEGORY = "mobile-phone"
BRAND = "samsung"
OUTPUT_FILE = "digikala_products.csv"
MAX_PAGES = None

SITE = "https://www.digikala.com"
API_URL = "https://api.digikala.com/discovery/api/v1/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/152.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*"
}


def get_page(page, category=None, brand=None):
    category = category or CATEGORY
    brand = brand or BRAND

    url = f"{API_URL}categories/{category}/brands/{brand}/products"
    params = {"page": page, "view_type": "listing"}

    for attempt in range(3):
        try:
            response = requests.get(
                url,
                params=params,
                headers=HEADERS,
                timeout=15
            )

        except requests.RequestException as error:
            print(f"Network error on page {page}: {error}")
            time.sleep(10)
            continue

        if response.status_code == 200:
            try:
                return response.json()
            except ValueError:
                print(f"Invalid JSON response on page {page}.")
                return None

        if response.status_code in (403, 404):
            print(f"Status code {response.status_code} - Stopping.")
            return None

        print(
            f"Status code {response.status_code} - "
            "Waiting 30 seconds before retrying."
        )
        time.sleep(30)

    print(f"All retry attempts failed for page {page}.")
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
    toman = rial // 10 if rial is not None else None

    uri = url_info.get("uri")
    link = SITE + uri if uri else None

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


def save_files(collected_products, output_file=None):
    output_file = output_file or OUTPUT_FILE

    table = pd.DataFrame(list(collected_products.values()))

    table.to_csv(
        output_file,
        index=False,
        encoding="utf-8-sig"
    )

    print("Saved:", len(collected_products), "products to", output_file)


def scrape_products(
    category=None,
    brand=None,
    max_pages=None,
    progress_callback=None,
    output_file=None
):
    """
    Scrape products for a selected category and brand.

    progress_callback receives:
    (current_page, total_pages, products_collected, status_message)
    """
    category = category or CATEGORY
    brand = brand or BRAND
    output_file = output_file or OUTPUT_FILE

    collected_products = {}

    first_page = get_page(1, category, brand)

    if first_page is None:
        if progress_callback:
            progress_callback(
                0, 0, 0,
                "Failed to retrieve the first page."
            )
        return collected_products

    total_pages = (
        first_page.get("data", {})
        .get("pager", {})
        .get("total_pages", 1)
    )

    last_page = total_pages

    if max_pages is not None:
        last_page = min(max(0, max_pages), total_pages)

    if last_page == 0:
        if progress_callback:
            progress_callback(0, total_pages, 0, "No pages selected.")
        return collected_products

    if progress_callback:
        progress_callback(0, last_page, 0, "Scraping started.")

    for page in range(1, last_page + 1):
        if page == 1:
            data = first_page
        else:
            time.sleep(random.uniform(2, 4))
            data = get_page(page, category, brand)

        if data is None:
            if progress_callback:
                progress_callback(
                    page, last_page, len(collected_products),
                    f"Failed to retrieve page {page}. Stopping."
                )
            break

        products = data.get("data", {}).get("products", [])

        if not products:
            if progress_callback:
                progress_callback(
                    page, last_page, len(collected_products),
                    "The page is empty. Stopping."
                )
            break

        for product in products:
            properties = product.get("properties") or {}

            if properties.get("is_ad"):
                continue

            product_id = product.get("id")

            if product_id is not None:
                collected_products[product_id] = creat_product_row(product)

        print(
            "Page", page, "of", last_page,
            "- Total products:", len(collected_products)
        )

        if progress_callback:
            progress_callback(
                page, last_page, len(collected_products),
                f"Scraped page {page} of {last_page}."
            )

        if page % 5 == 0:
            save_files(collected_products, output_file)

    if collected_products:
        save_files(collected_products, output_file)

    if progress_callback:
        progress_callback(
            last_page, last_page, len(collected_products),
            "Scraping completed."
        )

    return collected_products


def main():
    collected_products = scrape_products(
        category=CATEGORY,
        brand=BRAND,
        max_pages=MAX_PAGES
    )
    print("Total collected:", len(collected_products))


if __name__ == "__main__":
    main()
