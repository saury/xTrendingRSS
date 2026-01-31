# Agent Guidelines for xTrendingRSS

## Project Overview

**xTrendingRSS** is a Python 3.9+ application that generates daily RSS feeds from X (Twitter) trending topics using the `bird` CLI tool. It creates **one daily digest article** containing all trending topics, organized by category.

**Tech Stack:**
- Python 3.9+ (main application)
- Node.js 22+ (required for `bird` CLI)
- `feedgen` for RSS 2.0 generation
- `bird` CLI for X (Twitter) GraphQL data fetching
- GitHub Actions for daily automation

---

## Build, Run & Test Commands

### Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (bird CLI)
npm install
```

### Run Locally
```bash
# Prerequisites: Set up .env file with credentials
cp .env.example .env
# Edit .env and fill in TWITTER_AUTH_TOKEN and TWITTER_CT0

# Execute main script
python3 fetch_trending.py

# Alternative: Make executable and run
chmod +x fetch_trending.py
./fetch_trending.py
```

### GitHub Actions
```bash
# Trigger manual workflow run
gh workflow run update-rss.yml

# View workflow logs
gh run list --workflow=update-rss.yml
gh run view <run-id> --log
```

### Testing & Validation
```bash
# Validate RSS output (XML well-formedness)
xmllint --noout trending.xml

# Check Python syntax without execution
python3 -m py_compile fetch_trending.py

# Test bird CLI connectivity (requires credentials in .env)
source .env
npx @steipete/bird news -n 5 --json \
  --auth-token "$TWITTER_AUTH_TOKEN" \
  --ct0 "$TWITTER_CT0"

# Validate history JSON
python3 -c "import json; json.load(open('trending_history.json'))"
```

---

## Code Style & Conventions

### Python Style

**General Principles:**
- Follow **PEP 8** conventions
- Use **type hints** for function signatures (Python 3.9+ syntax)
- Prefer **descriptive variable names** over abbreviations
- Keep functions **single-purpose** and well-documented

**Imports:**
```python
# Standard library imports first (alphabetically)
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Third-party imports second (alphabetically)
from dotenv import load_dotenv
from feedgen.feed import FeedGenerator
```

**Type Annotations:**
```python
# Always use type hints for function parameters and return values
def get_trending_data(auth_token: str, ct0: str, count: int = 20) -> list:
    """Docstring describes the function."""
    pass

def load_history() -> dict:
    """Return type always specified."""
    pass
```

**Docstrings:**
```python
def function_name(param1: str, param2: int = 10) -> dict:
    """
    Brief one-line description.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: 10)
        
    Returns:
        Description of return value
    """
```

**Error Handling:**
```python
# Specific exception types, never bare except
try:
    result = subprocess.run(cmd, check=True)
except subprocess.CalledProcessError as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"Error parsing JSON: {e}", file=sys.stderr)
    sys.exit(1)

# Use sys.stderr for error messages
print("Error message", file=sys.stderr)
```

**File I/O:**
```python
# Use pathlib.Path for file operations
from pathlib import Path

history_path = Path(HISTORY_FILE)
if not history_path.exists():
    return {}

# Always specify encoding for text files
with open(history_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Use json.dump with consistent formatting
json.dump(history, f, indent=2, ensure_ascii=False)
```

**Constants:**
```python
# Module-level constants in UPPER_CASE
HISTORY_FILE = 'trending_history.json'
HISTORY_DAYS = 7
```

**String Formatting:**
```python
# Prefer f-strings for readability
print(f"✓ Fetched {len(trending_data)} trending topics")
html_parts.append(f'<h2>📊 X Trending Topics - {date_str}</h2>')

# Use format for complex formatting
"{:,}".format(post_count)  # Thousand separators
```

---

## Project-Specific Patterns

### Date Handling
```python
# Always use UTC timezone
from datetime import datetime, timezone, timedelta

current_time = datetime.now(timezone.utc)
date_key = current_time.strftime('%Y-%m-%d')

# ISO format for timestamps
timestamp = current_time.isoformat()
parsed = datetime.fromisoformat(timestamp)
```

### Environment Variables
```python
# Load from .env file at script start
from dotenv import load_dotenv
load_dotenv()

# Get with fallback defaults
trending_count = int(os.getenv('TRENDING_COUNT', '20'))
output_file = os.getenv('OUTPUT_FILE', 'trending.xml')

# Required variables should fail fast
auth_token = os.getenv('TWITTER_AUTH_TOKEN')
if not auth_token:
    print("Error: Missing TWITTER_AUTH_TOKEN", file=sys.stderr)
    sys.exit(1)
```

### subprocess Usage
```python
# Use list format for commands (safer than shell=True)
cmd = [
    'npx', '@steipete/bird', 'news',
    '-n', str(count),
    '--json',
    '--auth-token', auth_token,
    '--ct0', ct0
]

# Always capture output for parsing
result = subprocess.run(
    cmd,
    capture_output=True,
    text=True,
    check=True  # Raises CalledProcessError on non-zero exit
)
```

### Data Structure Patterns
```python
# History structure (trending_history.json)
{
    "YYYY-MM-DD": {
        "timestamp": "ISO 8601 string",
        "count": 20,
        "html": "full HTML digest content"
    }
}

# Trending topic structure (from bird CLI)
{
    "headline": "Topic title",
    "url": "twitter://... or https://...",
    "category": "Politics · Trending",
    "description": "Optional description",
    "postCount": 12345,
    "timeAgo": "2 days ago"
}
```

---

## Important Constraints

### Security
- **NEVER commit credentials** - `.env` is gitignored
- Use **GitHub Secrets** for Actions (`TWITTER_AUTH_TOKEN`, `TWITTER_CT0`)
- Sanitize credentials in logs: `print(f"Executing: {' '.join(cmd[:6])}... [auth hidden]")`

### RSS Feed Requirements
- Use **feedgen** library for RSS 2.0 generation
- Content must use `type='CDATA'` to prevent escaping issues
- Unique GUIDs: `x-trending-digest-YYYY-MM-DD`
- Keep **7 days** of history (configurable via `HISTORY_DAYS`)

### bird CLI Compatibility
- Requires **Node.js 22+** (bird 0.8.0+ requirement)
- Always use `--json` flag for structured output
- Convert `twitter://` URLs to `https://x.com` for web compatibility

### Data Integrity
- **One digest per day** - update if already exists
- Clean old history items beyond `HISTORY_DAYS`
- Validate JSON before writing to files
- Use UTF-8 encoding for all text files

---

## File Structure

```
xTrendingRSS/
├── fetch_trending.py        # Main script (executable)
├── requirements.txt         # Python dependencies
├── package.json            # Node.js dependencies (bird CLI)
├── .env.example            # Environment template
├── .env                    # Local credentials (gitignored)
├── .github/workflows/
│   └── update-rss.yml      # GitHub Actions workflow
├── trending.xml            # Generated RSS feed
├── trending_history.json   # 7-day digest history
└── AGENTS.md              # This file
```

---

## Common Tasks

### Adding a New Feature
1. Check if it requires new dependencies (`requirements.txt` or `package.json`)
2. Add type hints to all new functions
3. Follow existing patterns for error handling and logging
4. Update `.env.example` if new environment variables are needed
5. Test locally before committing

### Modifying RSS Output
- Edit `create_digest_html()` for HTML structure changes
- Edit `create_rss_feed()` for feed metadata changes
- Validate with `xmllint` after changes
- Test in RSS reader (Reeder, NetNewsWire, Feedly)

### Debugging
```bash
# Check bird CLI output directly
npx @steipete/bird news -n 5 --json \
  --auth-token "$TWITTER_AUTH_TOKEN" \
  --ct0 "$TWITTER_CT0"

# Validate JSON files
python3 -c "import json; print(json.load(open('trending_history.json')))"

# Check GitHub Actions logs
gh run view --log
```

### Updating Dependencies
```bash
# Python dependencies
pip install --upgrade feedgen python-dotenv
pip freeze > requirements.txt

# Node.js dependencies (bird CLI)
npm update @steipete/bird
```

---

## Troubleshooting

**"bird CLI not found"**
- Run `npm install` to install bird CLI locally
- Ensure Node.js 22+ is installed

**"Missing required environment variables"**
- Copy `.env.example` to `.env`
- Add valid `TWITTER_AUTH_TOKEN` and `TWITTER_CT0` from browser cookies

**"Cookies expired"**
- X (Twitter) cookies expire periodically
- Re-extract from browser and update `.env` or GitHub Secrets

**RSS validation errors**
- Run `xmllint --noout trending.xml`
- Check for unescaped HTML in digest content
- Ensure all URLs are properly formatted
