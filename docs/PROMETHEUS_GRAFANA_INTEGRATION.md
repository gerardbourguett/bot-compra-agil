# Integración con Prometheus y Grafana Existentes

Esta guía te ayudará a integrar el sistema de métricas de CompraAgil con tus instancias existentes de Prometheus y Grafana.

## 📋 Resumen

Ya tienes Prometheus y Grafana corriendo en tu servidor. Solo necesitas:
1. **Prometheus**: Agregar configuración para scrapear bot y scraper
2. **Grafana**: Importar los 3 dashboards pre-construidos

---

## 🔧 1. Configurar Prometheus

### Ubicar tu archivo de configuración

Primero, encuentra dónde está tu `prometheus.yml`:

```bash
# Opción 1: Si Prometheus está en Docker
docker inspect prometheus | grep -A 5 "Mounts"

# Opción 2: Si Prometheus está como servicio systemd
sudo systemctl status prometheus
# Busca la línea --config.file

# Opción 3: Buscar en el sistema
sudo find / -name prometheus.yml 2>/dev/null
```

Ubicaciones comunes:
- `/etc/prometheus/prometheus.yml`
- `/opt/prometheus/prometheus.yml`
- `~/prometheus/prometheus.yml`

---

### Agregar jobs de scraping

Abre tu `prometheus.yml` y agrega estos dos jobs al final de `scrape_configs`:

```yaml
scrape_configs:
  # ... tus jobs existentes ...

  # ========== CompraAgil Bot ==========
  - job_name: 'compraagil-bot'
    static_configs:
      - targets: ['localhost:8001']  # O la IP de tu servidor
        labels:
          service: 'bot'
          tier: 'application'
          app: 'compraagil'
    metrics_path: '/metrics'
    scrape_interval: 10s
    scrape_timeout: 5s

  # ========== CompraAgil Scraper ==========
  - job_name: 'compraagil-scraper'
    static_configs:
      - targets: ['localhost:8002']  # O la IP de tu servidor
        labels:
          service: 'scraper'
          tier: 'application'
          app: 'compraagil'
    metrics_path: '/metrics'
    scrape_interval: 30s
    scrape_timeout: 10s
```

**Nota importante**: Si Prometheus está en Docker y los contenedores están en la misma red:
```yaml
      - targets: ['compra_agil_bot:8000']  # Puerto interno
      - targets: ['compra_agil_scraper:8000']  # Puerto interno
```

---

### Agregar reglas de alerting (opcional)

Si quieres las alertas automáticas:

1. **Copia el archivo de alertas**:
```bash
sudo cp monitoring/prometheus/alerts.yml /etc/prometheus/alerts.yml
```

2. **Edita tu prometheus.yml** para cargar las reglas:
```yaml
# En la sección global de prometheus.yml
rule_files:
  - 'alerts.yml'
  # - tus otras reglas...
```

---

### Recargar configuración de Prometheus

**Opción 1**: Reload sin downtime (recomendado)
```bash
# Si Prometheus tiene API habilitada
curl -X POST http://localhost:9090/-/reload

# O enviar señal
kill -HUP $(pidof prometheus)

# Si está en Docker
docker exec -it prometheus kill -HUP 1
```

**Opción 2**: Restart completo
```bash
# Systemd
sudo systemctl restart prometheus

# Docker
docker restart prometheus
```

---

### Verificar que funciona

1. **Targets en Prometheus**: http://tu-servidor:9090/targets
   - Deberías ver `compraagil-bot` y `compraagil-scraper` con estado **UP**
   - Si están DOWN, revisa:
     - ¿Los contenedores están corriendo? `docker ps | grep compra_agil`
     - ¿Los puertos están accesibles? `curl http://localhost:8001/metrics`

2. **Métricas disponibles**: http://tu-servidor:9090/graph
   - Busca `compra_agil_` en el query builder
   - Deberías ver 45+ métricas disponibles

---

## 📊 2. Importar Dashboards en Grafana

### Método 1: Importar manualmente (recomendado)

1. **Accede a Grafana**: http://tu-servidor:3000

2. **Importar cada dashboard**:
   - Click en **+** → **Import**
   - Click en **Upload JSON file**
   - Selecciona uno de estos archivos:
     - `monitoring/grafana/dashboards/business-metrics.json`
     - `monitoring/grafana/dashboards/technical-performance.json`
     - `monitoring/grafana/dashboards/saas-metrics.json`
   - En "Folder", selecciona o crea una carpeta "CompraAgil"
   - En "Prometheus", selecciona tu datasource de Prometheus
   - Click **Import**

3. **Repetir para los 3 dashboards**

---

### Método 2: Provisioning automático (avanzado)

Si tu Grafana soporta provisioning:

1. **Copia los archivos de provisioning**:
```bash
# Dashboards
sudo cp -r monitoring/grafana/dashboards/*.json /etc/grafana/dashboards/

# Provisioning config
sudo cp monitoring/grafana/provisioning/dashboards/dashboards.yml /etc/grafana/provisioning/dashboards/compraagil.yml
```

2. **Edita el archivo de provisioning** si es necesario:
```bash
sudo nano /etc/grafana/provisioning/dashboards/compraagil.yml
```

Ajusta la ruta si es diferente:
```yaml
options:
  path: /etc/grafana/dashboards  # Ajusta según tu instalación
```

3. **Restart Grafana**:
```bash
sudo systemctl restart grafana-server
# O
docker restart grafana
```

---

### Verificar dashboards

1. En Grafana, ve a **Dashboards** → **Browse**
2. Deberías ver la carpeta **CompraAgil** con 3 dashboards:
   - CompraAgil - Business Metrics
   - CompraAgil - Technical Performance
   - CompraAgil - SaaS Metrics & Revenue

3. Abre cada uno y verifica que los paneles muestran datos

---

## 🔍 3. Verificar que todo funciona

### Test 1: Métricas del Bot

```bash
# Debería mostrar métricas en formato Prometheus
curl http://localhost:8001/metrics

# Buscar métricas específicas
curl http://localhost:8001/metrics | grep compra_agil_active_users
```

### Test 2: Métricas del Scraper

```bash
curl http://localhost:8002/metrics | grep compra_agil_licitaciones
```

### Test 3: Prometheus está scrapeando

```bash
# Query via API de Prometheus
curl 'http://localhost:9090/api/v1/query?query=compra_agil_active_users'

# Deberías ver algo como:
# {"status":"success","data":{"resultType":"vector","result":[{"metric":{...},"value":[1735428000,"15"]}]}}
```

### Test 4: Grafana puede consultar

1. En Grafana → Explore
2. Selecciona datasource Prometheus
3. Query: `compra_agil_active_users`
4. Deberías ver un gráfico con datos

---

## 🚨 Troubleshooting

### Prometheus no puede scrapear (targets DOWN)

**Síntoma**: Targets muestran "Connection refused"

**Soluciones**:
1. **Verifica que los servicios estén corriendo**:
   ```bash
   docker ps | grep compra_agil
   ```

2. **Verifica que metrics_server esté iniciado**:
   ```bash
   docker logs compra_agil_bot | grep "Metrics server"
   docker logs compra_agil_scraper | grep "Metrics server"
   ```

3. **Verifica conectividad**:
   ```bash
   curl http://localhost:8001/health
   curl http://localhost:8001/metrics
   ```

4. **Revisa firewall**:
   ```bash
   sudo ufw status
   # Si está bloqueado:
   sudo ufw allow 8001/tcp
   sudo ufw allow 8002/tcp
   ```

---

### Dashboards no muestran datos

**Síntoma**: Paneles dicen "No data"

**Soluciones**:
1. **Verifica datasource en Grafana**:
   - Settings → Data Sources → Prometheus
   - Test connection debe ser exitoso
   - URL debe ser correcta (ejemplo: `http://localhost:9090`)

2. **Verifica que Prometheus tiene datos**:
   - Ve a Prometheus: http://localhost:9090/graph
   - Query: `compra_agil_active_users`
   - Si no hay datos, el problema es el scraping

3. **Revisa el time range en Grafana**:
   - Algunos paneles buscan datos de "Last 6 hours"
   - Si recién iniciaste, cambia a "Last 5 minutes"

---

### Métricas aparecen pero con valores en 0

**Síntoma**: Métricas existen pero todos los valores son 0

**Causa**: Las métricas se crean en el startup pero no se están actualizando

**Solución**: Verifica que el bot/scraper estén procesando actividad:
```bash
# Ver logs del bot
docker logs -f compra_agil_bot

# Deberías ver mensajes como:
# "📊 Cache HIT: ..."
# "🔄 Cache MISS: ..."
# "📦 Guardado en cache: ..."
```

---

## 📝 Configuración de Alertmanager (opcional)

Si quieres recibir notificaciones de las alertas:

### 1. Instalar Alertmanager

```bash
# Docker
docker run -d \
  --name alertmanager \
  -p 9093:9093 \
  -v ~/alertmanager:/etc/alertmanager \
  prom/alertmanager:latest
```

### 2. Configurar Alertmanager

Crea `~/alertmanager/alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'telegram'  # O 'email', 'slack', etc.

receivers:
  - name: 'telegram'
    telegram_configs:
      - bot_token: 'TU_BOT_TOKEN'
        chat_id: TU_CHAT_ID
        parse_mode: 'Markdown'
        message: |
          🚨 *{{ .GroupLabels.alertname }}*

          *Severity:* {{ .CommonLabels.severity }}
          *Summary:* {{ .CommonAnnotations.summary }}
          *Description:* {{ .CommonAnnotations.description }}
```

### 3. Conectar Prometheus con Alertmanager

En tu `prometheus.yml`:

```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - 'localhost:9093'
```

---

## 📚 Recursos adicionales

- **Prometheus**: https://prometheus.io/docs/
- **Grafana**: https://grafana.com/docs/
- **Alertmanager**: https://prometheus.io/docs/alerting/latest/alertmanager/

---

## ✅ Checklist final

Usa esta checklist para verificar que todo está configurado:

- [ ] Bot expone métricas en `:8001/metrics`
- [ ] Scraper expone métricas en `:8002/metrics`
- [ ] Prometheus scrapea bot y scraper (targets UP)
- [ ] Prometheus puede hacer queries de métricas `compra_agil_*`
- [ ] Grafana tiene datasource Prometheus configurado
- [ ] 3 dashboards importados en Grafana
- [ ] Dashboards muestran datos reales (no "No data")
- [ ] Alertas configuradas en Prometheus (opcional)
- [ ] Alertmanager recibe y envía notificaciones (opcional)

---

**Última actualización**: 2025-12-28
