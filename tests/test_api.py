"""Tests for Polymarket API client."""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch
from src.services.polymarket_api import PolymarketAPI, PolymarketAPIError


class TestPolymarketAPI:
    """Test Polymarket API client."""

    def test_init(self):
        """Test API initialization."""
        with patch('src.services.polymarket_api.get_settings') as mock_settings:
            mock_settings.return_value.polymarket_api_key = ""
            api = PolymarketAPI()
            assert api.BASE_URL == "https://clob.polymarket.com"

    @patch('src.services.polymarket_api.httpx.Client')
    def test_get_markets_success(self, mock_client_class):
        """Test successful market fetch."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": "test-1", "question": "Test?"}]
        mock_response.raise_for_status = MagicMock()

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        with patch('src.services.polymarket_api.get_settings') as mock_settings:
            mock_settings.return_value.polymarket_api_key = ""
            api = PolymarketAPI()
            api._client = mock_client

            markets = api.get_markets()
            assert len(markets) == 1
            assert markets[0]["question"] == "Test?"

    def test_get_price_default(self):
        """Test default price when API fails."""
        with patch('src.services.polymarket_api.get_settings') as mock_settings:
            mock_settings.return_value.polymarket_api_key = ""
            api = PolymarketAPI()

            prices = api.get_price("test-condition")
            assert prices["yes"] == Decimal("0.5")
            assert prices["no"] == Decimal("0.5")
