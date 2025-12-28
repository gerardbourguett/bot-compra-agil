# Configuración de Uptime Kuma para CompraAgil

Este documento detalla los monitores que debes configurar en Uptime Kuma para supervisar la disponibilidad y salud de CompraAgil.

## 📋 Índice

1. [Instalación de Uptime Kuma](#instalación-de-uptime-kuma)
2. [Monitores Críticos](#monitores-críticos)
3. [Monitores de Aplicación](#monitores-de-aplicación)
4. [Monitores de Infraestructura](#monitores-de-infraestructura)
5. [Configuración de Notificaciones](#configuración-de-notticaciones)
6. [Grupos de Monitores](#grupos-de-monitores)

---

## Instalación de Uptime Kuma

Si aún no tienes Uptime Kuma instalado, puedes agregarlo a tu `docker-compose.yml`:

```yaml
  uptime-kuma:
    image: louislam/uptime-kuma:1
    container_name: compra_agil_uptime_kuma
    restart: unless-stopped
    ports:
      - "3001:3001"
    volumes:
      - uptime_kuma_data:/app/data
    networks:
      - default
```

Y agregar el volumen:

```yaml
  uptime_kuma_data:
    driver: local
    name: compra_agil_uptime_kuma_data
```

Luego acceder a `http://tu-servidor:3001` para configurar.

---

## Monitores Críticos

### 1. PostgreSQL Database
- **Tipo**: HTTP(s) - Keyword
- **URL**: `http://localhost:9090/api/v1/query?query=up{job="postgresql"}`
- **Método**: GET
- **Keyword**: `"success"`
- **Intervalo**: 60 segundos
- **Reintentos**: 3
- **Heartbeat Interval**: 60s
- **Grupo**: Infraestructura

**Descripción**: Verifica que PostgreSQL esté respondiendo a través de Prometheus.

---

### 2. Redis Cache
- **Tipo**: HTTP(s) - Keyword
- **URL**: `http://localhost:9090/api/v1/query?query=compra_agil_redis_conexiones_activas`
- **Método**: GET
- **Keyword**: `"success"`
- **Intervalo**: 60 segundos
- **Grupo**: Infraestructura

**Descripción**: Verifica que Redis tenga conexiones activas.

---

### 3. Bot de Telegram
- **Tipo**: HTTP(s)
- **URL**: `http://localhost:8001/health`
- **Método**: GET
- **Código de estado esperado**: 200
- **Intervalo**: 30 segundos
- **Reintentos**: 2
- **Grupo**: Aplicación

**Descripción**: Healthcheck del bot de Telegram (puerto 8001).

---

### 4. Scraper
- **Tipo**: HTTP(s)
- **URL**: `http://localhost:8002/health`
- **Método**: GET
- **Código de estado esperado**: 200
- **Intervalo**: 60 segundos
- **Grupo**: Aplicación

**Descripción**: Healthcheck del scraper (puerto 8002).

---

### 5. Prometheus
- **Tipo**: HTTP(s)
- **URL**: `http://localhost:9090/-/healthy`
- **Método**: GET
- **Código de estado esperado**: 200
- **Intervalo**: 60 segundos
- **Grupo**: Monitoring

**Descripción**: Verifica que Prometheus esté operativo.

---

### 6. Grafana
- **Tipo**: HTTP(s)
- **URL**: `http://localhost:3000/api/health`
- **Método**: GET
- **Código de estado esperado**: 200
- **Intervalo**: 60 segundos
- **Grupo**: Monitoring

**Descripción**: Verifica que Grafana esté respondiendo.

---

## Monitores de Aplicación

### 7. Licitaciones Activas
- **Tipo**: HTTP(s) - Keyword
- **URL**: `http://localhost:9090/api/v1/query?query=compra_agil_licitaciones_activas`
- **Método**: GET
- **Keyword**: `"value":[`
- **Intervalo**: 300 segundos (5 min)
- **Grupo**: Business Metrics

**Descripción**: Verifica que haya licitaciones activas en la BD.

---

### 8. Usuarios Activos
- **Tipo**: HTTP(s) - Keyword
- **URL**: `http://localhost:9090/api/v1/query?query=compra_agil_active_users`
- **Método**: GET
- **Keyword**: `"success"`
- **Intervalo**: 300 segundos
- **Grupo**: Business Metrics

**Descripción**: Monitorea usuarios activos en las últimas 24h.

---

### 9. Error Rate Bajo
- **Tipo**: HTTP(s) - Keyword
- **URL**: `http://localhost:9090/api/v1/query?query=rate(compra_agil_errors_total[5m])`
- **Método**: GET
- **Keyword**: `"success"`
- **Intervalo**: 120 segundos
- **Grupo**: Health

**Descripción**: Monitorea la tasa de errores general.

---

## Monitores de Infraestructura

### 10. CPU Usage
- **Tipo**: HTTP(s) - JSON Query
- **URL**: `http://localhost:9090/api/v1/query?query=compra_agil_cpu_uso_percent`
- **Método**: GET
- **JSON Path**: `$.data.result[0].value[1]`
- **Condición**: `< 90` (alerta si CPU > 90%)
- **Intervalo**: 60 segundos
- **Grupo**: System Resources

**Descripción**: Monitorea uso de CPU del proceso.

---

### 11. Memory Usage
- **Tipo**: HTTP(s) - JSON Query
- **URL**: `http://localhost:9090/api/v1/query?query=compra_agil_memoria_uso_bytes{tipo="percent"}`
- **Método**: GET
- **JSON Path**: `$.data.result[0].value[1]`
- **Condición**: `< 85`
- **Intervalo**: 60 segundos
- **Grupo**: System Resources

**Descripción**: Monitorea uso de memoria.

---

### 12. Disk Space (Host)
- **Tipo**: HTTP(s) - JSON Query
- **URL**: `http://localhost:9090/api/v1/query?query=node_filesystem_avail_bytes{mountpoint="/"}/node_filesystem_size_bytes{mountpoint="/"}`
- **Método**: GET
- **JSON Path**: `$.data.result[0].value[1]`
- **Condición**: `> 0.10` (alerta si < 10% libre)
- **Intervalo**: 300 segundos
- **Grupo**: System Resources

**Descripción**: Verifica espacio libre en disco (requiere node-exporter).

---

## Monitores de Performance

### 13. ML Latency (p95)
- **Tipo**: HTTP(s) - JSON Query
- **URL**: `http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,rate(compra_agil_ml_duration_seconds_bucket[5m]))`
- **Método**: GET
- **JSON Path**: `$.data.result[0].value[1]`
- **Condición**: `< 30` (alerta si p95 > 30s)
- **Intervalo**: 120 segundos
- **Grupo**: Performance

**Descripción**: Monitorea latencia ML (percentil 95).

---

### 14. Cache Hit Rate
- **Tipo**: HTTP(s) - JSON Query
- **URL**: `http://localhost:9090/api/v1/query?query=rate(compra_agil_cache_operations_total{result="hit"}[5m])/(rate(compra_agil_cache_operations_total{result="hit"}[5m])+rate(compra_agil_cache_operations_total{result="miss"}[5m]))*100`
- **Método**: GET
- **JSON Path**: `$.data.result[0].value[1]`
- **Condición**: `> 50` (alerta si hit rate < 50%)
- **Intervalo**: 120 segundos
- **Grupo**: Performance

**Descripción**: Monitorea eficiencia del caché Redis.

---

## Monitores de SaaS

### 15. Revenue Mensual (MRR)
- **Tipo**: HTTP(s) - JSON Query
- **URL**: `http://localhost:9090/api/v1/query?query=sum(compra_agil_revenue_mensual_clp)`
- **Método**: GET
- **JSON Path**: `$.data.result[0].value[1]`
- **Intervalo**: 3600 segundos (1 hora)
- **Grupo**: Business Metrics

**Descripción**: Trackea el Monthly Recurring Revenue.

---

### 16. Suscripciones Pagadas
- **Tipo**: HTTP(s) - JSON Query
- **URL**: `http://localhost:9090/api/v1/query?query=sum(compra_agil_subscriptions{tier!="free"})`
- **Método**: GET
- **JSON Path**: `$.data.result[0].value[1]`
- **Intervalo**: 3600 segundos
- **Grupo**: Business Metrics

**Descripción**: Cuenta suscripciones de pago activas.

---

## Configuración de Notificaciones

Configura al menos una de estas opciones de notificación:

### Opción 1: Telegram
1. Ve a Settings → Notifications
2. Crea un nuevo "Notification"
3. Selecciona "Telegram"
4. Ingresa tu **Bot Token** y **Chat ID**
5. Prueba la notificación

**Cómo obtener Chat ID**:
- Envía un mensaje a tu bot
- Visita: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
- Busca `"chat":{"id":12345678}}`

---

### Opción 2: Email (SMTP)
1. Settings → Notifications
2. Tipo: SMTP
3. Configura:
   - **SMTP Host**: smtp.gmail.com (para Gmail)
   - **Puerto**: 587
   - **Seguridad**: TLS
   - **Usuario**: tu-email@gmail.com
   - **Contraseña**: App Password (no tu contraseña real)
   - **De**: tu-email@gmail.com
   - **Para**: tu-email-destino@gmail.com

---

### Opción 3: Webhook (para integrar con Slack, Discord, etc.)
1. Settings → Notifications
2. Tipo: Webhook
3. **URL**: Tu webhook URL
4. **Método**: POST
5. **Headers** (opcional):
   ```json
   {
     "Content-Type": "application/json"
   }
   ```

---

## Grupos de Monitores

Organiza tus monitores en estos grupos para mejor visibilidad:

1. **Infraestructura**: PostgreSQL, Redis
2. **Aplicación**: Bot, Scraper, API
3. **Monitoring**: Prometheus, Grafana
4. **Business Metrics**: Licitaciones, Usuarios, Revenue
5. **Performance**: ML Latency, Cache Hit Rate, DB Queries
6. **System Resources**: CPU, Memory, Disk

---

## Status Page Pública (Opcional)

Uptime Kuma permite crear una página de status pública:

1. Ve a "Status Pages"
2. Crea una nueva Status Page
3. Selecciona los monitores que quieres mostrar públicamente
4. Personaliza el título, descripción y tema
5. Comparte la URL con tus usuarios

**Recomendación**: Solo incluir monitores de alto nivel (Bot, API, Database) sin exponer métricas internas.

---

## Configuración Recomendada de Intervalos

| Tipo de Monitor | Intervalo Recomendado |
|------------------|-----------------------|
| Críticos (DB, Bot) | 30-60 segundos |
| Aplicación | 60-120 segundos |
| Performance | 120-300 segundos |
| Business Metrics | 300-3600 segundos |
| System Resources | 60-120 segundos |

---

## Mantenimiento

### Backups de Uptime Kuma
El volumen `uptime_kuma_data` contiene toda la configuración. Crea backups periódicos:

```bash
docker run --rm \
  -v compra_agil_uptime_kuma_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/uptime-kuma-$(date +%Y%m%d).tar.gz /data
```

### Actualización
```bash
docker compose pull uptime-kuma
docker compose up -d uptime-kuma
```

---

## Troubleshooting

### Los monitores HTTP fallan con "getaddrinfo EAI_AGAIN"
- **Causa**: Uptime Kuma no puede resolver `localhost`
- **Solución**: Usa la IP del host o el nombre del contenedor en la red Docker
- **Ejemplo**: `http://compra_agil_prometheus:9090` en lugar de `http://localhost:9090`

### Métricas de Prometheus no se actualizan
- Verifica que Prometheus esté scrapeando correctamente: `http://localhost:9090/targets`
- Revisa que bot y scraper tengan el servidor de métricas iniciado

### Notificaciones no llegan
- Prueba la notificación desde Settings → Notifications
- Revisa los logs de Uptime Kuma: `docker logs compra_agil_uptime_kuma`

---

## Recursos Adicionales

- [Documentación oficial de Uptime Kuma](https://github.com/louislam/uptime-kuma)
- [Lista completa de tipos de notificaciones](https://github.com/louislam/uptime-kuma/wiki/Notification-Types)
- [API de Prometheus](https://prometheus.io/docs/prometheus/latest/querying/api/)

---

**Última actualización**: 2025-12-28
