#!/usr/bin/env python3
"""
Fetch X (Twitter) trending topics and generate RSS feed.
Uses the bird CLI to fetch trending data.
Generates one daily digest article containing all trending topics.
AI-enhanced with ZhipuAI GLM-4-Flash model to generate Chinese summaries.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv
from feedgen.feed import FeedGenerator

try:
    from zhipuai import ZhipuAI
    ZHIPUAI_AVAILABLE = True
except ImportError:
    ZHIPUAI_AVAILABLE = False
    print("Warning: zhipuai not installed. AI enhancement will be disabled.", file=sys.stderr)
    print("Install with: pip install zhipuai", file=sys.stderr)


HISTORY_FILE = 'trending_history.json'
HISTORY_DAYS = 7  # Keep daily digests for 7 days
TIMEZONE_OFFSET = 8  # Beijing time (UTC+8)


def enhance_with_ai(topic: dict) -> str:
    """
    Use ZhipuAI GLM-4-Flash model to generate Chinese summary.
    
    Args:
        topic: Trending topic dictionary with headline, category, description, etc.
        
    Returns:
        Chinese summary string (fallback to empty string on error)
    """
    if not ZHIPUAI_AVAILABLE:
        return ''
    
    api_key = os.getenv('ZHIPUAI_API_KEY', 'free-api-key-for-demo')
    
    headline = topic.get('headline', '')
    category = topic.get('category', '')
    description = topic.get('description', '')
    post_count = topic.get('postCount', 0)
    
    # Build context
    context_parts = [f"话题: {headline}"]
    if category:
        context_parts.append(f"分类: {category}")
    if description:
        context_parts.append(f"描述: {description}")
    if post_count:
        context_parts.append(f"讨论量: {post_count:,}")
    
    context = "\n".join(context_parts)
    
    # Create prompt
    prompt = f"""请为以下 X (Twitter) 热门话题生成一段简短的中文描述（40-60字），突出主要亮点和潜在影响。

{context}

要求：直接输出中文描述，不要其他说明。"""
    
    try:
        client = ZhipuAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "user", "content": prompt}
            ],
            timeout=15
        )
        
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content.strip()
            # Clean up and limit length
            if len(content) > 100:
                content = content[:97] + '...'
            return content
        
        return ''
        
    except Exception as e:
        print(f"  ⚠️  AI错误 ({headline[:20]}...): {str(e)[:60]}", file=sys.stderr)
        return ''


def get_trending_data(auth_token: str, ct0: str, count: int = 20, enable_ai: bool = True) -> list:
    """
    Fetch trending topics using bird CLI and enhance with AI summaries.
    
    Args:
        auth_token: Twitter auth_token cookie
        ct0: Twitter ct0 cookie
        count: Number of trending items to fetch
        enable_ai: Whether to enhance topics with AI-generated Chinese summaries
        
    Returns:
        List of trending topic dictionaries (with 'ai_summary_zh' field if AI enabled)
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
        
        # Enhance with AI summaries if enabled
        if enable_ai and ZHIPUAI_AVAILABLE:
            print("🤖 Generating AI summaries with ZhipuAI GLM-4 model...")
            for i, topic in enumerate(trending_data, 1):
                print(f"  [{i}/{len(trending_data)}] Processing: {topic.get('headline', 'N/A')[:40]}...")
                summary = enhance_with_ai(topic)
                topic['ai_summary_zh'] = summary
                if summary:
                    print(f"      ✓ {summary[:60]}...")
        elif enable_ai and not ZHIPUAI_AVAILABLE:
            print("⚠️  AI enhancement skipped (zhipuai not installed)", file=sys.stderr)
        
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
    Get date key in YYYY-MM-DD format using Beijing time (UTC+8).
    
    Args:
        dt: Datetime object (default: now in UTC+8)
        
    Returns:
        Date string in YYYY-MM-DD format
    """
    if dt is None:
        # Get current time in Beijing timezone (UTC+8)
        dt = datetime.now(timezone.utc) + timedelta(hours=TIMEZONE_OFFSET)
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
    Create HTML content for daily trending digest with AI-generated summaries.
    
    Args:
        trending_data: List of trending topic dictionaries (may include 'ai_summary_zh')
        date_str: Date string for the digest
        
    Returns:
        HTML string
    """
    html_parts = []
    
    # Header
    html_parts.append(f'<h2>📊 X Trending Topics - {date_str}</h2>')
    html_parts.append(f'<p><strong>Total trending topics:</strong> {len(trending_data)}</p>')
    
    # Check if AI summaries are available
    has_ai_summaries = any(item.get('ai_summary_zh') for item in trending_data)
    if has_ai_summaries:
        html_parts.append('<p><em>🤖 AI-enhanced with Chinese summaries powered by ZhipuAI GLM-4</em></p>')
    
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
            ai_summary = item.get('ai_summary_zh', '')
            post_count = item.get('postCount', 0)
            time_ago = item.get('timeAgo', '')
            
            html_parts.append('<li>')
            html_parts.append(f'<strong><a href="{url}" target="_blank">{headline}</a></strong>')
            
            # Add AI-generated Chinese summary first (highlighted)
            if ai_summary:
                html_parts.append(f'<br/><div style="background:#f0f8ff;padding:8px;margin:4px 0;border-left:3px solid #4a90e2;"><strong>🤖 AI 摘要：</strong>{ai_summary}</div>')
            
            # Original description (if available)
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
    beijing_time = datetime.now(timezone.utc) + timedelta(hours=TIMEZONE_OFFSET)
    html_parts.append(f'<p><small>Generated at {beijing_time.strftime("%Y-%m-%d %H:%M")} Beijing Time (UTC+8)</small></p>')
    if has_ai_summaries:
        html_parts.append('<p><small>AI summaries generated using ZhipuAI GLM-4-Flash model</small></p>')
    
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
