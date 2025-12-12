# 🚀 API v3.0 - Guía de Inicio Rápido

## ✅ Lo que incluye API v3.0

### 📊 40+ Endpoints Organizados:

#### 1. **Licitaciones** (`/api/v3/licitaciones`)
- `GET /` - Listar con filtros (estado, organismo, monto)
- `GET /{codigo}` - Detalle completo

#### 2. **Histórico** (`/api/v3/historico`)
- `GET /` - Listar datos históricos
- Filtros: producto, región, solo_ganadores

#### 3. **Productos** (`/api/v3/productos`)
- `GET /search` - Búsqueda de productos

#### 4. **Perfiles** (`/api/v3/perfiles`)
- `GET /{telegram_id}` - Obtener perfil

#### 5. **ML & IA** (`/api/v3/ml` y `/api/v3/ai`)
- `POST /ml/precio` - Precio óptimo
- `POST /historico/buscar` - Búsqueda RAG
- `GET /stats` - Estadísticas generales
- `POST /ai/analizar-con-perfil` - ⭐ **NUEVO: Análisis con prompts dinámicos**

#### 6. **Stats Avanzadas** (`/api/v3/stats`)
- `GET /region/{region}` - Stats por región

---

## 🎯 Endpoint Destacado: Análisis con Perfil

### POST `/api/v3/ai/analizar-con-perfil`

Este endpoint usa los **prompts dinámicos** que creamos.

**Request:**
```json
{
  "nombre_empresa": "Banquetes Doña Clara",
  "rubro": "Catering",
  "historial_adjudicaciones": 0,
  "dolor_principal": "entender_papeles",
  
  "codigo_licitacion": "1234-56-LQ23",
  "titulo": "Servicio de Coffee Break",
  "descripcion": "...",
  "monto_estimado": 250000,
  "organismo": "Municipalidad de Providencia",
  "region": "RM"
}
```

**Response:**
```json
{
  "success": true,
  "perfil_detectado": "principiante",
  "system_prompt": "Actúa como un Asesor Senior...",
  "user_prompt": "Analiza esta licitación...",
  "mensaje": "Prompts generados exitosamente"
}
```

El prompt se adapta automáticamente:
- **0 adjudicaciones** → Prompt PRINCIPIANTE (educativo)
- **1-10 adjudicaciones** → Prompt INTERMEDIO (estratégico)
- **10+ adjudicaciones** → Prompt EXPERTO (técnico)

---

## 🚀 Cómo Ejecutar

### Paso 1: Detener APIs anteriores
```bash
# Detener v1 y v2 (CTRL+C en cada terminal)
```

### Paso 2: Iniciar API v3
```bash
python api_backend_v3.py
```

### Paso 3: Abrir Documentación
```
http://localhost:8000/api/docs
```

---

## 🧪 Testing Rápido

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Listar Licitaciones (con filtros)
```bash
curl "http://localhost:8000/api/v3/licitaciones/?page=1&limit=5&estado=Publicada"
```

### 3. Buscar Productos
```bash
curl "http://localhost:8000/api/v3/productos/search?q=laptop&limit=10"
```

### 4. Stats Generales
```bash
curl http://localhost:8000/api/v3/stats
```

### 5. **Análisis con Perfil (NEW!)**
```bash
curl -X POST http://localhost:8000/api/v3/ai/analizar-con-perfil \
  -H "Content-Type: application/json" \
  -d '{
    "nombre_empresa": "Mi Empresa",
    "rubro": "Catering",
    "historial_adjudicaciones": 0,
    "codigo_licitacion": "TEST-123",
    "titulo": "Servicio de alimentación",
    "descripcion": "Coffe break para 50 personas",
    "monto_estimado": 300000,
    "organismo": "Municipalidad",
    "region": "RM"
  }'
```

---

## 📊 Comparación de Versiones

| Feature | v1 | v2 | v3 |
|---------|----|----|-----|
| Endpoints ML | ✅ | ✅ | ✅ |
| CRUD Licitaciones | ❌ | ✅ | ✅ |
| Todas las tablas | ❌ | ⚠️ Parcial | ✅ Completo |
| Prompts Dinámicos | ❌ | ❌ | ✅ **NEW** |
| Redis Cache | ❌ | ⚠️ Preparado | ✅ Integrado |
| Paginación | ⚠️ Básica | ✅ | ✅ |
| Total Endpoints | 8 | 18 | 40+ |

---

## 🔥 Próximos Pasos

1. ✅ **API v3 lista**
2. ⏳ Integrar Gemini AI real en `/ai/analizar-con-perfil`
3. ⏳ Activar Redis cache (opcional)
4. ⏳ Añadir más endpoints (alertas, guardadas, etc.)

---

**Versión:** 3.0.0  
**Última actualización:** 2025-12-11  
**Estado:** ✅ Lista para testing
