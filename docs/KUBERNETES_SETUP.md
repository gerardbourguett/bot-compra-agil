# 🚀 Kubernetes Deployment Guide - CompraÁgil API v3

## Archivos Creados

```
k8s/
├── deployment.yaml    # Deployment con 3 réplicas
├── service.yaml       # Service ClusterIP
├── ingress.yaml       # Ingress con SSL
├── configmap.yaml     # Variables no sensibles
├── secrets.yaml       # Variables sensibles (template)
└── redis.yaml         # Redis deployment
```

---

## 📋 Paso 1: Instalar Kubernetes en Vultr VPS

### Opción A: K3s (Recomendado - Ligero)

```bash
# SSH a tu VPS
ssh VPS_USER@VPS_HOST

# Instalar K3s
curl -sfL https://get.k3s.io | sh -

# Verificar instalación
sudo k3s kubectl get nodes

# Copiar kubeconfig
mkdir -p ~/.kube
sudo cat /etc/rancher/k3s/k3s.yaml > ~/.kube/config
sudo chown $USER:$USER ~/.kube/config

# Alias para kubectl
echo "alias kubectl='sudo k3s kubectl'" >> ~/.bashrc
source ~/.bashrc
```

### Opción B: MicroK8s

```bash
sudo snap install microk8s --classic
sudo microk8s enable dns storage ingress
sudo microk8s kubectl get nodes
```

---

## 📋 Paso 2: Instalar Nginx Ingress Controller

```bash
# Para K3s
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# Verificar
kubectl get pods -n ingress-nginx
```

---

## 📋 Paso 3: Instalar cert-manager (SSL Automático)

```bash
# Instalar cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Crear ClusterIssuer para Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: tu-email@ejemplo.com  # Cambia esto
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

---

## 📋 Paso 4: Configurar GitHub Container Registry

### 1. Clonar repo en el VPS

```bash
cd ~
git clone https://github.com/TU-USUARIO/bot-compra-agil.git
cd bot-compra-agil
```

### 2. Actualizar manifiestos

Edita `k8s/deployment.yaml`:
```yaml
image: ghcr.io/TU-USUARIO/bot-compra-agil:latest
```

Edita `k8s/ingress.yaml`:
```yaml
- host: api.tudominio.com  # Tu dominio real
```

### 3. Crear secreto para pull de imágenes (si tu repo es privado)

```bash
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=TU-USUARIO \
  --docker-password=TU_GITHUB_TOKEN \
  --docker-email=TU-EMAIL
```

---

## 📋 Paso 5: Desplegar la Aplicación

### 1. Crear secrets desde tus GitHub Secrets

```bash
kubectl create secret generic compraagil-secrets \
  --from-literal=DATABASE_URL="postgresql://..." \
  --from-literal=GEMINI_API_KEY="tu_key" \
  --from-literal=TELEGRAM_TOKEN="tu_token"
```

### 2. Aplicar todos los manifiestos

```bash
cd ~/bot-compra-agil

# ConfigMap
kubectl apply -f k8s/configmap.yaml

# Redis
kubectl apply -f k8s/redis.yaml

# API Deployment
kubectl apply -f k8s/deployment.yaml

# Service
kubectl apply -f k8s/service.yaml

# Ingress
kubectl apply -f k8s/ingress.yaml
```

### 3. Verificar deployment

```bash
# Ver pods
kubectl get pods

# Ver deployment status
kubectl rollout status deployment/compraagil-api

# Ver logs
kubectl logs -f deployment/compraagil-api

# Ver todos los recursos
kubectl get all
```

---

## 📋 Paso 6: Configurar DNS

Apunta tu dominio a la IP de tu VPS:

```
A Record: api.tudominio.com → TU_IP_VPS
```

---

## 🔧 Comandos Útiles de Kubectl

### Ver recursos

```bash
# Pods
kubectl get pods
kubectl get pods -o wide  # Con más info

# Deployments
kubectl get deployments

# Services
kubectl get services

# Ingress
kubectl get ingress

# Logs de un pod
kubectl logs POD_NAME
kubectl logs -f POD_NAME  # Follow

# Logs de deployment
kubectl logs -f deployment/compraagil-api
```

### Ejecutar comandos en pods

```bash
# Abrir shell en un pod
kubectl exec -it POD_NAME -- /bin/bash

# Health check
kubectl exec -it POD_NAME -- curl http://localhost:8000/health

# Ver variables de entorno
kubectl exec -it POD_NAME -- env
```

### Scaling

```bash
# Escalar a 5 réplicas
kubectl scale deployment/compraagil-api --replicas=5

# Auto-scaling
kubectl autoscale deployment/compraagil-api --min=2 --max=10 --cpu-percent=80
```

### Updates

```bash
# Rolling update con nueva imagen
kubectl set image deployment/compraagil-api api=ghcr.io/TU-USUARIO/bot-compra-agil:new-tag

# Restart deployment
kubectl rollout restart deployment/compraagil-api

# Ver historial
kubectl rollout history deployment/compraagil-api

# Rollback
kubectl rollout undo deployment/compraagil-api
```

### Debugging

```bash
# Describir pod (ver eventos)
kubectl describe pod POD_NAME

# Describir deployment
kubectl describe deployment compraagil-api

# Ver eventos del cluster
kubectl get events --sort-by='.lastTimestamp'

# Port forward (para testing local)
kubectl port-forward deployment/compraagil-api 8000:8000
```

---

## 🎯 GitHub Actions - Cómo Funciona

Cuando haces `git push` a `main`:

1. **Build**: Construye imagen Docker
2. **Push**: Sube a GitHub Container Registry (ghcr.io)
3. **Test**: Ejecuta tests
4. **Deploy**: 
   - Se conecta al VPS por SSH
   - Actualiza secrets
   - Aplica manifiestos
   - Hace rolling update
   - Verifica health

**Ver deploys**: GitHub → Tu repo → Actions → "Build and Deploy to Kubernetes"

---

## 📊 Monitoreo

### Health check manual

```bash
kubectl port-forward svc/compraagil-api-service 8080:80
curl http://localhost:8080/health
```

### Ver métricas

```bash
kubectl top pods
kubectl top nodes
```

### Logs centralizados

```bash
# Logs de todas las réplicas
kubectl logs -l app=compraagil-api --all-containers=true -f
```

---

## 🔒 Seguridad

### NetworkPolicy (Opcional)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: compraagil-netpol
spec:
  podSelector:
    matchLabels:
      app: compraagil-api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: nginx-ingress
    ports:
    - protocol: TCP
      port: 8000
```

### RBAC (ya configurado por K3s)

```bash
# Ver roles
kubectl get roles
kubectl get clusterroles
```

---

## 🚨 Troubleshooting

### Pods no arrancan

```bash
# Ver detalles del pod
kubectl describe pod POD_NAME

# Ver logs
kubectl logs POD_NAME

# Eventos del deployment
kubectl describe deployment compra agil-api
```

### Imagen no se puede pull

```bash
# Verificar secret
kubectl get secret ghcr-secret

# Recrear secret
kubectl delete secret ghcr-secret
kubectl create secret docker-registry ghcr-secret ...
```

### Ingress no funciona

```bash
# Verificar ingress controller
kubectl get pods -n ingress-nginx

# Ver logs del ingress
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

### Base de datos no conecta

```bash
# Verificar secret
kubectl get secret compraagil-secrets -o yaml

# Ver variables en pod
kubectl exec -it POD_NAME -- env | grep DATABASE
```

---

## 📈 Escalabilidad

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: compraagil-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: compraagil-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

Aplicar:
```bash
kubectl apply -f k8s/hpa.yaml
kubectl get hpa
```

---

## ✅ Checklist de Deployment

Antes del primer deploy:

- [ ] K3s instalado en VPS
- [ ] Nginx Ingress Controller instalado
- [ ] cert-manager instalado (para SSL)
- [ ] DNS apuntando a VPS
- [ ] Repositorio clonado en VPS
- [ ] Manifiestos actualizados (imagen, dominio)
- [ ] Secrets creados en K8s
- [ ] GitHub Container Registry configurado
- [ ] Workflow de GitHub Actions configurado
- [ ] Primer deployment manual exitoso

Después del setup:
- [ ] Health endpoint responde
- [ ] SSL funcionando (HTTPS)
- [ ] Logs visibles
- [ ] Scaling funciona
- [ ] GitHub Actions funciona

---

## 🎯 Comandos de Deployment Rápido

```bash
# Deploy completo desde cero
cd ~/bot-compra-agil
git pull origin main
kubectl apply -f k8s/
kubectl rollout restart deployment/compraagil-api
kubectl rollout status deployment/compraagil-api

# Verificar
kubectl get pods
kubectl logs -f deployment/compraagil-api
```

---

**Siguiente paso**: Hacer setup de K3s en tu Vultr VPS y primer deploy manual! 🚀
