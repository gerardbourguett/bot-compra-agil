# Guía Rápida: Bot Inteligente de Compra Ágil 🤖

## 🚀 Inicio Rápido

### 1. Configurar Variables de Entorno

Crea o edita el archivo `.env`:

```bash
TELEGRAM_TOKEN=tu_token_de_telegram_aqui
GEMINI_API_KEY=tu_api_key_de_gemini_aqui
```

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 3. Iniciar el Bot

```bash
python bot_inteligente.py
```

## 📋 Comandos Disponibles

### Perfil y Configuración
- `/start` - Bienvenida y lista de comandos
- `/configurar_perfil` - Configurar perfil de empresa (formulario guiado)
- `/perfil` - Ver tu perfil actual

### Búsqueda
- `/buscar [palabra]` - Buscar licitaciones por palabra clave
- `/oportunidades` - Licitaciones compatibles con tu perfil
- `/urgentes [días]` - Licitaciones que cierran pronto (default: 3 días)
- `/por_monto [min] [max]` - Buscar por rango de monto en CLP

### Análisis con IA 🤖
- `/analizar [código]` - Análisis completo con Gemini AI
- `/recomendar` - Top 5 licitaciones recomendadas
- `/ayuda_cotizar [código]` - Guía personalizada para cotizar

### Licitaciones Guardadas ⭐
- `/guardar [código]` - Guardar licitación para seguimiento
- `/mis_guardadas` - Ver todas las guardadas
- `/eliminar_guardada [código]` - Eliminar de guardadas

### Alertas 🔔
- `/alertas_on` - Activar notificaciones automáticas
- `/alertas_off` - Desactivar notificaciones

### Estadísticas
- `/stats` - Ver estadísticas del sistema

## 🎯 Flujo de Uso Recomendado

### Primera Vez

1. **Configura tu perfil**
   ```
   /configurar_perfil
   ```
   El bot te guiará paso a paso para configurar:
   - Nombre de empresa
   - Tipo de negocio (productos/servicios)
   - Productos o servicios que ofreces
   - Palabras clave
   - Capacidad de entrega
   - Ubicación
   - Experiencia
   - Certificaciones

2. **Busca oportunidades**
   ```
   /oportunidades
   ```
   El bot te mostrará licitaciones compatibles con tu perfil

3. **Analiza una licitación**
   ```
   /analizar 1057389-2539-COT25
   ```
   Gemini AI te dará:
   - Score de compatibilidad (0-100)
   - Recomendación de participar o no
   - Probabilidad de éxito
   - Precio sugerido
   - Análisis de competencia

4. **Obtén ayuda para cotizar**
   ```
   /ayuda_cotizar 1057389-2539-COT25
   ```
   Recibirás:
   - Checklist de documentos
   - Consejos de presentación
   - Errores a evitar
   - Timeline sugerido

5. **Guarda las interesantes**
   ```
   /guardar 1057389-2539-COT25
   ```

6. **Activa alertas**
   ```
   /alertas_on
   ```

### Uso Diario

1. **Revisa oportunidades nuevas**
   ```
   /oportunidades
   ```

2. **Revisa urgentes**
   ```
   /urgentes
   ```

3. **Revisa tus guardadas**
   ```
   /mis_guardadas
   ```

4. **Busca algo específico**
   ```
   /buscar sillas oficina
   ```

## 💡 Ejemplos de Uso

### Ejemplo 1: Empresa de Mobiliario

```
Usuario: /configurar_perfil
Bot: ¿Cuál es el nombre de tu empresa?
Usuario: Muebles del Sur Ltda.
Bot: ¿Tu empresa vende principalmente productos o servicios?
Usuario: [Selecciona "Productos"]
Bot: Describe brevemente los productos que ofreces:
Usuario: Sillas de oficina, escritorios, estanterías, mobiliario escolar
Bot: Escribe palabras clave separadas por comas:
Usuario: sillas, escritorios, mobiliario, oficina, escolar, muebles
...

Usuario: /oportunidades
Bot: 🎯 Oportunidades para Muebles del Sur Ltda.
     
     🟢 Score: 85/100
     📄 Adquisición de mobiliario escolar para liceo...
     🏢 I. Municipalidad de Punta Arenas
     💰 $1,500,000 CLP
     📅 Cierre: 2025-11-30
     🔗 /analizar 4649-79-COT25
```

### Ejemplo 2: Empresa de Servicios

```
Usuario: /buscar mantención computadores
Bot: 📋 Encontré 8 licitaciones:
     
     📄 Servicio de mantención preventiva equipos computacionales...
     🏢 Servicio de Salud Metropolitano Norte
     💰 $800,000 CLP
     📅 Cierre: 2025-11-28
     👥 Cotizando: 2 proveedores
     🔗 /analizar 2403-1813-COT25

Usuario: /analizar 2403-1813-COT25
Bot: 🤖 Análisis de Licitación
     
     🟢 Compatibilidad: 78/100
     Esta licitación coincide bien con tu perfil...
     
     ✅ Recomendación: PARTICIPAR
     📊 Probabilidad de éxito: ALTA
     
     💵 Precio sugerido: $720,000 CLP
     📈 Rango: $650,000 - $780,000
     
     🔗 Más detalles: /ayuda_cotizar 2403-1813-COT25
```

## 🔧 Solución de Problemas

### El bot no responde
- Verifica que `TELEGRAM_TOKEN` esté correctamente configurado en `.env`
- Asegúrate de que el bot esté corriendo (`python bot_inteligente.py`)

### El análisis de IA no funciona
- Verifica que `GEMINI_API_KEY` esté configurado en `.env`
- Verifica que tengas créditos disponibles en tu cuenta de Google AI

### No encuentra licitaciones
- Asegúrate de que el scraper haya ejecutado (`python scraper.py`)
- Verifica que haya datos en la base de datos (`/stats`)

### Las búsquedas no dan resultados relevantes
- Actualiza tus palabras clave en `/configurar_perfil`
- Usa palabras más generales (ej: "sillas" en vez de "sillas ergonómicas ejecutivas")

## 📊 Arquitectura del Sistema

```
Usuario (Telegram)
       ↓
bot_inteligente.py
       ↓
┌──────┴──────┬──────────┬──────────┐
│             │          │          │
gemini_ai.py  filtros.py  database_bot.py  api_client.py
│             │          │          │
└──────┬──────┴──────────┴──────────┘
       ↓
database_extended.py
       ↓
compra_agil.db (SQLite)
```

## 🎓 Tips para Mejores Resultados

1. **Perfil completo**: Mientras más detallado tu perfil, mejores recomendaciones
2. **Palabras clave precisas**: Usa términos que aparecen en las licitaciones
3. **Revisa diario**: Las licitaciones se publican constantemente
4. **Activa alertas**: No te pierdas oportunidades
5. **Guarda las interesantes**: Haz seguimiento de las que te interesan
6. **Usa el análisis de IA**: Te ahorra tiempo y te da insights valiosos

## 📞 Soporte

Si tienes problemas o sugerencias:
1. Revisa esta guía
2. Verifica los logs del bot
3. Revisa el archivo `README.md` para más detalles técnicos
