# 🚀 Guía de Deployment - Tu Cluster Kubernetes en Vultr

## Estado Actual de tu Cluster

```
✅ Kubernetes v1.30.14
✅ Calico CNI
✅ Prometheus + Grafana (namespace: monitoring)
✅ Namespace "apps" creado
✅ Demo nginx funcionando
```

---

## 📋 Paso 1: Clonar Repositorio en el VPS

```bash
# SSH a tu VPS
ssh root@TU_IP_VULTR

# Clonar repo
cd /home/vultr
git clone https://github.com/gerardbourguett/bot-compra-agil.git
cd bot-compra-agil
```

---

## 📋 Paso 2: Crear Secrets en Kubernetes

```bash
# Usando tus GitHub Secrets
kubectl create secret generic compraagil-secrets \
  -n apps \
  --from-literal=DATABASE_URL="postgresql://compra_agil_user:CompraAgil2024!Secure@64.176.19.51:5433/compra_agil" \
  --from-literal=GEMINI_API_KEY="TU_GEMINI_KEY" \
  --from-literal=TELEGRAM_TOKEN="TU_TELEGRAM_TOKEN"

# Verificar
kubectl get secret compraagil-secrets -n apps
```

---

## 📋 Paso 3: Aplicar Manifiestos

```bash
cd /home/vultr/bot-compra-agil

# 1. ConfigMap
kubectl apply -f k8s/configmap.yaml

# 2. Redis
kubectl apply -f k8s/redis.yaml

# 3. API Deployment
kubectl apply -f k8s/deployment.yaml

# 4. Service
kubectl apply -f k8s/service.yaml

# Ver todo
kubectl get all -n apps
```

---

## 📋 Paso 4: Verificar Deployment

```bash
# Ver pods
kubectl get pods -n apps -w

# Ver logs
kubectl logs -f deployment/compraagil-api -n apps

# Health check
kubectl exec -it $(kubectl get pod -n apps -l app=compraagil-api -o jsonpath='{.items[0].metadata.name}') -- curl http://localhost:8000/health
```

---

## 📋 Paso 5: Abrir Puerto en Firewall

```bash
# El servicio está en NodePort 30800
sudo ufw allow 30800/tcp
sudo ufw reload

# Ver servicio
kubectl get svc -n apps compraagil-api
```

---

## 🌐 Acceder a la API

```bash
# Desde fuera del cluster
curl http://TU_IP_VULTR:30800/health

# Docs de la API
http://TU_IP_VULTR:30800/api/docs
```

---

## 🔧 Comandos Para Tu Cluster

### Ver recursos en namespace apps

```bash
kubectl get all -n apps
kubectl get pods -n apps
kubectl get svc -n apps
```

### Logs de la API

```bash
# Logs de deployment
kubectl logs -f deployment/compraagil-api -n apps

# Logs de un pod específico
kubectl logs -f POD_NAME -n apps

# Logs de todos los pods
kubectl logs -l app=compraagil-api -n apps --all-containers=true -f
```

### Ejecutar comandos en pods

```bash
# Shell en un pod
kubectl exec -it POD_NAME -n apps -- /bin/bash

# Health check
kubectl exec -it POD_NAME -n apps -- curl http://localhost:8000/health

# Ver env vars
kubectl exec -it POD_NAME -n apps -- env | grep DATABASE
```

### Update deployment

```bash
cd /home/vultr/bot-compra-agil

# Pull código nuevo
git pull origin main

# Restart deployment (force rolling update)
kubectl rollout restart deployment/compraagil-api -n apps

# Ver status
kubectl rollout status deployment/compraagil-api -n apps

# Ver historial
kubectl rollout history deployment/compraagil-api -n apps
```

### Scaling

```bash
# Escalar a 3 réplicas
kubectl scale deployment/compraagil-api --replicas=3 -n apps

# Ver réplicas
kubectl get deployment compraagil-api -n apps
```

---

## 📊 Monitoreo con Prometheus + Grafana

Tu Grafana ya está accesible en:
```
http://TU_IP_VULTR:32000
Usuario: admin
Password: keYSQMLcGtyaEH5o43iXEUbdv1K07Nk8YoZWD3Mt
```

### Añadir métricas de la API a Prometheus

Crea archivo `k8s/servicemonitor.yaml`:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: compraagil-api-metrics
  namespace: apps
  labels:
    release: prometheus-stack
spec:
  selector:
    matchLabels:
      app: compraagil-api
  endpoints:
  - port: http
    path: /metrics  # Si tu API exporta métricas
    interval: 30s
```

Aplicar:
```bash
kubectl apply -f k8s/servicemonitor.yaml
```

---

## 🚀 GitHub Actions - Deployment Automático

El workflow ya está configurado pero necesitas ajustar:

1. **Crear secret para Docker Registry**:
```bash
# En tu VPS
kubectl create secret docker-registry ghcr-secret \
  -n apps \
  --docker-server=ghcr.io \
  --docker-username=gerardbourguett \
  --docker-password=TU_GITHUB_TOKEN \
  --docker-email=tu@email.com
```

2. **Añadir el secret al deployment**:

Edita `k8s/deployment.yaml` y añade:
```yaml
spec:
  template:
    spec:
      imagePullSecrets:
      - name: ghcr-secret
      containers:
      - name: api
        ...
```

3. **Push a main** → Auto-deploy!

---

## 🐛 Troubleshooting

### Pods en CrashLoopBackOff

```bash
# Ver logs del pod que falla
kubectl logs POD_NAME -n apps

# Ver eventos
kubectl describe pod POD_NAME -n apps

# Ver eventos del deployment
kubectl describe deployment compraagil-api -n apps
```

### Imagen no se puede pull

```bash
# Verificar el imagePullSecret
kubectl get secret ghcr-secret -n apps

# Ver eventos de pull
kubectl get events -n apps --sort-by='.lastTimestamp' | grep -i pull
```

### Database connection error

```bash
# Verificar secret
kubectl get secret compraagil-secrets -n apps -o yaml

# Ver env en pod
kubectl exec -it POD_NAME -n apps -- env | grep DATABASE_URL

# Test conexión desde pod
kubectl exec -it POD_NAME -n apps -- curl -v telnet://64.176.19.51:5433
```

---

## 📝 Script de Deployment Rápido

Crea `/home/vultr/deploy-api.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Deploying CompraÁgil API..."

cd /home/vultr/bot-compra-agil

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Apply manifests
echo "📦 Applying Kubernetes manifests..."
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Restart deployment
echo "🔄 Restarting deployment..."
kubectl rollout restart deployment/compraagil-api -n apps

# Wait for rollout
echo "⏳ Waiting for rollout..."
kubectl rollout status deployment/compraagil-api -n apps --timeout=5m

# Health check
echo "🏥 Health check..."
sleep 10
POD=$(kubectl get pod -n apps -l app=compraagil-api -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it $POD -n apps -- curl -f http://localhost:8000/health || exit 1

echo "✅ Deployment successful!"
kubectl get pods -n apps -l app=compraagil-api
```

Hacer ejecutable:
```bash
chmod +x /home/vultr/deploy-api.sh
```

Usar:
```bash
/home/vultr/deploy-api.sh
```

---

## ✅ Checklist de Deployment

- [ ] Repositorio clonado en `/home/vultr/bot-compra-agil`
- [ ] Secret `compraagil-secrets` creado en namespace `apps`
- [ ] ConfigMap aplicado
- [ ] Redis deployment aplicado y corriendo
- [ ] API deployment aplicado y corriendo
- [ ] Service creado (NodePort 30800)
- [ ] Puerto 30800 abierto en firewall
- [ ] Health endpoint responde desde fuera: `curl http://IP:30800/health`
- [ ] Logs visibles: `kubectl logs -f deployment/compraagil-api -n apps`
- [ ] GitHub Actions configurado y funcionando

---

**Tu API estará disponible en**: `http://TU_IP_VULTR:30800`

**Docs**: `http://TU_IP_VULTR:30800/api/docs`
