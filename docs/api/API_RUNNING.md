# 🚀 API REST - Corriendo y Lista

## ✅ Estado: SERVIDOR ACTIVO

**URL Base:** http://localhost:8000

### 📚 Enlaces Importantes:

- **Documentación interactiva (Swagger):** http://localhost:8000/api/docs
- **Documentación alternativa (ReDoc):** http://localhost:8000/api/redoc  
- **Health Check:** http://localhost:8000/health
- **Endpoint raíz:** http://localhost:8000

---

## 🧪 Probar la API

### Opción 1: Navegador (más fácil)

1. Abre: http://localhost:8000/api/docs
2. Verás todos los endpoints con interfaz interactiva
3. Click en cualquier endpoint → "Try it out" → Ejecutar

### Opción 2: curl (línea de comandos)

```bash
# Health check
curl http://localhost:8000/health

# Precio óptimo
curl -X POST http://localhost:8000/api/v1/ml/precio \
  -H "Content-Type: application/json" \
  -d "{\"producto\": \"laptop\", \"cantidad\": 10}"

# Búsqueda histórica
curl -X POST http://localhost:8000/api/v1/historico/buscar \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"laptop dell\", \"limite\": 5}"

# Estadísticas generales
curl http://localhost:8000/api/v1/stats

# Competencia
curl -X POST "http://localhost:8000/api/v1/ml/competencia?producto=laptop"
```

### Opción 3: JavaScript/Fetch (para Next.js)

```javascript
// Precio óptimo
const response = await fetch('http://localhost:8000/api/v1/ml/precio', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    producto: 'laptop',
    cantidad: 10
  })
});

const data = await response.json();
console.log(data);
```

---

## 📡 Endpoints Disponibles

### 1. Health Check
```
GET /health
```
Verifica que la API y base de datos están funcionando.

### 2. Precio Óptimo
```
POST /api/v1/ml/precio
Body: {
  "producto": "laptop",
  "cantidad": 10,
  "region": "RM"  // opcional
}
```

### 3. Búsqueda Histórica
```
POST /api/v1/historico/buscar
Body: {
  "query": "laptop dell",
  "limite": 10
}
```

### 4. Análisis Enriquecido (RAG)
```
POST /api/v1/ml/analisis
Body: {
  "nombre_licitacion": "Adquisición de computadores",
  "monto_estimado": 5000000
}
```

### 5. Estadísticas Generales
```
GET /api/v1/stats
```

### 6. Estadísticas de Producto
```
POST /api/v1/stats/producto
Body: {
  "producto": "laptop"
}
```

### 7. Análisis de Competencia
```
POST /api/v1/ml/competencia?producto=laptop
```

---

## 🎨 Ejemplo de Test Completo

```bash
# 1. Verificar que la API está viva
curl http://localhost:8000/health

# Respuesta esperada:
# {"status":"healthy","database":"connected","timestamp":"2025-12-10T..."}

# 2. Obtener precio óptimo
curl -X POST http://localhost:8000/api/v1/ml/precio \
  -H "Content-Type: application/json" \
  -d '{"producto": "laptop", "cantidad": 10}'

# Respuesta esperada:
# {
#   "success": true,
#   "precio_unitario": {"recomendado": 625820.5, ...},
#   "precio_total": {"recomendado": 6258205.0, ...},
#   "estadisticas": {...},
#   "confianza": 0.95
# }

# 3. Buscar casos históricos
curl -X POST http://localhost:8000/api/v1/historico/buscar \
  -H "Content-Type: application/json" \
  -d '{"query": "computador", "limite": 5}'

# Respuesta esperada:
# {
#   "success": true,
#   "total": 5,
#   "casos": [...]
# }
```

---

## 🔧 Desarrollo con Next.js

### Setup en Next.js:

```typescript
// lib/api.ts
const API_URL = 'http://localhost:8000';

export const api = {
  async precioOptimo(producto: string, cantidad: number) {
    const res = await fetch(`${API_URL}/api/v1/ml/precio`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ producto, cantidad })
    });
    return res.json();
  },
  
  async buscarHistorico(query: string, limite = 10) {
    const res = await fetch(`${API_URL}/api/v1/historico/buscar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, limite })
    });
    return res.json();
  },
  
  async stats() {
    const res = await fetch(`${API_URL}/api/v1/stats`);
    return res.json();
  }
};
```

### Uso en Componente:

```tsx
// app/page.tsx
'use client';
import { useState } from 'react';
import { api } from '@/lib/api';

export default function Home() {
  const [precio, setPrecio] = useState(null);
  
  const calcular = async () => {
    const data = await api.precioOptimo('laptop', 10);
    setPrecio(data);
  };
  
  return (
    <div>
      <button onClick={calcular}>Calcular Precio</button>
      {precio?.success && (
        <p>Precio recomendado: ${precio.precio_total.recomendado}</p>
      )}
    </div>
  );
}
```

---

## 📝 Notas

- ✅ **CORS configurado** para localhost:3000 (Next.js dev)
- ✅ **Documentación automática** en /api/docs
- ✅ **Hot reload activo** - cambios se aplican automáticamente
- ⚠️  **Warnings de Pydantic** son solo deprecation notices (no afectan funcionalidad)

---

## 🛑 Cómo Detener la API

Presiona `CTRL+C` en la terminal donde está corriendo.

---

**Siguiente paso:** Abre http://localhost:8000/api/docs y prueba los endpoints interactivamente! 🎉
