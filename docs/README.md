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

## Bot Inteligente de Telegram para Compra Ágil 🤖

Sistema completo para ayudar a PYMEs a encontrar, analizar y ganar licitaciones de Compra Ágil del Mercado Público de Chile, potenciado por Gemini AI.

## 🎯 Características Principales

### 🤖 Análisis Inteligente con IA
- Análisis de compatibilidad personalizado (score 0-100)
- Recomendaciones de precio competitivo
- Estrategias para ganar licitaciones
- Guías personalizadas para cotizar
- Análisis de competencia

### 👤 Sistema de Perfiles
- Formulario guiado para configurar perfil empresarial
- Búsquedas personalizadas según tu negocio
- Filtrado automático por tipo de producto/servicio
- Recomendaciones basadas en tu experiencia y capacidades

### 🔍 Búsquedas Avanzadas
- Por palabra clave
- Por tipo (productos vs servicios)
- Por rango de monto
- Licitaciones urgentes (próximas a cerrar)
- Oportunidades compatibles con tu perfil

### ⭐ Gestión de Licitaciones
- Guardar licitaciones de interés
- Seguimiento de guardadas
- Notas personalizadas
- Alertas de cierre próximo

### 🔔 Sistema de Alertas
- Nuevas licitaciones compatibles
- Recordatorios de cierre
- Cambios en licitaciones guardadas

### ✍️ Generador de Ofertas (IA)
- Redacción automática de borradores
- Formatos: Texto Telegram, PDF (Markdown), Correo
- Personalizado según tu perfil y la licitación

### 📊 Reportes Administrativos
- Exportación a Excel (`/exportar_reporte`)
- Análisis de competencia (Top 10 Ganadores)
- Estadísticas de mercado y organismos

## 📦 Componentes del Sistema

```
├── bot_inteligente.py          # Bot principal con todos los comandos
├── gemini_ai.py                # Integración con Gemini 2.5 Pro
├── database_bot.py             # BD extendida (perfiles, guardadas, caché)
├── database_extended.py        # BD principal (licitaciones, detalles)
├── filtros.py                  # Búsquedas y filtros inteligentes
├── api_client.py               # Cliente para API de Mercado Público
├── scraper.py                  # Scraper de listado básico
├── scraper_completo.py         # Scraper completo (listado + detalles)
├── obtener_detalles.py         # Script para obtener detalles
└── GUIA_BOT.md                 # Guía de uso del bot
```

## 🚀 Inicio Rápido

### 1. Requisitos

```bash
Python 3.8+
```

### 2. Instalación

```bash
# Clonar o descargar el proyecto
cd "Nueva carpeta"

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configuración

Crea un archivo `.env` con:

```env
TELEGRAM_TOKEN=tu_token_de_telegram
GEMINI_API_KEY=tu_api_key_de_gemini
```

**Obtener tokens:**
- **Telegram**: Habla con [@BotFather](https://t.me/botfather) en Telegram
- **Gemini**: [Google AI Studio](https://aistudio.google.com/app/apikey)

### 4. Inicializar Base de Datos

```bash
# Crear tablas
python database_extended.py
python database_bot.py

# Obtener licitaciones (primera vez)
python scraper.py

# Obtener detalles (opcional pero recomendado)
python obtener_detalles.py
```

### 5. Iniciar el Bot

```bash
python bot_inteligente.py
```

## 📱 Uso del Bot

### Comandos Principales

#### Configuración
- `/start` - Bienvenida y ayuda
- `/configurar_perfil` - Configurar perfil de empresa
- `/perfil` - Ver perfil actual

#### Búsqueda
- `/buscar [palabra]` - Buscar licitaciones
- `/oportunidades` - Licitaciones para ti
- `/urgentes` - Cierran pronto
- `/por_monto [min] [max]` - Por rango de monto

#### Análisis con IA 🤖
- `/analizar [código]` - Análisis completo
- `/recomendar` - Top 5 recomendadas
- `/ayuda_cotizar [código]` - Guía para cotizar

#### Guardadas
- `/guardar [código]` - Guardar licitación
- `/mis_guardadas` - Ver guardadas
- `/eliminar_guardada [código]` - Eliminar

#### Alertas
- `/alertas_on` - Activar alertas
- `/alertas_off` - Desactivar alertas

### Ejemplo de Uso

```
1. Configura tu perfil:
   /configurar_perfil
   
2. Busca oportunidades:
   /oportunidades
   
3. Analiza una licitación:
   /analizar 1057389-2539-COT25
   
4. Obtén ayuda para cotizar:
   /ayuda_cotizar 1057389-2539-COT25
   
5. Guarda las interesantes:
   /guardar 1057389-2539-COT25
```

Ver [GUIA_BOT.md](GUIA_BOT.md) para más ejemplos y detalles.

## 🗄️ Estructura de Base de Datos

### Tablas Principales
- `licitaciones` - Información básica de licitaciones (17 campos)
- `licitaciones_detalle` - Detalles completos
- `productos_solicitados` - Productos de cada licitación
- `historial` - Historial de acciones
- `adjuntos` - Archivos adjuntos

### Tablas del Bot
- `perfiles_empresas` - Perfiles de usuarios
- `licitaciones_guardadas` - Licitaciones guardadas por usuario
- `analisis_cache` - Caché de análisis de IA
- `historial_interacciones` - Log de interacciones

## 🔧 Mantenimiento

### Actualizar Licitaciones

```bash
# Obtener nuevas licitaciones
python scraper.py

# Obtener detalles de las nuevas
python obtener_detalles.py
```

### Programar Actualizaciones Automáticas

**Windows (Task Scheduler):**
```bash
# Ejecutar scraper.py diariamente a las 8:00 AM
```

0 8 * * * cd /ruta/al/proyecto && python scraper.py
0 9 * * * cd /ruta/al/proyecto && python obtener_detalles.py
```

### Importación de Datos Históricos (Big Data)

Para potenciar el análisis de competencia, puedes importar el historial de licitaciones (aprox. 1GB/mes).

**Características:**
*   Descarga y procesa archivos ZIP mensuales.
*   **Seguridad:** Verifica si el mes ya fue importado para evitar duplicados.
*   **Eficiencia:** Usa streaming para no ocupar disco y `COPY` para inserción rápida.

**Ejecución Manual:**

```bash
# Importar mes actual (por defecto)
python src/importar_historico.py

# Importar URL específica
python src/importar_historico.py --url "https://.../COT_2024-12.zip"

# Forzar re-importación (si ya existen datos)
python src/importar_historico.py --force
```

> **Nota:** El script descarga el ZIP temporalmente, procesa los datos y lo elimina automáticamente. No ocupa espacio permanente en el servidor.

## 🤖 Análisis con Gemini AI

El bot utiliza Gemini 2.5 Pro para proporcionar:

### Análisis de Compatibilidad
- Score de 0-100 basado en tu perfil
- Fortalezas y debilidades
- Probabilidad de éxito

### Recomendaciones de Precio
- Rango competitivo
- Precio sugerido
- Estrategia de pricing
- Justificación basada en competencia

### Guía para Cotizar
- Checklist de documentos
- Estructura de cotización
- Consejos de presentación
- Errores a evitar
- Timeline sugerido

## 📊 API de Mercado Público

### Endpoints Utilizados

1. **Listado de licitaciones:**
   ```
   GET https://api.buscador.mercadopublico.cl/compra-agil
   ```

2. **Ficha detallada:**
   ```
   GET https://api.buscador.mercadopublico.cl/compra-agil?action=ficha&code={codigo}
   ```

3. **Historial:**
   ```
   GET https://api.buscador.mercadopublico.cl/compra-agil?action=historial&code={codigo}
   ```

### Autenticación
- Solo requiere `X-API-Key` (incluida en el código)
- No requiere token Bearer para información pública

## 🎓 Documentación Adicional

- [GUIA_BOT.md](GUIA_BOT.md) - Guía de uso del bot con ejemplos
- [CAMBIOS.md](CAMBIOS.md) - Historial de cambios
- [implementation_plan.md](implementation_plan.md) - Plan de implementación

## 🔐 Seguridad

- Las API keys se almacenan en `.env` (no incluido en git)
- Los datos de usuarios se almacenan localmente en SQLite
- No se comparte información con terceros

## 📝 Licencia

Este proyecto es de código abierto para uso educativo y comercial.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📞 Soporte

Para problemas o preguntas:
1. Revisa [GUIA_BOT.md](GUIA_BOT.md)
2. Verifica los logs del bot
3. Abre un issue en GitHub

---

**Desarrollado con ❤️ para ayudar a PYMEs chilenas a acceder a licitaciones públicas**
## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request.

## ⚠️ Disclaimer

Este proyecto es solo para fines educativos. Asegúrate de cumplir con los términos de servicio de Mercado Público al usar su API.

## 📝 Licencia

MIT
