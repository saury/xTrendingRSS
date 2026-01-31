#!/usr/bin/env python3
"""
Fetch X (Twitter) trending topics and generate RSS feed.
Uses the bird CLI to fetch trending data.
Generates one daily digest article containing all trending topics.
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
HISTORY_DAYS = 7  # Keep daily digests for 7 days


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
        Dictionary mapping dates to digest data
    """
    history_path = Path(HISTORY_FILE)
    if not history_path.exists():
        return {}
    
    try:
        with open(history_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
            print(f"✓ Loaded history with {len(history)} daily digests")
            return history
    except json.JSONDecodeError:
        print("Warning: Could not parse history file, starting fresh", file=sys.stderr)
        return {}


def save_history(history: dict):
    """
    Save trending history to JSON file.
    
    Args:
        history: Dictionary mapping dates to digest data
    """
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved history with {len(history)} daily digests")


def clean_old_history(history: dict, cutoff_date: datetime) -> dict:
    """
    Remove history items older than the cutoff date.
    
    Args:
        history: Dictionary mapping dates to digest data
        cutoff_date: Remove items older than this date
        
    Returns:
        Cleaned history dictionary
    """
    cleaned = {}
    removed_count = 0
    
    for date_key, digest_data in history.items():
        digest_date = datetime.fromisoformat(digest_data['timestamp'])
        if digest_date >= cutoff_date:
            cleaned[date_key] = digest_data
        else:
            removed_count += 1
    
    if removed_count > 0:
        print(f"✓ Removed {removed_count} old daily digests from history")
    
    return cleaned


def get_date_key(dt: datetime = None) -> str:
    """
    Get date key in YYYY-MM-DD format.
    
    Args:
        dt: Datetime object (default: now in UTC)
        
    Returns:
        Date string in YYYY-MM-DD format
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.strftime('%Y-%m-%d')


def convert_twitter_url(url: str, headline: str = '') -> str:
    """
    Convert twitter:// protocol URLs to https://x.com URLs.
    
    Args:
        url: Original URL from bird CLI (may be twitter:// protocol)
        headline: Topic headline (used as fallback for search)
        
    Returns:
        Valid https://x.com URL
    """
    import urllib.parse
    
    if url.startswith('twitter://search/'):
        # Convert twitter://search/?query=... to https://x.com/search?q=...
        query = url.replace('twitter://search/?query=', '')
        return f'https://x.com/search?q={query}'
    elif url.startswith('twitter://trending/'):
        # twitter://trending/{id} is not a public URL format
        # Use headline to create a search query instead
        if headline:
            query = urllib.parse.quote(headline)
            return f'https://x.com/search?q={query}&src=trend_click'
        # Fallback to explore page
        return 'https://x.com/explore'
    elif url.startswith('eventsummary-'):
        # Event summary IDs also need to use headline as search
        if headline:
            query = urllib.parse.quote(headline)
            return f'https://x.com/search?q={query}&src=trend_click'
        return 'https://x.com/explore'
    
    # Return URL as-is if it's already a valid https:// URL
    return url


def create_digest_html(trending_data: list, date_str: str) -> str:
    """
    Create HTML content for daily trending digest.
    
    Args:
        trending_data: List of trending topic dictionaries
        date_str: Date string for the digest
        
    Returns:
        HTML string
    """
    html_parts = []
    
    # Header
    html_parts.append(f'<h2>📊 X Trending Topics - {date_str}</h2>')
    html_parts.append(f'<p><strong>Total trending topics:</strong> {len(trending_data)}</p>')
    html_parts.append('<hr/>')
    
    # Group by category
    categories = {}
    for item in trending_data:
        category = item.get('category', 'Other')
        if category not in categories:
            categories[category] = []
        categories[category].append(item)
    
    # Render each category
    for category, items in sorted(categories.items()):
        html_parts.append(f'<h3>📂 {category}</h3>')
        html_parts.append('<ol>')
        
        for item in items:
            headline = item.get('headline', 'Trending Topic')
            raw_url = item.get('url', item.get('id', 'https://x.com/explore'))
            url = convert_twitter_url(raw_url, headline)
            description = item.get('description', '')
            post_count = item.get('postCount', 0)
            time_ago = item.get('timeAgo', '')
            
            html_parts.append('<li>')
            html_parts.append(f'<strong><a href="{url}" target="_blank">{headline}</a></strong>')
            
            if description:
                html_parts.append(f'<br/><em>{description}</em>')
            
            metadata = []
            if post_count:
                metadata.append(f'{post_count:,} posts')
            if time_ago:
                metadata.append(f'Updated: {time_ago}')
            
            if metadata:
                html_parts.append(f'<br/><small>{" • ".join(metadata)}</small>')
            
            html_parts.append('</li>')
        
        html_parts.append('</ol>')
    
    # Footer
    html_parts.append('<hr/>')
    html_parts.append(f'<p><small>Generated at {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}</small></p>')
    
    return '\n'.join(html_parts)


def create_rss_feed(history: dict, output_path: str = 'trending.xml', feed_url: str = None):
    """
    Generate RSS feed from daily digest history.
    
    Args:
        history: Dictionary mapping dates to digest data
        output_path: Output file path for RSS XML
        feed_url: Self-referencing URL for the RSS feed
    """
    fg = FeedGenerator()
    fg.id('https://github.com/YOUR_USERNAME/xTrendingRSS')
    fg.title('X (Twitter) Daily Trending Digest')
    fg.author({'name': 'X Trending RSS Bot', 'email': 'bot@example.com'})
    
    # Add self-referencing link first
    if feed_url:
        fg.link(href=feed_url, rel='self')
    
    # Main channel link (must be last for feedgen)
    fg.link(href='https://x.com/explore', rel='alternate')
    
    fg.logo('https://abs.twimg.com/icons/apple-touch-icon-192x192.png')
    fg.subtitle('Daily digest of trending topics from X (Twitter)')
    fg.language('en')
    
    # Update timestamp
    update_time = datetime.now(timezone.utc)
    fg.updated(update_time)
    
    # Sort history by date (newest first)
    sorted_history = sorted(
        history.items(),
        key=lambda x: x[1]['timestamp'],
        reverse=True
    )
    
    # Add each daily digest as a feed entry
    for date_key, digest_data in sorted_history:
        fe = fg.add_entry()
        
        # Unique identifier for this day's digest
        fe.id(f"x-trending-digest-{date_key}")
        
        # Title with date
        fe.title(f"X Trending Topics - {date_key}")
        
        # HTML content - use CDATA to prevent escaping issues in RSS readers
        html_content = digest_data['html']
        fe.content(html_content, type='CDATA')
        fe.description(f"Daily digest of {digest_data['count']} trending topics from X (Twitter)")
        
        # Link to X explore page
        fe.link(href='https://x.com/explore')
        
        # Use the digest timestamp
        digest_time = datetime.fromisoformat(digest_data['timestamp'])
        fe.published(digest_time)
        fe.updated(digest_time)
        
        # Add category
        fe.category(term='Daily Digest')
    
    # Generate RSS 2.0 feed
    rss_str = fg.rss_str(pretty=True)
    
    # Write to file
    output_file = Path(output_path)
    output_file.write_bytes(rss_str)
    
    print(f"✓ RSS feed generated: {output_path}")
    print(f"✓ Feed contains {len(history)} daily digests")


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
    print("X Trending RSS Generator (Daily Digest)")
    print("=" * 60)
    
    # Load existing history
    history = load_history()
    
    # Clean old history items
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=HISTORY_DAYS)
    history = clean_old_history(history, cutoff_date)
    
    # Fetch trending data
    trending_data = get_trending_data(auth_token, ct0, trending_count)
    
    if not trending_data:
        print("No trending data to process. Exiting.")
        sys.exit(0)
    
    # Get today's date key
    today_key = get_date_key()
    current_time = datetime.now(timezone.utc)
    
    # Check if we already have today's digest
    if today_key in history:
        print(f"⚠️  Daily digest for {today_key} already exists")
        print(f"   Updating with latest data...")
    
    # Create HTML digest
    html_content = create_digest_html(trending_data, today_key)
    
    # Store in history
    history[today_key] = {
        'timestamp': current_time.isoformat(),
        'count': len(trending_data),
        'html': html_content
    }
    
    print(f"✓ Created daily digest for {today_key} with {len(trending_data)} topics")
    
    # Save updated history
    save_history(history)
    
    # Generate RSS feed
    feed_url = os.getenv('FEED_URL', 'https://raw.githubusercontent.com/YOUR_USERNAME/xTrendingRSS/main/trending.xml')
    create_rss_feed(history, output_file, feed_url)
    
    print("=" * 60)
    print(f"✓ Done! (1 digest, {len(history)} total in feed)")
    print("=" * 60)


if __name__ == '__main__':
    main()
