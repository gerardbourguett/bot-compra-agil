# Bot de Telegram - Compra Ágil

Bot de Telegram para buscar licitaciones de Compra Ágil del Mercado Público de Chile.

## 🚀 Características

- **Obtención automática de licitaciones** desde la API de Mercado Público
- **Autenticación automática** con X-API-Key (no requiere token Bearer)
- **Almacenamiento completo** en base de datos SQLite local:
  - Listado de licitaciones
  - Detalles completos de cada licitación
  - Productos solicitados
  - Historial de acciones
  - Archivos adjuntos
- **Bot de Telegram** para búsquedas interactivas y consulta de detalles
- **Manejo de paginación** para obtener todos los resultados
- **Modo modular**: Ejecutar solo listado, solo detalles, o proceso completo

## 📋 Requisitos

- Python 3.8 o superior
- Token de Bot de Telegram (obtenerlo desde [@BotFather](https://t.me/botfather))

## 🔧 Instalación

1. Clona o descarga este repositorio

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Crea un archivo `.env` basado en `.env.example`:
```bash
cp .env.example .env
```

4. Edita el archivo `.env` y agrega tu token de Telegram:
```
TELEGRAM_TOKEN=tu_token_de_telegram_aqui
```

## 📖 Uso

### 1. Scraper Simple (solo listado)

Para obtener solo el listado de licitaciones sin detalles:

```bash
python scraper.py
```

### 2. Scraper Completo (listado + detalles)

Para obtener tanto el listado como los detalles completos de cada licitación:

```bash
python scraper_completo.py
```

Puedes modificar el archivo para:
- Limitar páginas de listado (para pruebas)
- Limitar número de detalles a obtener
- Cambiar el rango de fechas

### 3. Cliente de API (uso programático)

```python
import api_client

# Obtener listado
data = api_client.obtener_licitaciones("2025-11-01", "2025-11-26")

# Obtener ficha detallada
ficha = api_client.obtener_ficha_detalle("1057389-2539-COT25")

# Obtener historial
historial = api_client.obtener_historial("1057389-2539-COT25")

# Obtener adjuntos
adjuntos = api_client.obtener_adjuntos("1057389-2539-COT25")

# Obtener todo de una vez
detalle = api_client.obtener_detalle_completo("1057389-2539-COT25")
```

### 4. Bot de Telegram

```bash
python bot.py
```

### 5. Comandos del Bot

En Telegram, envía los siguientes comandos:

- `/start` - Inicia el bot y muestra ayuda
- `/buscar [palabra]` - Busca licitaciones por palabra clave
- `/detalle [código]` - Muestra detalles completos de una licitación
- `/stats` - Muestra estadísticas de la base de datos

**Ejemplos:**
```
/buscar computadores
/buscar mascarillas
/detalle 1057389-2539-COT25
/stats
```

## 📁 Estructura del Proyecto

```
.
├── api_client.py          # Cliente de API (funciones para obtener datos)
├── database.py            # Base de datos simple (solo listado)
├── database_extended.py   # Base de datos extendida (con detalles)
├── scraper.py            # Scraper simple (solo listado)
├── scraper_completo.py   # Scraper completo (listado + detalles)
├── bot.py                # Bot de Telegram mejorado
├── test_api.py           # Scripts de prueba de la API
├── test_simple.py        # Script de prueba simple
├── requirements.txt      # Dependencias de Python
├── .env                  # Variables de entorno (no incluido en git)
├── .env.example          # Ejemplo de variables de entorno
├── README.md             # Este archivo
└── compra_agil.db        # Base de datos SQLite (se crea automáticamente)
```

## 🗄️ Estructura de la Base de Datos

### Tabla: `licitaciones`
Información básica del listado de licitaciones.

### Tabla: `licitaciones_detalle`
Información detallada de cada licitación (descripción, presupuesto, fechas, etc.)

### Tabla: `productos_solicitados`
Productos solicitados en cada licitación.

### Tabla: `historial`
Registro de acciones realizadas sobre cada licitación.

### Tabla: `adjuntos`
Archivos adjuntos de cada licitación.

## 🔑 Cómo Funciona la Autenticación

La API de Mercado Público requiere únicamente:
- `X-API-Key: e93089e4-437c-4723-b343-4fa20045e3bc`
- Headers de navegador correctos (`Origin`, `Referer`, etc.)

**No se requiere token Bearer** para acceder a la información pública.

## 📡 Endpoints de la API

1. **Listado**: `https://api.buscador.mercadopublico.cl/compra-agil`
2. **Ficha**: `https://api.buscador.mercadopublico.cl/compra-agil?action=ficha&code={codigo}`
3. **Historial**: `https://api.buscador.mercadopublico.cl/compra-agil?action=historial&code={codigo}`
4. **Adjuntos**: `https://adjunto.mercadopublico.cl/adjunto-compra-agil/v1/adjuntos-compra-agil/listar/{codigo}`

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request.

## ⚠️ Disclaimer

Este proyecto es solo para fines educativos. Asegúrate de cumplir con los términos de servicio de Mercado Público al usar su API.

## 📝 Licencia

MIT

