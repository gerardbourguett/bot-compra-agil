# Arquitectura Backend SaaS - Compra Ágil

Sistema backend completo para transformar el bot en una plataforma SaaS multi-tenant con suscripciones, pagos y API REST.

## Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                            │
│  • Web App (Next.js)                                        │
│  • Telegram Bot                                             │
│  • Mobile App (futuro)                                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY LAYER                         │
│  • FastAPI (REST API)                                       │
│  • Rate Limiting                                            │
│  • Authentication (JWT)                                     │
│  • Request Validation                                       │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Auth Service│  │ Subscription │  │   ML Service │
│              │  │   Service    │  │              │
│ • Login      │  │ • Plans      │  │ • Predictions│
│ • Register   │  │ • Payments   │  │ • RAG        │
│ • Tokens     │  │ • Webhooks   │  │ • Pricing    │
└──────────────┘  └──────────────┘  └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    DATA LAYER                                │
│  • PostgreSQL (users, subscriptions, licitaciones)          │
│  • Redis (cache, sessions, rate limiting)                   │
│  • S3/Storage (files, models)                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  EXTERNAL SERVICES                           │
│  • Stripe (pagos)                                           │
│  • Gemini API (IA)                                          │
│  • Mercado Público API                                      │
│  • SendGrid (emails)                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Componentes del Backend

### 1. API REST (FastAPI)

**Estructura de directorios:**
```
backend/
├── __init__.py
├── main.py                 # Entry point
├── config.py              # Configuración
├── dependencies.py        # Dependency injection
│
├── api/
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── auth.py        # /auth/login, /auth/register
│   │   ├── users.py       # /users/me, /users/{id}
│   │   ├── subscriptions.py # /subscriptions
│   │   ├── licitaciones.py  # /licitaciones
│   │   ├── ml.py          # /ml/predict, /ml/price
│   │   └── webhooks.py    # /webhooks/stripe
│
├── core/
│   ├── auth.py            # JWT, password hashing
│   ├── security.py        # Security utilities
│   └── rate_limit.py      # Rate limiting
│
├── models/
│   ├── user.py           # SQLAlchemy models
│   ├── subscription.py
│   ├── licitacion.py
│   └── usage.py
│
├── schemas/
│   ├── user.py           # Pydantic schemas
│   ├── subscription.py
│   ├── licitacion.py
│   └── ml.py
│
├── services/
│   ├── auth_service.py
│   ├── subscription_service.py
│   ├── payment_service.py  # Stripe integration
│   ├── ml_service.py
│   └── notification_service.py
│
└── database/
    ├── base.py
    ├── session.py
    └── migrations/        # Alembic migrations
```

---

### 2. Modelos de Datos

**Esquema de Base de Datos:**

```sql
-- Usuarios
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    company_name VARCHAR(255),
    rut VARCHAR(20),
    phone VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Planes de suscripción
CREATE TABLE subscription_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL, -- 'free', 'emprendedor', 'pyme', 'profesional'
    display_name VARCHAR(100),
    price_monthly INTEGER, -- en CLP
    price_yearly INTEGER,
    stripe_price_id VARCHAR(255),
    features JSONB, -- { "ai_analyses_per_day": 5, "saved_licitaciones": 30, ... }
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suscripciones de usuarios
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    plan_id INTEGER REFERENCES subscription_plans(id),
    status VARCHAR(20) NOT NULL, -- 'active', 'canceled', 'past_due', 'trialing'
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    current_period_start DATE,
    current_period_end DATE,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    trial_end DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Uso de recursos (rate limiting y analytics)
CREATE TABLE usage_tracking (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    resource_type VARCHAR(50) NOT NULL, -- 'ai_analysis', 'search', 'export', 'api_call'
    resource_id VARCHAR(255), -- codigo de licitacion, etc
    month DATE NOT NULL, -- primer día del mes
    count INTEGER DEFAULT 1,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, resource_type, month)
);

-- Pagos
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    subscription_id INTEGER REFERENCES subscriptions(id),
    amount INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'CLP',
    status VARCHAR(20) NOT NULL, -- 'pending', 'succeeded', 'failed', 'refunded'
    stripe_payment_intent_id VARCHAR(255),
    payment_method VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Organizaciones (para multi-usuario)
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    owner_id INTEGER REFERENCES users(id),
    subscription_id INTEGER REFERENCES subscriptions(id),
    max_users INTEGER DEFAULT 1,
    settings JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Miembros de organizaciones
CREATE TABLE organization_members (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member', -- 'owner', 'admin', 'member', 'viewer'
    permissions JSONB,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, user_id)
);

-- API Keys (para clientes Enterprise)
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    key_prefix VARCHAR(20), -- Primeros caracteres para identificar
    name VARCHAR(100),
    scopes JSONB, -- ["read:licitaciones", "write:analysis"]
    rate_limit_per_minute INTEGER DEFAULT 60,
    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Webhooks configurables (para Enterprise)
CREATE TABLE webhook_endpoints (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    url VARCHAR(500) NOT NULL,
    events JSONB NOT NULL, -- ["licitacion.new", "licitacion.closing"]
    secret VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Log de webhooks enviados
CREATE TABLE webhook_deliveries (
    id SERIAL PRIMARY KEY,
    webhook_id INTEGER REFERENCES webhook_endpoints(id) ON DELETE CASCADE,
    event_type VARCHAR(50),
    payload JSONB,
    response_status INTEGER,
    response_body TEXT,
    delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX idx_users_telegram ON users(telegram_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_usage_user_month ON usage_tracking(user_id, month);
CREATE INDEX idx_payments_user ON payments(user_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
```

---

### 3. Autenticación y Autorización

**JWT-based Authentication:**

```python
# backend/core/auth.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

SECRET_KEY = "your-secret-key-here"  # En producción: usar env var
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user
```

---

### 4. Rate Limiting por Tier

```python
# backend/core/rate_limit.py
from fastapi import HTTPException, Depends
from redis import Redis
from datetime import datetime

redis_client = Redis(host='localhost', port=6379, db=0)

RATE_LIMITS = {
    'free': {
        'ai_analysis': {'limit': 2, 'period': 'day'},
        'searches': {'limit': 50, 'period': 'day'},
        'api_calls': {'limit': 0, 'period': 'day'},
    },
    'emprendedor': {
        'ai_analysis': {'limit': 5, 'period': 'day'},
        'searches': {'limit': 200, 'period': 'day'},
        'api_calls': {'limit': 0, 'period': 'day'},
    },
    'pyme': {
        'ai_analysis': {'limit': 10, 'period': 'day'},
        'searches': {'limit': 1000, 'period': 'day'},
        'api_calls': {'limit': 0, 'period': 'day'},
    },
    'profesional': {
        'ai_analysis': {'limit': 999999, 'period': 'day'},  # unlimited
        'searches': {'limit': 999999, 'period': 'day'},
        'api_calls': {'limit': 100, 'period': 'day'},
    },
}

async def check_rate_limit(
    user: User,
    resource_type: str,
    db
):
    """Verifica si el usuario ha excedido su límite de uso"""
    
    # Admin siempre tiene acceso ilimitado
    if user.is_admin:
        return True
    
    # Obtener plan del usuario
    subscription = db.query(Subscription).filter(
        Subscription.user_id == user.id,
        Subscription.status == 'active'
    ).first()
    
    plan_name = subscription.plan.name if subscription else 'free'
    limits = RATE_LIMITS.get(plan_name, RATE_LIMITS['free'])
    
    if resource_type not in limits:
        return True
    
    limit_config = limits[resource_type]
    limit = limit_config['limit']
    period = limit_config['period']
    
    # Key de Redis para tracking
    today = datetime.utcnow().date()
    redis_key = f"ratelimit:{user.id}:{resource_type}:{today}"
    
    # Obtener uso actual
    current_usage = redis_client.get(redis_key)
    current_usage = int(current_usage) if current_usage else 0
    
    if current_usage >= limit:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"Has excedido el límite de {limit} {resource_type} por {period}",
                "current_plan": plan_name,
                "upgrade_url": "/pricing"
            }
        )
    
    # Incrementar contador
    redis_client.incr(redis_key)
    redis_client.expire(redis_key, 86400)  # Expira en 24 horas
    
    return True
```

---

### 5. Integración con Stripe

```python
# backend/services/payment_service.py
import stripe
from typing import Dict

stripe.api_key = "sk_test_..."  # Usar env var en producción

PLANS = {
    'emprendedor': {
        'price_id': 'price_emprendedor_monthly',
        'amount': 4990,
    },
    'pyme': {
        'price_id': 'price_pyme_monthly',
        'amount': 9990,
    },
    'profesional': {
        'price_id': 'price_profesional_monthly',
        'amount': 19990,
    },
}

async def create_checkout_session(
    user_id: int,
    plan_name: str,
    success_url: str,
    cancel_url: str
) -> Dict:
    """Crea sesión de checkout de Stripe"""
    
    plan = PLANS.get(plan_name)
    if not plan:
        raise ValueError(f"Plan {plan_name} no existe")
    
    session = stripe.checkout.Session.create(
        customer_email=user.email,
        client_reference_id=str(user_id),
        payment_method_types=['card'],
        line_items=[{
            'price': plan['price_id'],
            'quantity': 1,
        }],
        mode='subscription',
        success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
        cancel_url=cancel_url,
        metadata={
            'user_id': user_id,
            'plan_name': plan_name,
        }
    )
    
    return {
        'session_id': session.id,
        'url': session.url
    }

async def handle_stripe_webhook(payload: dict, sig_header: str):
    """Procesa webhooks de Stripe"""
    
    endpoint_secret = "whsec_..."  # Usar env var
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Manejar eventos
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        await activate_subscription(session)
    
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        await update_subscription(subscription)
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        await cancel_subscription(subscription)
    
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        await handle_payment_failure(invoice)
    
    return {"status": "success"}
```

---

### 6. API Endpoints Principales

```python
# backend/api/v1/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register")
async def register(user_create: UserCreate, db = Depends(get_db)):
    """Registro de nuevo usuario"""
    # Verificar si email ya existe
    # Crear usuario
    # Crear suscripción FREE por defecto
    # Enviar email de verificación
    pass

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db = Depends(get_db)
):
    """Login y generación de tokens"""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect credentials")
    
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """Renovar access token"""
    pass

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Obtener información del usuario actual"""
    return current_user
```

```python
# backend/api/v1/subscriptions.py
router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

@router.get("/plans")
async def get_available_plans():
    """Listar planes disponibles"""
    pass

@router.post("/checkout")
async def create_checkout(
    plan_name: str,
    current_user: User = Depends(get_current_user)
):
    """Crear sesión de pago"""
    checkout_session = await create_checkout_session(
        user_id=current_user.id,
        plan_name=plan_name,
        success_url="https://app.compraagil.cl/success",
        cancel_url="https://app.compraagil.cl/pricing"
    )
    return checkout_session

@router.get("/current")
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Obtener suscripción actual del usuario"""
    pass

@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Cancelar suscripción"""
    pass
```

```python
# backend/api/v1/ml.py
router = APIRouter(prefix="/ml", tags=["Machine Learning"])

@router.post("/predict/probability")
async def predict_win_probability(
    request: ProbabilityRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Predecir probabilidad de ganar licitación"""
    await check_rate_limit(current_user, 'ai_analysis', db)
    
    # Llamar al modelo ML
    resultado = ml_service.predecir_probabilidad(request.dict())
    
    # Registrar uso
    track_usage(current_user.id, 'ai_analysis', db)
    
    return resultado

@router.post("/recommend/price")
async def recommend_price(
    product: str,
    quantity: int,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Recomendar precio óptimo"""
    await check_rate_limit(current_user, 'ai_analysis', db)
    
    from ml_precio_optimo import calcular_precio_optimo
    resultado = calcular_precio_optimo(product, quantity)
    
    return resultado
```

---

## Deployment y DevOps

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/compraagil
      - REDIS_URL=redis://redis:6379/0
      - STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY}
    depends_on:
      - postgres
      - redis
  
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: compraagil
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
```

---

## Próximos Pasos de Implementación

1. ✅ Crear estructura de directorios `backend/`
2. ✅ Implementar modelos SQLAlchemy
3. ✅ Configurar Alembic para migraciones
4. ✅ Implementar autenticación JWT
5. ✅ Crear endpoints principales
6. ✅ Integrar Stripe
7. ✅ Implementar rate limiting
8. ✅ Tests unitarios y de integración
9. ✅ Documentación OpenAPI/Swagger
10. ✅ Deploy en Railway/Render

---

## Estimación de Tiempos

- **Semana 1-2**: Setup base, auth, modelos
- **Semana 3**: Suscripciones y Stripe
- **Semana 4**: API endpoints y rate limiting
- **Semana 5**: Testing y documentación
- **Semana 6**: Deploy y monitoreo

**Total: ~6 semanas para MVP del backend SaaS**
