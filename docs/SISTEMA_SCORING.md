# Sistema de Scoring y Mejoras del Bot

## 📊 Cómo Funciona el Score de Compatibilidad

El **Score** que ves en `/oportunidades` y `/analizar` se calcula automáticamente para ayudarte a priorizar licitaciones.

### Cálculo del Score (0-100 puntos)

#### 1. **Coincidencia de Palabras Clave** (0-100 puntos base)
```
Score = (Palabras que coinciden / Total palabras en tu perfil) × 100
```

**Ejemplo:**
- Tu perfil: "mobiliario, oficina, sillas"
- Licitación: "ADQ. MOBILIARIO P/PROY. CONSTRUCCION OF. MUNICIPAL"
- Coincidencias: "mobiliario" ✅
- Score base: (1/3) × 100 = 33 puntos

#### 2. **Bonus por Baja Competencia** (+0 a +10 puntos)
- **0 proveedores cotizando**: +10 puntos (¡oportunidad única!)
- **1-2 proveedores**: +5 puntos (poca competencia)
- **3+ proveedores**: +0 puntos

#### 3. **Bonus por Monto Ideal** (+0 a +10 puntos)
- **$500k - $5M CLP**: +10 puntos (rango ideal para PYMEs)
- Fuera de rango: +0 puntos

### Interpretación del Score

| Score | Color | Significado |
|-------|-------|-------------|
| 70-100 | 🟢 | **Alta compatibilidad** - Muy recomendado participar |
| 40-69 | 🟡 | **Media compatibilidad** - Evaluar con análisis IA |
| 0-39 | 🔴 | **Baja compatibilidad** - Probablemente no es para ti |

### Ejemplo Real

**Licitación: "ADQ. MOBILIARIO P/PROY. CONSTRUCCION OF. MUNICIPAL"**
- Monto: $3,000,000 CLP
- Proveedores cotizando: 2

**Cálculo:**
1. Coincidencia palabras: 25 puntos (1 de 4 palabras)
2. Bonus competencia: +5 puntos (2 proveedores)
3. Bonus monto: +10 puntos ($3M está en rango ideal)
4. **Total: 40 puntos** 🟡

---

## ✨ Mejoras Implementadas

### 1. **Código Copiable en `/analizar`**

Ahora el mensaje de análisis incluye:
```
📋 Código: 4022-1151-COT25 (toca para copiar)
```

El código aparece en formato `<code>` que permite:
- ✅ Tocar para copiar en móvil
- ✅ Seleccionar fácilmente en desktop
- ✅ Usar directamente en otros comandos

### 2. **Explicación del Score**

Cada análisis ahora muestra:
```
🟡 Compatibilidad: 35/100
[Explicación de Gemini AI]
💡 Score basado en: palabras clave, competencia y monto
```

### 3. **Formato Mejorado**

El mensaje de análisis ahora incluye:
- 📊 Score con emoji de color
- ✅/❌ Recomendación clara
- 📝 Resumen ejecutivo de Gemini
- 💵 Precio sugerido con rango
- 📋 Código copiable
- 🔗 Enlaces a comandos relacionados

---

## 🎯 Cómo Mejorar tu Score

### 1. **Optimiza tus Palabras Clave**
```bash
/configurar_perfil
```
- Usa palabras específicas de tu rubro
- Incluye sinónimos y variaciones
- Ejemplo: "mobiliario, muebles, sillas, escritorios, oficina"

### 2. **Ajusta tu Perfil**
- **Productos/Servicios**: Sé específico
- **Palabras Clave**: Incluye términos técnicos
- **Capacidad de Entrega**: Realista para tu empresa

### 3. **Usa el Análisis IA**
```bash
/analizar [código]
```
Gemini AI te da:
- Análisis profundo de compatibilidad
- Fortalezas y debilidades específicas
- Estrategia de precio personalizada
- Consejos para ganar la licitación

---

## 📱 Comandos Útiles

### Búsqueda
- `/buscar [palabra]` - Buscar por palabra clave
- `/oportunidades` - Licitaciones compatibles con tu perfil (con Score)
- `/urgentes [días]` - Licitaciones que cierran pronto
- `/por_monto [min] [max]` - Buscar por rango de monto

### Análisis
- `/analizar [código]` - Análisis completo con IA
- `/ayuda_cotizar [código]` - Guía para preparar cotización
- `/recomendar` - Top 5 mejores oportunidades

### Gestión
- `/guardar [código]` - Guardar licitación
- `/mis_guardadas` - Ver guardadas
- `/perfil` - Ver tu perfil actual

---

## 💡 Tips

1. **Score bajo no significa "no participar"**
   - Usa `/analizar` para análisis profundo
   - Gemini puede encontrar oportunidades ocultas

2. **Actualiza tu perfil regularmente**
   - Agrega nuevas palabras clave según lo que buscas
   - Ajusta capacidades según tu crecimiento

3. **Combina comandos**
   ```bash
   /oportunidades        # Ver compatibles
   /analizar 123-456    # Analizar la mejor
   /guardar 123-456     # Guardar para seguimiento
   ```

4. **Aprovecha el análisis IA**
   - Gemini considera factores que el Score simple no puede
   - Te da estrategia de precio personalizada
   - Identifica ventajas competitivas únicas

---

## 🔄 Próximas Mejoras Planeadas

- [ ] Score dinámico que aprende de tus licitaciones ganadas
- [ ] Alertas automáticas para licitaciones con Score alto
- [ ] Comparación de múltiples licitaciones
- [ ] Historial de Scores para ver tendencias

---

**¿Preguntas sobre el Score?**
Usa `/stats` para ver estadísticas generales del sistema.
