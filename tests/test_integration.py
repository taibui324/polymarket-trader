"""Integration tests."""

import pytest
from unittest.mock import MagicMock, patch
from src.workers.data_fetcher import DataFetcher
from src.workers.scanner import Scanner


class TestDataFetcher:
    """Test data fetcher worker."""

    @patch('src.workers.data_fetcher.get_polymarket_api')
    @patch('src.workers.data_fetcher.get_supabase_client')
    def test_fetch_and_store_markets(self, mock_supabase, mock_api):
        """Test fetching and storing markets."""
        # Mock API response
        mock_api_instance = MagicMock()
        mock_api_instance.get_markets.return_value = [
            {"conditionId": "test-1", "question": "Test?", "yesPrice": "0.6", "noPrice": "0.4"}
        ]
        mock_api.return_value = mock_api_instance

        # Mock Supabase
        mock_supabase_instance = MagicMock()
        mock_supabase_instance.fetch_markets.return_value = []
        mock_supabase.return_value = mock_supabase_instance

        fetcher = DataFetcher()
        result = fetcher.fetch_and_store_markets()

        assert result == 1


class TestScanner:
    """Test scanner worker."""

    @patch('src.workers.scanner.get_supabase_client')
    def test_scan_all_markets_no_markets(self, mock_supabase):
        """Test scanning with no markets."""
        mock_supabase_instance = MagicMock()
        mock_supabase_instance.fetch_markets.return_value = []
        mock_supabase.return_value = mock_supabase_instance

        scanner = Scanner()
        result = scanner.scan_all_markets()

        assert result == 0
