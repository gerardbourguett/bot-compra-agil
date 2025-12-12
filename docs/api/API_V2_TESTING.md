# 🧪 Testing API v2.0 Expandida

## 🚀 Inicio Rápido

### Detener API v1 y Iniciar v2

```bash
# Si la API v1 está corriendo, detenerla con CTRL+C

# Iniciar API v2.0 expandida
python api_backend_v2.py
```

**URL Base:** http://localhost:8000
**Swagger Docs:** http://localhost:8000/api/docs

---

## 📋 Nuevos Endpoints (v2.0)

### 1. Licitaciones

```bash
# Listar con paginación
curl "http://localhost:8000/api/v1/licitaciones/?page=1&limit=20"

# Filtrar por estado y organismo
curl "http://localhost:8000/api/v1/licitaciones/?estado=Publicada&organismo=Ministerio&limit=10"

# Ordenar por monto descendente
curl "http://localhost:8000/api/v1/licitaciones/?order_by=-monto_disponible&limit=5"

# Obtener detalle completo (con productos e historial)
curl "http://localhost:8000/api/v1/licitaciones/1234-56-LQ23"
```

**Respuesta con paginación:**
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

### 2. Productos

```bash
# Buscar productos
curl "http://localhost:8000/api/v1/productos/search?q=laptop&limit=10"

# Productos de una licitación específica
curl "http://localhost:8000/api/v1/productos/licitacion/1234-56-LQ23"
```

---

### 3. Historial

```bash
# Timeline de una licitación
curl "http://localhost:8000/api/v1/historial/1234-56-LQ23?limit=50"

# Historial de usuario con paginación
curl "http://localhost:8000/api/v1/historial/user/123456?page=1&limit=20"
```

---

### 4. Licitaciones Guardadas

```bash
# Ver guardadas de un usuario
curl "http://localhost:8000/api/v1/guardadas/user/123456"

# Guardar una licitación
curl -X POST "http://localhost:8000/api/v1/guardadas" \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_user_id": 123456,
    "codigo_licitacion": "1234-56-LQ23",
    "notas": "Interesante para Q1"
  }'

# Eliminar guardada
curl -X DELETE "http://localhost:8000/api/v1/guardadas/1"
```

---

### 5. Perfiles

```bash
# Obtener perfil
curl "http://localhost:8000/api/v1/perfiles/123456"

# Actualizar perfil
curl -X PUT "http://localhost:8000/api/v1/perfiles/123456" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre_empresa": "Mi Empresa SPA",
    "tipo_negocio": "Tecnología",
    "palabras_clave": "laptop, computador, tecnología"
  }'
```

---

### 6. Análisis y Feedback

```bash
# Obtener análisis en caché
curl "http://localhost:8000/api/v1/analisis/cache/1234-56-LQ23"

# Registrar feedback
curl -X POST "http://localhost:8000/api/v1/analisis/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_user_id": 123456,
    "codigo_licitacion": "1234-56-LQ23",
    "feedback": 1
  }'
```

---

### 7. Estadísticas Avanzadas

```bash
# Stats por organismo
curl "http://localhost:8000/api/v1/stats/advanced/organismo/Ministerio"

# Stats por región
curl "http://localhost:8000/api/v1/stats/advanced/region/RM"
```

---

## 🔥 Testing desde Next.js

### Crear cliente API

```typescript
// lib/api-v2.ts
const API_URL = 'http://localhost:8000';

export const apiV2 = {
  // Licitaciones
  async getLicitaciones(params: {
    page?: number;
    limit?: number;
    estado?: string;
    organismo?: string;
    order_by?: string;
  }) {
    const query = new URLSearchParams(params as any).toString();
    const res = await fetch(`${API_URL}/api/v1/licitaciones/?${query}`);
    return res.json();
  },
  
  async getLicitacion(codigo: string) {
    const res = await fetch(`${API_URL}/api/v1/licitaciones/${codigo}`);
    return res.json();
  },
  
  // Productos
  async searchProductos(q: string, limit = 20) {
    const res = await fetch(
      `${API_URL}/api/v1/productos/search?q=${encodeURIComponent(q)}&limit=${limit}`
    );
    return res.json();
  },
  
  // Guardadas
  async getGuardadas(telegram_id: number, page = 1) {
    const res = await fetch(
      `${API_URL}/api/v1/guardadas/user/${telegram_id}?page=${page}&limit=20`
    );
    return res.json();
  },
  
  async guardarLicitacion(data: {
    telegram_user_id: number;
    codigo_licitacion: string;
    notas?: string;
  }) {
    const res = await fetch(`${API_URL}/api/v1/guardadas`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res.json();
  },
  
  // Stats avanzadas
  async getStatsOrganismo(nombre: string) {
    const res = await fetch(
      `${API_URL}/api/v1/stats/advanced/organismo/${encodeURIComponent(nombre)}`
    );
    return res.json();
  }
};
```

### Componente con Paginación

```tsx
// components/LicitacionesList.tsx
'use client';
import { useState, useEffect } from 'react';
import { apiV2 } from '@/lib/api-v2';

export default function LicitacionesList() {
  const [data, setData] = useState<any>(null);
  const [page, setPage] = useState(1);
  const [loading setLoading] = useState(false);
  
  useEffect(() => {
    loadData();
  }, [page]);
  
  const loadData = async () => {
    setLoading(true);
    const result = await apiV2.getLicitaciones({ page, limit: 20 });
    setData(result);
    setLoading(false);
  };
  
  if (!data) return <div>Cargando...</div>;
  
  return (
    <div>
      <h1>Licitaciones ({data.pagination.total})</h1>
      
      {data.data.map((lic: any) => (
        <div key={lic.codigo} className="border p-4 my-2">
          <h3>{lic.nombre}</h3>
          <p>Monto: ${lic.monto_disponible?.toLocaleString()}</p>
          <p>Estado: {lic.estado}</p>
        </div>
      ))}
      
      {/* Paginación */}
      <div className="flex gap-2 mt-4">
        <button 
          disabled={page === 1}
          onClick={() => setPage(p => p - 1)}
        >
          Anterior
        </button>
        
        <span>Página {page} de {data.pagination.pages}</span>
        
        <button 
          disabled={page === data.pagination.pages}
          onClick={() => setPage(p => p + 1)}
        >
          Siguiente
        </button>
      </div>
    </div>
  );
}
```

---

## ✅ Test Completo Checklist

### Endpoints Básicos
- [ ] GET `/` - Info de API
- [ ] GET `/health` - Health check

### Licitaciones
- [ ] GET `/api/v1/licitaciones/` - Listar
- [ ] GET `/api/v1/licitaciones/?page=2` - Paginación
- [ ] GET `/api/v1/licitaciones/?estado=Publicada` - Filtro
- [ ] GET `/api/v1/licitaciones/{codigo}` - Detalle

### Productos
- [ ] GET `/api/v1/productos/search?q=laptop` - Búsqueda
- [ ] GET `/api/v1/productos/licitacion/{codigo}` - Por licitación

### Historial
- [ ] GET `/api/v1/historial/{codigo}` - De licitación
- [ ] GET `/api/v1/historial/user/{id}` - De usuario

### Guardadas
- [ ] GET `/api/v1/guardadas/user/{id}` - Listar
- [ ] POST `/api/v1/guardadas` - Crear
- [ ] DELETE `/api/v1/guardadas/{id}` - Eliminar

### Perfiles
- [ ] GET `/api/v1/perfiles/{id}` - Obtener
- [ ] PUT `/api/v1/perfiles/{id}` - Actualizar

### Análisis
- [ ] GET `/api/v1/analisis/cache/{codigo}` - Caché
- [ ] POST `/api/v1/analisis/feedback` - Feedback

### Stats Avanzadas
- [ ] GET `/api/v1/stats/advanced/organismo/{nombre}` - Por organismo
- [ ] GET `/api/v1/stats/advanced/region/{nombre}` - Por región

### ML (de v1)
- [ ] POST `/api/v1/ml/precio` - Precio óptimo
- [ ] POST `/api/v1/historico/buscar` - Búsqueda RAG
- [ ] GET `/api/v1/stats` - Stats generales
- [ ] POST `/api/v1/ml/competencia` - Competencia

---

## 📊 Performance Testing

Con los índices optimizados, espera estos tiempos:

- **Listar licitaciones (paginado):** < 100ms
- **Búsqueda de productos:** < 200ms
- **Historial de licitación:** < 50ms
- **Stats por región:** < 100ms
- **Detalle completo:** < 150ms

---

## 🔄 Próxima Fase: Redis Cache

Una vez que todos los endpoints funcionen, implementaremos:
1. Cache de stats generales (TTL: 1h)
2. Cache de búsquedas frecuentes (TTL: 30min)
3. Rate limiting por IP

---

**Versión:** 2.0.0  
**Última actualización:** 2025-12-11
