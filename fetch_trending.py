#!/usr/bin/env python3
"""
Fetch X (Twitter) trending topics and generate RSS feed.
Uses the bird CLI to fetch trending data.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from feedgen.feed import FeedGenerator


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
    # Run bird news command with authentication
    cmd = [
        'npx', '@steipete/bird', 'news',
        '--ai-only',  # Filter to only AI-curated news
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


def create_rss_feed(trending_data: list, output_path: str = 'trending.xml'):
    """
    Generate RSS feed from trending topics.
    
    Args:
        trending_data: List of trending topic dictionaries
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
    
    # Add trending topics as feed entries
    for item in trending_data:
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
            description_parts.append(f"Category: {item['category']}")
        
        if item.get('description'):
            description_parts.append(item['description'])
        
        if item.get('postCount'):
            description_parts.append(f"{item['postCount']:,} posts")
        
        if item.get('timeAgo'):
            description_parts.append(f"Updated: {item['timeAgo']}")
        
        description = '<br/>'.join(description_parts) if description_parts else headline
        fe.description(description)
        
        # Link to the trend URL if available, otherwise to explore
        url = item.get('url', 'https://x.com/explore')
        fe.link(href=url)
        
        # Use current time as published date
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
    print("X Trending RSS Generator")
    print("=" * 60)
    
    # Fetch trending data
    trending_data = get_trending_data(auth_token, ct0, trending_count)
    
    if not trending_data:
        print("No trending data to process. Exiting.")
        sys.exit(0)
    
    # Generate RSS feed
    create_rss_feed(trending_data, output_file)
    
    print("=" * 60)
    print("✓ Done!")
    print("=" * 60)


if __name__ == '__main__':
    main()
