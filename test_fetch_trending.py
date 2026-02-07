#!/usr/bin/env python3
"""
Tests for fetch_trending.py

Tests timezone handling, date key generation, and other core functionality.
"""

import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
import json
import tempfile
import os

# Import functions from fetch_trending.py
import sys
sys.path.insert(0, os.path.dirname(__file__))
from fetch_trending import (
    get_date_key,
    convert_twitter_url,
    load_history,
    save_history,
    clean_old_history,
    BEIJING_TZ,
)


class TestTimezoneHandling:
    """Test timezone conversion and date key generation."""
    
    def test_get_date_key_with_beijing_time(self):
        """Test that date key uses Beijing timezone correctly."""
        # Simulate UTC 22:00 on Feb 6, 2026 (Beijing 06:00 on Feb 7)
        utc_time = datetime(2026, 2, 6, 22, 0, 0, tzinfo=timezone.utc)
        beijing_time = utc_time.astimezone(BEIJING_TZ)
        
        result = get_date_key(beijing_time)
        
        # Should show Feb 7 (Beijing date), not Feb 6 (UTC date)
        assert result == "2026-02-07", f"Expected 2026-02-07, got {result}"
    
    def test_get_date_key_year_transition(self):
        """Test date key generation across year boundary."""
        # Simulate UTC 22:00 on Dec 31, 2025 (Beijing 06:00 on Jan 1, 2026)
        utc_time = datetime(2025, 12, 31, 22, 0, 0, tzinfo=timezone.utc)
        beijing_time = utc_time.astimezone(BEIJING_TZ)
        
        result = get_date_key(beijing_time)
        
        # Should show Jan 1, 2026 (Beijing date), not Dec 31, 2025 (UTC date)
        assert result == "2026-01-01", f"Expected 2026-01-01, got {result}"
    
    def test_get_date_key_month_transition(self):
        """Test date key generation across month boundary."""
        # Simulate UTC 22:00 on Feb 28, 2026 (Beijing 06:00 on Mar 1)
        utc_time = datetime(2026, 2, 28, 22, 0, 0, tzinfo=timezone.utc)
        beijing_time = utc_time.astimezone(BEIJING_TZ)
        
        result = get_date_key(beijing_time)
        
        # Should show Mar 1 (Beijing date), not Feb 28 (UTC date)
        assert result == "2026-03-01", f"Expected 2026-03-01, got {result}"
    
    def test_get_date_key_same_day(self):
        """Test date key when UTC and Beijing time are same day."""
        # Simulate UTC 15:00 on Feb 6 (Beijing 23:00 on Feb 6)
        utc_time = datetime(2026, 2, 6, 15, 0, 0, tzinfo=timezone.utc)
        beijing_time = utc_time.astimezone(BEIJING_TZ)
        
        result = get_date_key(beijing_time)
        
        # Should show Feb 6 (same day in both timezones)
        assert result == "2026-02-06", f"Expected 2026-02-06, got {result}"
    
    def test_get_date_key_default_uses_beijing_time(self):
        """Test that get_date_key() without arguments uses Beijing timezone."""
        result = get_date_key()
        
        # Should return a valid date string in YYYY-MM-DD format
        assert len(result) == 10
        assert result[4] == '-' and result[7] == '-'
        
        # Verify it matches Beijing time, not UTC
        beijing_now = datetime.now(BEIJING_TZ)
        expected = beijing_now.strftime('%Y-%m-%d')
        assert result == expected


class TestTwitterURLConversion:
    """Test Twitter URL conversion functionality."""
    
    def test_convert_twitter_search_url(self):
        """Test conversion of twitter://search/ URLs."""
        url = "twitter://search/?query=%23Python"
        headline = "Python Trending"
        
        result = convert_twitter_url(url, headline)
        
        assert result.startswith("https://x.com/search?q=")
        assert "%23Python" in result
    
    def test_convert_twitter_trending_url_with_headline(self):
        """Test conversion of twitter://trending/ URLs with headline."""
        url = "twitter://trending/12345"
        headline = "Breaking News"
        
        result = convert_twitter_url(url, headline)
        
        assert result.startswith("https://x.com/search?q=")
        assert "Breaking" in result or "Breaking%20News" in result
        assert "src=trend_click" in result
    
    def test_convert_twitter_trending_url_without_headline(self):
        """Test conversion of twitter://trending/ URLs without headline."""
        url = "twitter://trending/12345"
        headline = ""
        
        result = convert_twitter_url(url, headline)
        
        # Should fallback to explore page
        assert result == "https://x.com/explore"
    
    def test_convert_event_summary_with_headline(self):
        """Test conversion of event summary IDs with headline."""
        url = "eventsummary-12345"
        headline = "Major Event"
        
        result = convert_twitter_url(url, headline)
        
        assert result.startswith("https://x.com/search?q=")
        assert "src=trend_click" in result
    
    def test_convert_event_summary_without_headline(self):
        """Test conversion of event summary IDs without headline."""
        url = "eventsummary-12345"
        headline = ""
        
        result = convert_twitter_url(url, headline)
        
        # Should fallback to explore page
        assert result == "https://x.com/explore"
    
    def test_convert_https_url_unchanged(self):
        """Test that https:// URLs are returned unchanged."""
        url = "https://x.com/explore"
        headline = "Test"
        
        result = convert_twitter_url(url, headline)
        
        assert result == url


class TestHistoryManagement:
    """Test history loading, saving, and cleaning functionality."""
    
    def test_load_history_nonexistent_file(self):
        """Test loading history when file doesn't exist."""
        # Temporarily change to a temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = load_history()
                assert result == {}
            finally:
                os.chdir(old_cwd)
    
    def test_save_and_load_history(self):
        """Test saving and loading history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Create test history
                test_history = {
                    "2026-02-06": {
                        "timestamp": "2026-02-06T22:00:00+00:00",
                        "count": 20,
                        "html": "<h2>Test</h2>"
                    }
                }
                
                # Save history
                save_history(test_history)
                
                # Load it back
                loaded = load_history()
                
                assert loaded == test_history
                assert "2026-02-06" in loaded
                assert loaded["2026-02-06"]["count"] == 20
            finally:
                os.chdir(old_cwd)
    
    def test_clean_old_history(self):
        """Test cleaning old history items."""
        # Create test history with old and recent items
        test_history = {
            "2026-01-01": {
                "timestamp": "2026-01-01T00:00:00+00:00",
                "count": 10,
                "html": "<h2>Old</h2>"
            },
            "2026-02-05": {
                "timestamp": "2026-02-05T00:00:00+00:00",
                "count": 15,
                "html": "<h2>Recent</h2>"
            },
            "2026-02-06": {
                "timestamp": "2026-02-06T00:00:00+00:00",
                "count": 20,
                "html": "<h2>Very Recent</h2>"
            }
        }
        
        # Clean items older than Feb 5
        cutoff_date = datetime(2026, 2, 5, 0, 0, 0, tzinfo=timezone.utc)
        result = clean_old_history(test_history, cutoff_date)
        
        # Should only keep items from Feb 5 onwards
        assert "2026-01-01" not in result
        assert "2026-02-05" in result
        assert "2026-02-06" in result
        assert len(result) == 2


class TestDateKeyFormat:
    """Test date key format consistency."""
    
    def test_date_key_format(self):
        """Test that date keys follow YYYY-MM-DD format."""
        test_time = datetime(2026, 2, 6, 12, 0, 0, tzinfo=BEIJING_TZ)
        result = get_date_key(test_time)
        
        # Check format
        assert len(result) == 10
        assert result[4] == '-'
        assert result[7] == '-'
        
        # Check each component
        year, month, day = result.split('-')
        assert len(year) == 4
        assert len(month) == 2
        assert len(day) == 2
        assert year == "2026"
        assert month == "02"
        assert day == "06"


if __name__ == "__main__":
    # Allow running tests directly with python test_fetch_trending.py
    pytest.main([__file__, "-v"])
