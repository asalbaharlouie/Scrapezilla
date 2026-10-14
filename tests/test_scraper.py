from unittest.mock import Mock, patch

import pytest
import requests

import digiscraper


def fake_response(status_code=200, payload=None):
    response = Mock()
    response.status_code = status_code
    response.json.return_value = payload or {}
    response.raise_for_status.return_value = None
    return response


@patch("digiscraper.requests.get")
def test_get_page_uses_mocked_network(mock_get):
    mock_get.return_value = fake_response(
        payload={"data": {"products": [], "pager": {"total_pages": 1}}}
    )

    result = digiscraper.get_page(
        1,
        category="mobile-phone",
        brand="samsung",
    )

    mock_get.assert_called()
    assert result is not None


@patch("digiscraper.requests.get")
def test_get_page_does_not_make_real_request(mock_get):
    mock_get.return_value = fake_response(payload={"data": {}})

    digiscraper.get_page(
        1,
        category="mobile-phone",
        brand="samsung",
    )

    assert mock_get.call_count >= 1


@patch("digiscraper.requests.get")
def test_get_page_handles_http_403(mock_get):
    mock_get.return_value = fake_response(status_code=403)

    result = digiscraper.get_page(
        1,
        category="mobile-phone",
        brand="samsung",
    )

    assert result is None


@patch("digiscraper.requests.get")
def test_get_page_handles_http_404(mock_get):
    mock_get.return_value = fake_response(status_code=404)

    result = digiscraper.get_page(
        1,
        category="mobile-phone",
        brand="samsung",
    )

    assert result is None


@patch("digiscraper.time.sleep")
@patch("digiscraper.requests.get")
def test_get_page_handles_network_failure(mock_get, mock_sleep):
    mock_get.side_effect = requests.Timeout("Simulated timeout")

    result = digiscraper.get_page(
        1,
        category="mobile-phone",
        brand="samsung",
    )

    assert result is None
    assert mock_get.call_count >= 1


def test_create_product_row_handles_minimal_product():
    product = {"id": 123}

    row = digiscraper.creat_product_row(product)

    assert isinstance(row, dict)
    assert "id" in row
    