# API REST - Documentación para Next.js Frontend

## 🚀 Quick Start

### 1. Iniciar el Backend

```bash
# Instalar dependencias
pip install fastapi uvicorn

# Ejecutar servidor
python api_backend.py
```

El servidor estará disponible en:
- **API**: http://localhost:8000
- **Documentación interactiva**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### 2. Probar desde Next.js

```typescript
// lib/api.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = {
  async precioOptimo(producto: string, cantidad: number) {
    const response = await fetch(`${API_URL}/api/v1/ml/precio`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ producto, cantidad })
    });
    return response.json();
  },
  
  async buscarHistorico(query: string) {
    const response = await fetch(`${API_URL}/api/v1/historico/buscar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, limite: 10 })
    });
    return response.json();
  },
  
  async statsGenerales() {
    const response = await fetch(`${API_URL}/api/v1/stats`);
    return response.json();
  }
};
```

---

## 📡 Endpoints Disponibles

### 1. **Precio Óptimo** 💰

Calcula el precio óptimo basado en datos históricos.

**Endpoint:** `POST /api/v1/ml/precio`

**Request:**
```json
{
  "producto": "laptop dell",
  "cantidad": 10,
  "region": "RM",
  "solo_ganadores": true
}
```

**Response:**
```json
{
  "success": true,
  "precio_unitario": {
    "recomendado": 625820.50,
    "p25": 450000.00,
    "p50": 598500.00,
    "p75": 850000.00,
    "promedio": 650000.00
  },
  "precio_total": {
    "recomendado": 6258205.00,
    "minimo_competitivo": 4500000.00,
    "maximo_aceptable": 8500000.00
  },
  "estadisticas": {
    "n_registros": 156,
    "n_ganadores": 78,
    "tasa_conversion": 50.0,
    "solo_ganadores": true,
    "region": "RM"
  },
  "confianza": 0.95,
  "recomendacion": "Alta confianza (basado en 156 registros históricos)..."
}
```

**Ejemplo Next.js:**
```tsx
// components/PrecioOptimo.tsx
'use client';
import { useState } from 'react';

export default function PrecioOptimo() {
  const [data, setData] = useState(null);
  
  const calcular = async () => {
    const response = await fetch('http://localhost:8000/api/v1/ml/precio', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        producto: 'laptop',
        cantidad: 10
      })
    });
    const result = await response.json();
    setData(result);
  };
  
  return (
    <div>
      <button onClick={calcular}>Calcular Precio</button>
      {data?.success && (
        <div>
          <h3>Precio Recomendado: ${data.precio_total.recomendado.toLocaleString()}</h3>
          <p>Confianza: {(data.confianza * 100).toFixed(0)}%</p>
        </div>
      )}
    </div>
  );
}
```

---

### 2. **Búsqueda Histórica** 🔍

Busca licitaciones similares en el histórico.

**Endpoint:** `POST /api/v1/historico/buscar`

**Request:**
```json
{
  "query": "laptop dell",
  "limite": 10,
  "umbral_similitud": 50
}
```

**Response:**
```json
{
  "success": true,
  "total": 10,
  "casos": [
    {
      "codigo": "1234-56-LQ23",
      "nombre": "Adquisición de notebooks Dell Latitude",
      "producto": "Laptop Dell Latitude 5520",
      "proveedor": "TECH SOLUTIONS SPA",
      "monto": 8500000,
      "cantidad": 15,
      "precio_unitario": 566666,
      "es_ganador": true,
      "fecha_cierre": "2024-10-15",
      "region": "RM",
      "similitud": 92.5,
      "antiguedad_dias": 55
    }
  ]
}
```

**Ejemplo Next.js:**
```tsx
// components/BusquedaHistorico.tsx
'use client';

export default function BusquedaHistorico() {
  const [casos, setCasos] = useState([]);
  
  const buscar = async (query: string) => {
    const response = await fetch('http://localhost:8000/api/v1/historico/buscar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, limite: 10 })
    });
    const result = await response.json();
    setCasos(result.casos);
  };
  
  return (
    <div>
      <input onChange={(e) => buscar(e.target.value)} placeholder="Buscar..." />
      {casos.map(caso => (
        <div key={caso.codigo}>
          <h4>{caso.nombre}</h4>
          <p>Monto: ${caso.monto.toLocaleString()}</p>
          <span>{caso.es_ganador ? '✅ Ganado' : '❌ No ganado'}</span>
        </div>
      ))}
    </div>
  );
}
```

---

### 3. **Análisis Enriquecido (RAG)** 🤖

Genera análisis con contexto histórico para IA.

**Endpoint:** `POST /api/v1/ml/analisis`

**Request:**
```json
{
  "nombre_licitacion": "Adquisición de computadores portátiles",
  "monto_estimado": 5000000,
  "descripcion": "Laptops para oficina administrativa"
}
```

**Response:**
```json
{
  "success": true,
  "n_casos": 47,
  "insights": "📊 INSIGHTS BASADOS EN 47 CASOS HISTÓRICOS:\n✅ Ofertas Ganadoras: 23 (48.9%)\n...",
  "contexto": "📚 DATOS HISTÓRICOS DE LICITACIONES SIMILARES:\n...",
  "recomendacion_precio": {
    "basado_en_ganadores": true,
    "precio_promedio": 625820,
    "precio_mediana": 598500,
    "rango_min": 450000,
    "rango_max": 850000
  }
}
```

**Uso:** Ideal para mostrar contexto antes de que el usuario haga un análisis completo.

---

### 4. **Análisis de Competencia** 🎯

Analiza competidores para un producto.

**Endpoint:** `POST /api/v1/ml/competencia?producto=laptop`

**Response:**
```json
{
  "success": true,
  "total_competidores": 127,
  "top_competidores": [
    {
      "nombre": "TECH SOLUTIONS SPA",
      "ofertas": 89,
      "tasa_exito": 50.6,
      "precio_promedio": 625000.0
    }
  ],
  "estadisticas_generales": {
    "precio_min": 350000.0,
    "precio_max": 1200000.0,
    "precio_promedio": 625820.5,
    "desviacion_std": 125000.0
  }
}
```

---

### 5. **Estadísticas Generales** 📊

Estadísticas del histórico completo.

**Endpoint:** `GET /api/v1/stats`

**Response:**
```json
{
  "total_registros": 3245678,
  "ofertas_ganadoras": 1458923,
  "tasa_conversion": 44.9,
  "monto_promedio": 2458320.5,
  "top_regiones": [
    {"region": "Región Metropolitana", "total": 856234},
    {"region": "Valparaíso", "total": 234567}
  ]
}
```

**Ejemplo Next.js (Server Component):**
```tsx
// app/dashboard/page.tsx
export default async function Dashboard() {
  const response = await fetch('http://localhost:8000/api/v1/stats', {
    cache: 'no-store' // o { next: { revalidate: 3600 } }
  });
  const stats = await response.json();
  
  return (
    <div>
      <h1>Dashboard</h1>
      <p>Total licitaciones: {stats.total_registros.toLocaleString()}</p>
      <p>Tasa conversión: {stats.tasa_conversion.toFixed(1)}%</p>
    </div>
  );
}
```

---

### 6. **Estadísticas de Producto** 📈

Estadísticas específicas de un producto.

**Endpoint:** `POST /api/v1/stats/producto`

**Request:**
```json
{
  "producto": "laptop",
  "limite": 1000
}
```

**Response:**
```json
{
  "success": true,
  "total_ofertas": 1245,
  "ofertas_ganadoras": 623,
  "tasa_conversion": 50.0,
  "precio_unitario": {
    "minimo": 350000.0,
    "promedio": 625820.0,
    "mediana": 598500.0,
    "maximo": 1200000.0
  },
  "top_proveedores": [
    {"nombre": "TECH SOLUTIONS SPA", "victorias": 45},
    {"nombre": "COMPUTACIÓN INTEGRAL", "victorias": 38}
  ]
}
```

---

## 🔧 Utilities para Next.js

### Hook Personalizado

```typescript
// hooks/useApi.ts
import { useState, useEffect } from 'react';

export function useStats() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetch('http://localhost:8000/api/v1/stats')
      .then(res => res.json())
      .then(data => {
        setData(data);
        setLoading(false);
      });
  }, []);
  
  return { data, loading };
}

export function usePrecioOptimo(producto: string, cantidad: number) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const calcular = async () => {
    setLoading(true);
    const response = await fetch('http://localhost:8000/api/v1/ml/precio', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ producto, cantidad })
    });
    const result = await response.json();
    setData(result);
    setLoading(false);
  };
  
  return { data, loading, calcular };
}
```

---

## 🌐 CORS Configuration

El backend ya está configurado para aceptar requests desde:
- `http://localhost:3000` (Next.js dev)
- `http://localhost:3001`
- Tu dominio de producción (configúralo en `api_backend.py`)

---

## 🔐 Autenticación (Próximamente)

```typescript
// lib/auth.ts
export async function login(email: string, password: string) {
  const response = await fetch('http://localhost:8000/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  
  const { access_token, refresh_token } = await response.json();
  
  // Guardar tokens
  localStorage.setItem('access_token', access_token);
  localStorage.setItem('refresh_token', refresh_token);
  
  return access_token;
}

export function getAuthHeaders() {
  const token = localStorage.getItem('access_token');
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  };
}
```

---

## 📦 TypeScript Types

```typescript
// types/api.ts

export interface PrecioOptimo {
  success: boolean;
  precio_unitario?: {
    recomendado: number;
    p25: number;
    p50: number;
    p75: number;
    promedio: number;
  };
  precio_total?: {
    recomendado: number;
    minimo_competitivo: number;
    maximo_aceptable: number;
  };
  estadisticas?: {
    n_registros: number;
    n_ganadores: number;
    tasa_conversion: number;
  };
  confianza?: number;
  recomendacion?: string;
  error?: string;
}

export interface CasoHistorico {
  codigo: string;
  nombre: string;
  producto: string;
  proveedor: string;
  monto: number;
  cantidad: number;
  precio_unitario: number;
  es_ganador: boolean;
  fecha_cierre: string;
  region: string;
  similitud: number;
  antiguedad_dias: number;
}

export interface Stats {
  total_registros: number;
  ofertas_ganadoras: number;
  tasa_conversion: number;
  monto_promedio: number;
  top_regiones: Array<{
    region: string;
    total: number;
  }>;
}
```

---

## ✅ Testing

```bash
# Test de integración rápido
curl http://localhost:8000/health

# Test precio óptimo
curl -X POST http://localhost:8000/api/v1/ml/precio \
  -H "Content-Type: application/json" \
  -d '{"producto": "laptop", "cantidad": 10}'

# Test histórico
curl -X POST http://localhost:8000/api/v1/historico/buscar \
  -H "Content-Type: application/json" \
  -d '{"query": "laptop dell", "limite": 5}'
```

---

## 🚀 Deploy

### Backend (Railway/Render)
```bash
# Procfile
web: uvicorn api_backend:app --host 0.0.0.0 --port $PORT
```

### Frontend (Vercel)
```bash
# .env.production
NEXT_PUBLIC_API_URL=https://tu-api.railway.app
```

---

## 📚 Recursos

- **Swagger UI**: http://localhost:8000/api/docs (Prueba endpoints interactivamente)
- **ReDoc**: http://localhost:8000/api/redoc (Documentación estática)
- **OpenAPI JSON**: http://localhost:8000/openapi.json (Para generadores de código)

---

**Última actualización:** 2025-12-09  
**Versión API:** 1.0.0
