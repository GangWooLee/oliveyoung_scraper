# Creait - Instagram Product Trust Analysis System

AI-powered system to analyze Instagram advertising product credibility based on actual user reviews.

## Phase 1: Product Information Scraping and DB Storage (Complete)

Automatically extracts product information and reviews from product page URLs using AI Agent and stores them in database.

### Key Features

- AI Agent (GPT-4) based intelligent web scraping
- Dynamic page handling with Playwright
- Automatic extraction of product info (name, price, rating, description, reviews)
- SQLite database auto-save
- Auto-retry and error handling
- Structured logging system

## Installation and Usage

### 1. Environment Setup

```bash
# Python 3.13+ required
python --version

# Install uv package manager (recommended)
pip install uv

# Install dependencies
uv sync

# Install Playwright browsers
uv run playwright install chromium
```

### 2. Environment Variables

```bash
# Create .env file
cp .env.example .env

# Edit .env and add OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Run

```bash
# Run main program
uv run python main.py

# or
python main.py
```

### 4. Usage

```
Enter product page URL: https://example.com/product/123
```

Program will automatically:
1. Analyze page
2. Extract product info
3. Collect reviews (minimum 10+)
4. Save to database

## Project Structure

```
creait/
├── src/
│   ├── agent/              # AI Agent module
│   │   ├── scraper_agent.py   # Main Agent logic
│   │   ├── tools.py           # Agent tools
│   │   └── prompts.py         # Prompt templates
│   ├── browser/            # Browser automation
│   │   └── playwright_manager.py
│   ├── models/             # Data models
│   │   ├── product.py         # Pydantic models
│   │   └── database.py        # SQLAlchemy ORM
│   ├── database/           # DB management
│   │   ├── connection.py      # Connection manager
│   │   └── repository.py      # CRUD operations
│   └── utils/              # Utilities
│       └── config.py          # Config management
├── tests/                  # Tests
│   └── test_phase1.py
├── main.py                 # Main entry point
├── pyproject.toml          # Dependencies
├── .env.example            # Environment template
└── README.md
```

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test
uv run pytest tests/test_phase1.py -v

# With async tests
uv run pytest tests/ -v --asyncio-mode=auto
```

## Database Schema

### products table
- id, url, title, price, currency
- overall_rating, rating_count
- description, specifications (JSON), images (JSON)
- product_id, scraped_at, created_at, updated_at

### reviews table
- id, product_id (FK)
- author, rating, review_date
- content, verified_purchase, helpful_count
- created_at

## Tech Stack

- **AI/LLM**: OpenAI GPT-4, LangChain
- **Web Scraping**: Playwright, BeautifulSoup4
- **Database**: SQLAlchemy, SQLite (dev), PostgreSQL (production)
- **Data Validation**: Pydantic
- **Logging**: Loguru
- **Retry**: Tenacity
- **Package Manager**: uv

## Configuration

Settings in `.env` file:

```bash
# AI model
OPENAI_MODEL=gpt-4-turbo-preview

# Browser
HEADLESS=true              # false to show browser UI
BROWSER_TIMEOUT=30000      # timeout (milliseconds)

# Retry
MAX_RETRIES=3              # max retry attempts
RETRY_DELAY=2              # retry delay (seconds)

# Logging
LOG_LEVEL=INFO             # DEBUG, INFO, WARNING, ERROR
LOG_FILE=creait.log
```

## Troubleshooting

### Playwright browser installation error
```bash
uv run playwright install --with-deps chromium
```

### OpenAI API error
- Check if valid API key is set in `.env`
- Verify API key permissions and credits

### Database error
```bash
# Delete and recreate database
rm creait.db
python main.py
```

## Next Phases (Planned)

- [ ] Phase 2: Data preprocessing and cleaning
- [ ] Phase 3: AI analysis engine (trust score calculation)
- [ ] Phase 4: Report generation and visualization

## License

MIT License

## Contributing

Issues and PRs are welcome!