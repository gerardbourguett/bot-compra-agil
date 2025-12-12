# API REST Expandida - CompraÁgil

## 🎯 Nuevos Endpoints Implementados

### 1. **Licitaciones** (`/api/v1/licitaciones`)

#### GET /api/v1/licitaciones/
Lista licitaciones con filtros y paginación
- **Query params:**
  - `page`: Página (default: 1)
  - `limit`: Resultados por página (default: 20)
  - `estado`: Filtrar por estado
  - `organismo`: Filtrar por organismo
  - `monto_min`: Monto mínimo
  - `monto_max`: Monto máximo
  - `order_by`: Campo para ordenar (default: fecha_cierre)

#### GET /api/v1/licitaciones/{codigo}
Obtiene detalle completo de una licitación
- Incluye productos solicitados
- Incluye historial
- Incluye datos de detalle_extended

---

### 2. **Productos** (`/api/v1/productos`)

#### GET /api/v1/productos/search
Búsqueda de productos solicitados
- **Query params:**
  - `q`: Término de búsqueda
  - `limit`: Máximo de resultados

#### GET /api/v1/productos/licitacion/{codigo}
Productos de una licitación específica

---

### 3. **Historial** (`/api/v1/historial`)

#### GET /api/v1/historial/{codigo}
Timeline de actividad de una licitación

#### GET /api/v1/historial/user/{telegram_id}
Historial de interacciones de un usuario

---

### 4. **Análisis** (`/api/v1/analisis`)

#### GET /api/v1/analisis/cache/{codigo}
Obtiene análisis en caché

#### POST /api/v1/analisis/feedback
Registra feedback de análisis
```json
{
  "telegram_user_id": 123456,
  "codigo_licitacion": "1234-56-LQ23",
  "feedback": 1  // 1 = útil, 0 = no útil
}
```

---

### 5. **Guardadas** (`/api/v1/guardadas`)

#### GET /api/v1/guardadas/user/{telegram_id}
Licitaciones guardadas de un usuario

#### POST /api/v1/guardadas
Guardar una licitación
```json
{
  "telegram_user_id": 123456,
  "codigo_licitacion": "1234-56-LQ23",
  "notas": "Interesante para Q1 2025"
}
```

#### DELETE /api/v1/guardadas/{id}
Eliminar licitación guardada

---

### 6. **Perfiles** (`/api/v1/perfiles`)

#### GET /api/v1/perfiles/{telegram_id}
Obtiene perfil de empresa

#### PUT /api/v1/perfiles/{telegram_id}
Actualiza perfil de empresa

---

### 7. **Estadísticas Avanzadas** (`/api/v1/stats/advanced`)

#### GET /api/v1/stats/advanced/organismo/{nombre}
Estadísticas de un organismo específico

#### GET /api/v1/stats/advanced/region/{nombre}
Estadísticas de una región

#### GET /api/v1/stats/advanced/tendencias
Tendencias del mercado (últimos 6 meses)

---

### 8. **Reportes** (`/api/v1/reports`)

#### POST /api/v1/reports/competencia
Reporte completo de competidores
```json
{
  "producto": "laptop",
  "fecha_desde": "2024-01-01",
  "fecha_hasta": "2024-12-31"
}
```

#### POST /api/v1/reports/mercado
Reporte de análisis de mercado
```json
{
  "categoria": "tecnología",
  "regiones": ["RM", "Valparaíso"]
}
```

---

## 📊 Paginación

Todos los endpoints lista retornan:
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 26893,
    "pages": 1345
  }
}
```

---

## 🔍 Filtros Avanzados

### Ejemplo: Búsqueda compleja de licitaciones
```
GET /api/v1/licitaciones/?estado=Publicada&organismo=Ministerio&monto_min=1000000&order_by=-monto_disponible&limit=50
```

---

## ⚡ Performance

Con los nuevos índices:
- **Búsquedas en histórico:** < 100ms  (antes: 5-10s)
- **Stats por región:** < 50ms  (antes: 2-5s)
- **Búsqueda de productos:** < 200ms (antes: 10s+)

---

## 📝 Próximos Endpoints

### En desarrollo:
- `/api/v1/export` - Exportar datos a Excel/CSV
- `/api/v1/webhooks` - Sistema de webhooks
- `/api/v1/alertas` - Gestión de alertas
- `/api/v1/metrics` - Métricas de uso

---

**Versión API:** 1.1.0  
**Última actualización:** 2025-12-11
