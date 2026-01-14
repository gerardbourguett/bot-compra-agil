"""
Configuración centralizada para CompraAgil.
Todos los valores configurables en un solo lugar.
"""
import os
from dotenv import load_dotenv

load_dotenv()


# ==================== API KEYS & SECRETS ====================
# Estos se cargan de variables de entorno por seguridad

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MERCADO_PUBLICO_API_KEY = os.getenv('MERCADO_PUBLICO_API_KEY')
DATABASE_URL = os.getenv('DATABASE_URL', '')
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')


# ==================== AI / MODELO ====================

# Provider selection: 'gemini', 'groq', 'cerebras', 'openai'
AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini')

# Gemini (Google)
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')

# Groq (fast inference with Llama, Mixtral)
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')

# Cerebras (ultra-fast inference)
CEREBRAS_API_KEY = os.getenv('CEREBRAS_API_KEY')
CEREBRAS_MODEL = os.getenv('CEREBRAS_MODEL', 'llama3.1-8b')

# OpenAI (ChatGPT)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

# Fallback chain (try providers in order if one fails)
AI_FALLBACK_CHAIN = os.getenv('AI_FALLBACK_CHAIN', 'gemini,groq,openai,cerebras').split(',')


# ==================== SERVIDORES ====================

# API Backend (FastAPI)
API_PORT = int(os.getenv('API_PORT', '8001'))
API_HOST = os.getenv('API_HOST', '0.0.0.0')

# Servidor de Metricas (Prometheus)
METRICS_PORT = int(os.getenv('METRICS_PORT', '8000'))
METRICS_HOST = os.getenv('METRICS_HOST', '0.0.0.0')


# ==================== RATE LIMITING ====================
# Límites por minuto (window=60 segundos)

RATE_LIMITS = {
    'global': {
        'max_requests': int(os.getenv('RATE_LIMIT_GLOBAL', '1000')),
        'window': 60
    },
    'ml': {
        'max_requests': int(os.getenv('RATE_LIMIT_ML', '50')),
        'window': 60
    },
    'search': {
        'max_requests': int(os.getenv('RATE_LIMIT_SEARCH', '200')),
        'window': 60
    },
    'auth': {
        'max_requests': int(os.getenv('RATE_LIMIT_AUTH', '20')),
        'window': 60
    },
}


# ==================== CACHE TTLs (segundos) ====================

CACHE_TTL = {
    # Stats y dashboards
    'stats_general': 3600,        # 1 hora
    'stats_region': 1800,         # 30 min
    'stats_organismo': 1800,      # 30 min

    # Licitaciones
    'licitacion': 900,            # 15 min
    'licitacion_list': 600,       # 10 min (cambian rápido)
    'productos': 900,             # 15 min

    # Búsquedas históricas
    'historico_search': 1800,     # 30 min
    'rag_search': 3600,           # 1 hora

    # Machine Learning (más costosos, TTL más largo)
    'ml_precio': 7200,            # 2 horas
    'ml_competencia': 3600,       # 1 hora
    'ml_scoring': 7200,           # 2 horas
    'ml_rag': 3600,               # 1 hora

    # Embeddings y vectores (muy costosos, TTL largo)
    'embeddings': 86400,          # 24 horas

    # Default
    'default': 900,               # 15 min
}


# ==================== SCRAPER ====================

SCRAPER_PAUSE_BETWEEN_REQUESTS = float(os.getenv('SCRAPER_PAUSE', '0.5'))
SCRAPER_MAX_RETRIES = int(os.getenv('SCRAPER_MAX_RETRIES', '3'))


# ==================== BOT TELEGRAM ====================

# Días para considerar licitación como "urgente"
BOT_URGENTE_DIAS = int(os.getenv('BOT_URGENTE_DIAS', '3'))

# Máximo de competidores para "baja competencia"
BOT_MAX_COMPETENCIA_BAJA = int(os.getenv('BOT_MAX_COMPETENCIA', '2'))


# ==================== SUSCRIPCIONES (SaaS) ====================

SUBSCRIPTION_PRICING_CLP = {
    'free': 0,
    'emprendedor': 15000,
    'pyme': 45000,
    'profesional': 150000
}


# ==================== LOGGING ====================

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')  # 'json' o 'text'


# ==================== HELPERS ====================

def get_rate_limit(name: str) -> dict:
    """Obtiene configuración de rate limit por nombre."""
    return RATE_LIMITS.get(name, RATE_LIMITS['global'])


def is_production() -> bool:
    """Detecta si estamos en producción."""
    return os.getenv('ENV', 'development').lower() == 'production'
