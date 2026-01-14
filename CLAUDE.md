# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CompraAgil is a Chilean public procurement (licitaciones) intelligence system with:
- **Telegram Bot**: Interactive search, AI analysis, alerts, ML-powered recommendations
- **REST API (FastAPI)**: v3 with 40+ endpoints, Redis cache, rate limiting
- **ML/AI System**: Optimal pricing from 10.6M historical records, RAG search, competition analysis
- **PostgreSQL Database**: Historical procurement data with 17 optimized indexes

## Common Commands

### Running the Application

```bash
# Telegram bot (main entry point)
python src/bot_inteligente_parte1.py

# REST API v3 (recommended)
python api_backend_v3.py
# API docs: http://localhost:8000/api/docs

# Run scraper for new data
python src/scraper.py
```

### Testing

```bash
# Run all tests with pytest
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run only unit tests (fast, no external deps)
pytest -m "not integration"

# Run only integration tests (requires DB/Redis)
pytest -m integration

# Run specific test file
pytest tests/test_config.py -v

# Run tests matching pattern
pytest -k "test_rate_limit" -v

# Legacy test scripts (still work)
python tests/test_ml_system.py
python tests/test_api_v3.py
```

### Database

```bash
# Initialize database tables
python -c "from src.database_extended import iniciar_db_extendida; iniciar_db_extendida()"

# Create optimized indexes
python scripts/create_indexes.py

# Run migrations
python scripts/migrate_subscriptions.py

# Import historical data
python src/importar_historico.py
```

### Docker

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f bot

# Database backup
docker compose exec -T postgres pg_dump -U compra_agil_user compra_agil > backup.sql
```

## Architecture

### Core Components

```
src/
├── bot_inteligente_parte1.py   # Main bot entry, handlers
├── bot_inteligente_parte2.py   # Extended bot handlers
├── bot_ml_commands.py          # ML commands (/precio, /rag, /competencia)
├── database_extended.py        # DB abstraction (PostgreSQL/SQLite auto-detect)
├── ml_precio_optimo.py         # Optimal price recommendation engine
├── rag_historico.py            # Historical RAG search (fuzzy matching)
├── gemini_ai.py                # Google Gemini AI integration
├── redis_cache.py              # Redis caching layer
├── subscriptions.py            # SaaS subscription management
└── api_client.py               # Mercado Publico API client
```

### Data Flow

1. **Scraper** (`scraper.py`) fetches from Mercado Publico API → `licitaciones` table
2. **Historical Import** (`importar_historico.py`) loads monthly ZIP files → `historico_licitaciones` table (10.6M records)
3. **ML System** queries historical data for price analysis and RAG
4. **Bot/API** serves users with AI-enhanced responses via Gemini

### Database Schema

- `licitaciones`: Current tender listings
- `licitaciones_detalle`: Full tender details
- `productos_solicitados`: Requested products per tender
- `historico_licitaciones`: Historical records (10.6M rows) for ML
- `subscriptions`, `usage_tracking`, `payments`: SaaS monetization

### Key Patterns

- **Database**: Auto-detects PostgreSQL vs SQLite via `DATABASE_URL` env var
- **Caching**: Redis optional - graceful fallback if unavailable
- **Migrations**: Idempotent scripts in `scripts/migrate_*.py`, auto-run on deploy
- **API Versioning**: v3 is current (`api_backend_v3.py`)

## Environment Variables

Required in `.env`:
```
TELEGRAM_TOKEN=...
GEMINI_API_KEY=...
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://localhost:6379/0  # optional
```

## CI/CD

GitHub Actions workflow (`.github/workflows/ci-cd.yml`):
- Builds Docker images for bot and scraper
- Deploys to self-hosted runner
- Auto-runs migrations from `scripts/migrate_*.py`
- Creates automatic DB backups before deploy

## Python Path Note

When importing from `src/`, scripts use:
```python
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
```
