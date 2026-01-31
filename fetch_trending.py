#!/usr/bin/env python3
"""
Fetch X (Twitter) trending topics and generate RSS feed.
Uses the bird CLI to fetch trending data.
Maintains history to avoid duplicate entries in RSS readers.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
from feedgen.feed import FeedGenerator


HISTORY_FILE = 'trending_history.json'
HISTORY_DAYS = 3  # Keep trending items for 3 days


def get_trending_data(auth_token: str, ct0: str, count: int = 20) -> list:
    """
    Fetch trending topics using bird CLI.
    
    Args:
        auth_token: Twitter auth_token cookie
        ct0: Twitter ct0 cookie
        count: Number of trending items to fetch
        
    Returns:
        List of trending topic dictionaries
    """
    # Run bird news command with authentication (removed --ai-only to get more results)
    cmd = [
        'npx', '@steipete/bird', 'news',
        '-n', str(count),
        '--json',
        '--auth-token', auth_token,
        '--ct0', ct0
    ]
    
    print(f"Executing: {' '.join(cmd[:6])}... [auth hidden]")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse JSON output
        trending_data = json.loads(result.stdout)
        
        if not trending_data:
            print("Warning: No trending data returned", file=sys.stderr)
            return []
        
        print(f"✓ Fetched {len(trending_data)} trending topics")
        return trending_data
        
    except subprocess.CalledProcessError as e:
        print(f"Error running bird CLI: {e}", file=sys.stderr)
        print(f"STDOUT: {e.stdout}", file=sys.stderr)
        print(f"STDERR: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON output: {e}", file=sys.stderr)
        if 'result' in locals():
            print(f"Output was: {result.stdout}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: bird CLI not found. Please run 'npm install' first.", file=sys.stderr)
        sys.exit(1)


def load_history() -> dict:
    """
    Load trending history from JSON file.
    
    Returns:
        Dictionary mapping trending IDs to their first seen timestamp
    """
    history_path = Path(HISTORY_FILE)
    if not history_path.exists():
        return {}
    
    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
            print(f"✓ Loaded history with {len(history)} items")
            return history
    except json.JSONDecodeError:
        print("Warning: Could not parse history file, starting fresh", file=sys.stderr)
        return {}


def save_history(history: dict):
    """
    Save trending history to JSON file.
    
    Args:
        history: Dictionary mapping trending IDs to their first seen timestamp
    """
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved history with {len(history)} items")


def clean_old_history(history: dict, cutoff_date: datetime) -> dict:
    """
    Remove history items older than the cutoff date.
    
    Args:
        history: Dictionary mapping trending IDs to timestamps
        cutoff_date: Remove items older than this date
        
    Returns:
        Cleaned history dictionary
    """
    cleaned = {}
    removed_count = 0
    
    for item_id, timestamp in history.items():
        item_date = datetime.fromisoformat(timestamp)
        if item_date >= cutoff_date:
            cleaned[item_id] = timestamp
        else:
            removed_count += 1
    
    if removed_count > 0:
        print(f"✓ Removed {removed_count} old items from history")
    
    return cleaned


def merge_trending_with_history(new_items: list, history: dict) -> tuple[list, dict, int]:
    """
    Merge new trending items with historical data.
    
    Args:
        new_items: List of newly fetched trending topics
        history: Existing history dictionary
        
    Returns:
        Tuple of (all_items, updated_history, new_count)
    """
    current_time = datetime.now(timezone.utc)
    updated_history = history.copy()
    new_count = 0
    
    # Track which items we've seen in this run
    current_ids = set()
    
    # Process new items
    all_items = []
    for item in new_items:
        item_id = item.get('id', '')
        if not item_id:
            continue
        
        current_ids.add(item_id)
        
        # Check if this is a new trending topic
        if item_id not in history:
            # New item: record first seen time
            updated_history[item_id] = current_time.isoformat()
            item['_first_seen'] = current_time.isoformat()
            new_count += 1
            print(f"  → New: {item.get('headline', 'Unknown')[:60]}")
        else:
            # Existing item: use original timestamp
            item['_first_seen'] = history[item_id]
        
        all_items.append(item)
    
    print(f"✓ Found {new_count} new trending topics")
    
    return all_items, updated_history, new_count


def create_rss_feed(trending_data: list, output_path: str = 'trending.xml'):
    """
    Generate RSS feed from trending topics.
    
    Args:
        trending_data: List of trending topic dictionaries with _first_seen timestamps
        output_path: Output file path for RSS XML
    """
    fg = FeedGenerator()
    fg.id('https://github.com/YOUR_USERNAME/xTrendingRSS')
    fg.title('X (Twitter) Daily Trending Topics')
    fg.author({'name': 'X Trending RSS Bot', 'email': 'bot@example.com'})
    fg.link(href='https://x.com/explore', rel='alternate')
    fg.logo('https://abs.twimg.com/icons/apple-touch-icon-192x192.png')
    fg.subtitle('Daily curated trending topics from X (Twitter)')
    fg.language('en')
    
    # Update timestamp
    update_time = datetime.now(timezone.utc)
    fg.updated(update_time)
    
    # Sort by first seen time (newest first)
    trending_data_sorted = sorted(
        trending_data,
        key=lambda x: x.get('_first_seen', ''),
        reverse=True
    )
    
    # Add trending topics as feed entries
    for item in trending_data_sorted:
        fe = fg.add_entry()
        
        # Use ID as unique identifier
        item_id = item.get('id', '')
        fe.id(f"x-trending-{item_id}")
        
        # Title is the headline
        headline = item.get('headline', 'Trending Topic')
        fe.title(headline)
        
        # Build description from available fields
        description_parts = []
        
        if item.get('category'):
            description_parts.append(f"<strong>Category:</strong> {item['category']}")
        
        if item.get('description'):
            description_parts.append(f"<p>{item['description']}</p>")
        
        if item.get('postCount'):
            description_parts.append(f"<strong>Posts:</strong> {item['postCount']:,}")
        
        if item.get('timeAgo'):
            description_parts.append(f"<strong>Updated:</strong> {item['timeAgo']}")
        
        description = '<br/>'.join(description_parts) if description_parts else headline
        fe.description(description)
        
        # Link to the trend URL if available, otherwise to explore
        url = item.get('url', 'https://x.com/explore')
        fe.link(href=url)
        
        # Use first seen time as published date (key change!)
        first_seen_str = item.get('_first_seen')
        if first_seen_str:
            first_seen = datetime.fromisoformat(first_seen_str)
            fe.published(first_seen)
            fe.updated(update_time)  # Updated time is current run time
        else:
            fe.published(update_time)
            fe.updated(update_time)
        
        # Add category if available
        if item.get('category'):
            fe.category(term=item['category'])
    
    # Generate RSS 2.0 feed
    rss_str = fg.rss_str(pretty=True)
    
    # Write to file
    output_file = Path(output_path)
    output_file.write_bytes(rss_str)
    
    print(f"✓ RSS feed generated: {output_path}")
    print(f"✓ Feed contains {len(trending_data)} items")


def main():
    """Main execution function."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Get credentials from environment
    auth_token = os.getenv('TWITTER_AUTH_TOKEN')
    ct0 = os.getenv('TWITTER_CT0')
    
    if not auth_token or not ct0:
        print("Error: Missing required environment variables", file=sys.stderr)
        print("Please set TWITTER_AUTH_TOKEN and TWITTER_CT0", file=sys.stderr)
        sys.exit(1)
    
    # Get optional configuration
    trending_count = int(os.getenv('TRENDING_COUNT', '20'))
    output_file = os.getenv('OUTPUT_FILE', 'trending.xml')
    
    print("=" * 60)
    print("X Trending RSS Generator (with History Tracking)")
    print("=" * 60)
    
    # Load existing history
    history = load_history()
    
    # Clean old history items
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=HISTORY_DAYS)
    history = clean_old_history(history, cutoff_date)
    
    # Fetch trending data
    new_trending = get_trending_data(auth_token, ct0, trending_count)
    
    if not new_trending:
        print("No trending data to process. Exiting.")
        sys.exit(0)
    
    # Merge with history
    all_trending, updated_history, new_count = merge_trending_with_history(
        new_trending, history
    )
    
    # Save updated history
    save_history(updated_history)
    
    # Generate RSS feed
    create_rss_feed(all_trending, output_file)
    
    print("=" * 60)
    print(f"✓ Done! ({new_count} new, {len(all_trending)} total)")
    print("=" * 60)


if __name__ == '__main__':
    main()
