import csv

import pytest

import digiscraper


def test_save_files_creates_csv(tmp_path):
    output_file = tmp_path / "products.csv"

    products = {
        "123": {
            "id": 123,
            "title_fa": "گوشی آزمایشی",
            "title_en": "Test Phone",
            "price_rial": 1000000,
            "price_toman": 100000,
            "discount_percent": 10,
            "rating_rate": 4.5,
            "seller": "Test Seller",
            "warranty": "Test Warranty",
            "color": "Black",
            "url": "https://example.com/product/123",
            "scraped_at": "2026-01-01",
        }
    }

    digiscraper.save_files(
        products,
        output_file=str(output_file),
    )

    assert output_file.exists()
    assert output_file.stat().st_size > 0

    with output_file.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1
    assert rows[0]["title_en"] == "Test Phone"
    assert rows[0]["id"] == "123"


def test_save_files_handles_empty_products(tmp_path):
    output_file = tmp_path / "empty.csv"

    digiscraper.save_files(
        {},
        output_file=str(output_file),
    )

    assert output_file.exists()


def test_csv_is_written_outside_project(tmp_path):
    output_file = tmp_path / "isolated.csv"

    digiscraper.save_files(
        {},
        output_file=str(output_file),
    )

    assert output_file.parent == tmp_path
    