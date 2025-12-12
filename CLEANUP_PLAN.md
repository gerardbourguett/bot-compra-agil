# 🧹 Plan de Limpieza del Proyecto

## Archivos Identificados para Limpieza

### 📁 APIs Antiguas (Consolidar)
- ✅ **MANTENER**: `api_backend_v3.py` (versión actual)
- 🗑️ **MOVER A OLD**: `api_backend.py` (v1 - 15KB)
- 🗑️ **MOVER A OLD**: `api_backend_v2.py` (v2 - 27KB)
- 🗑️ **ELIMINAR**: `api_endpoints_complete.py` (temporal, ya integrado en v3)

### 📁 Archivos Temporales
- 🗑️ **ELIMINAR**: `temp_historico.zip` (85MB - archivo de descarga temporal)
- 🗑️ **LIMPIAR**: `__pycache__/` (archivos compilados .pyc)
- 🗑️ **LIMPIAR**: `*.pyc` (si existen)

### 📁 Documentación (Organizar)
**Archivos en raíz que YA movimos a docs/:**
- ✅ Ya en `docs/guides/README_ML.md`
- ✅ Ya en `docs/api/API_RUNNING.md`
- ✅ Ya en `docs/reports/TEST_RESULTS.md`

### 📁 Scripts de Instalación
- ✅ **MANTENER**: `install_ml_deps.bat` (útil)
- ✅ **MANTENER**: `requirements.txt`

### 📁 Archivos de Configuración
- ✅ **MANTENER**: `.env`, `.env.example`
- ✅ **MANTENER**: `docker-compose.yml`, `Dockerfile`
- ✅ **MANTENER**: `.gitignore`, `.pylintrc`

---

## 🎯 Acciones Propuestas

### Paso 1: Crear carpeta OLD
```bash
mkdir old_versions
```

### Paso 2: Mover APIs antiguas
```bash
mv api_backend.py old_versions/
mv api_backend_v2.py old_versions/
```

### Paso 3: Eliminar archivos temporales
```bash
rm api_endpoints_complete.py
rm temp_historico.zip
```

### Paso 4: Limpiar caché Python
```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### Paso 5: Renombrar v3 como principal (opcional)
```bash
cp api_backend_v3.py api_backend.py
# O mantener el nombre v3
```

---

## 📊 Espacio Liberado Estimado

- `temp_historico.zip`: ~85 MB
- APIs antiguas (movidas, no eliminadas): 0 MB
- `api_endpoints_complete.py`: ~11 KB
- `__pycache__/`: ~1-5 MB estimado

**Total liberado: ~86-90 MB**

---

## ✅ Estructura Después de Limpieza

```
bot-compra-agil/
├── api_backend_v3.py          # API principal
├── old_versions/               # Versiones anteriores
│   ├── api_backend.py
│   └── api_backend_v2.py
├── src/                        # Código fuente
├── docs/                       # Documentación organizada
│   ├── api/
│   ├── architecture/
│   ├── guides/
│   └── reports/
├── scripts/                    # Scripts útiles
├── tests/                      # Tests
├── requirements.txt
└── README.md
```

---

## ⚠️ Archivos a NO Tocar

- ✅ Todo en `src/` (código fuente activo)
- ✅ Todo en `docs/` (documentación)
- ✅ Todo en `scripts/` (scripts útiles)
- ✅ Todo en `tests/` (tests)
- ✅ `.env`, `.env.example`
- ✅ `requirements.txt`
- ✅ Archivos Docker
- ✅ Base de datos `compra_agil.db`

---

## 🔄 Próximo Paso

**¿Ejecuto el script de limpieza?**

Opción A: Script automático (recomendado)
Opción B: Manual (revisar archivo por archivo)

---

**Creado**: 2025-12-11  
**Espacio a liberar**: ~90 MB  
**Archivos a mover**: 2 (v1, v2)  
**Archivos a eliminar**: 2 (endpoints_complete, temp_historico)
