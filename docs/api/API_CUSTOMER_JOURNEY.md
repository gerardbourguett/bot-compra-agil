# 🎯 API Customer Journey - CompraÁgil

## Customer Profiles & Use Cases

### 🌱 Perfil 1: Pequeña Empresa Catering (Principiante)

**Contexto**: Primera vez en CompraÁgil, no sabe por dónde empezar.

#### Journey del Cliente

1. **Descubrimiento** → `/api/v1/starter/oportunidades`
   ```json
   GET /api/v1/starter/oportunidades?categoria=catering&presupuesto_max=5000000
   
   Response:
   {
     "nivel": "starter",
     "mensaje_bienvenida": "¡Encontramos 12 oportunidades para tu negocio de catering!",
     "oportunidades": [
       {
         "codigo": "1234-56-LQ23",
         "titulo_simple": "Servicio de alimentación para hospital",
         "organismo": "Hospital Regional",
         "monto": 3500000,
         "dificultad": "Fácil",  // ⭐ NUEVO: nivel de dificultad
         "razon_recomendacion": "Presupuesto accesible y sin requisitos complejos",
         "plazo_cierre_dias": 15,
         "competidores_estimados": 5,
         "probabilidad_texto": "Alta - Similar a tu capacidad",
         "siguiente_paso": "Ver detalles y guía de cómo postular"
       }
     ],
     "consejos": [
       "💡 Empieza con licitaciones pequeñas para ganar experiencia",
       "📝 Revisa bien los requisitos antes de postular",
       "💰 No ofertes muy bajo, usa nuestro recomendador de precio"
     ]
   }
   ```

2. **Aprender Precio** → `/api/v1/starter/precio-guia`
   ```json
   POST /api/v1/starter/precio-guia
   Body: {
     "producto": "servicio catering almuerzo",
     "cantidad": 100,
     "region": "RM"
   }
   
   Response:
   {
     "explicacion_simple": "Para 100 almuerzos en Santiago:",
     "precio_unitario": {
       "bajo": 2500,  // ⚠️ Riesgoso
       "medio": 3200,  // ✅ Recomendado
       "alto": 4000    // 💸 Menos competitivo
     },
     "recomendacion": {
       "valor": 3200,
       "texto": "Te recomendamos $3.200 por almuerzo",
       "razon": "Precio competitivo basado en 456 licitaciones similares ganadas"
     },
     "consejos": [
       "💡 Incluye todos tus costos (ingredientes, transporte, personal)",
       "📊 Este precio ha ganado el 68% de las veces",
       "⏰ Considera el plazo de entrega en tu cálculo"
     ],
     "siguiente_paso": {
       "accion": "crear_oferta",
       "url": "/api/v1/starter/crear-mi-primera-oferta"
     }
   }
   ```

3. **Analizar Licitación** → `/api/v1/starter/analizar-simple/{codigo}`
   ```json
   GET /api/v1/starter/analizar-simple/1234-56-LQ23
   
   Response:
   {
     "nivel": "starter",
     "recomendacion": "SI - Esta licitación es buena para ti",
     "puntaje_oportunidad": 8.5,  // de 10
     "analisis_simple": {
       "✅ pros": [
         "Presupuesto accesible para empresa pequeña",
         "Plazo de entrega realista (30 días)",
         "No requiere certificaciones complejas",
         "5 competidores (competencia moderada)"
       ],
       "⚠️ contras": [
         "Requiere transporte refrigerado",
         "Debe entregar en 3 locaciones"
       ],
       "❓ dudas_frecuentes": [
         {
           "q": "¿Necesito experiencia previa?",
           "a": "No, pero ayuda mostrar referencias de clientes"
         }
       ]
     },
     "checklist_preparacion": [
       { "item": "Calcular costo real de producción", "completado": false },
       { "item": "Verificar capacidad de entrega", "completado": false },
       { "item": "Preparar documentos requeridos", "completado": false }
     ],
     "siguiente_paso": "Calcular tu precio con nuestro recomendador"
   }
   ```

---

### 📈 Perfil 2: Empresa Muebles de Oficina (Intermedio)

**Contexto**: 3 años licitando, quiere mejorar su tasa de éxito.

#### Journey del Cliente

1. **Análisis de Competencia** → `/api/v1/pro/competidores-sector`
   ```json
   POST /api/v1/pro/competidores-sector
   Body: {
     "mi_rut": "76123456-7",
     "sector": "muebles oficina",
     "region": ["RM", "Valparaíso"],
     "periodo": "12m"
   }
   
   Response:
   {
     "mi_posicion": {
       "rank": 8,  // de 45 competidores
       "tasa_exito": 35.2,  // %
       "promedio_sector": 28.5,
       "estado": "Por sobre promedio ✅"
     },
     "top_competidores": [
       {
         "rank": 1,
         "nombre": "MUEBLES CORPORATIVOS SPA",
         "tasa_exito": 58.3,
         "licitaciones_ganadas": 47,
         "monto_total": 456000000,
         "ventajas_clave": [
           "Precios 12% más bajos que promedio",
           "Tiempos de entrega rápidos (15 días avg)",
           "Fuerte en licitaciones grandes (+$20M)"
         ],
         "donde_gana": ["Ministerios", "Hospitales", "Universidades"],
         "mi_comparacion": {
           "precio": "Ellos 15% más baratos",
           "velocidad": "Similar",
           "volumen": "Ellos pueden manejar 3x más"
         }
       }
     ],
     "oportunidades_nicho": [
       {
         "nicho": "Muebles ergonómicos especializados",
         "competidores": 3,  // Poca competencia
         "tasa_exito_promedio": 42,
         "razon": "Menos players, requiere certificación especial"
       }
     ],
     "recomendaciones": [
       "💡 Especialízate en muebles ergonómicos (solo 3 competidores)",
       "📊 Tus precios son competitivos, mejora tiempos de entrega",
       "🎯 Enfócate en licitaciones de $5M-$15M (tu sweet spot)"
     ]
   }
   ```

2. **Oportunidades Rankeadas** → `/api/v1/pro/oportunidades-rankeadas`
   ```json
   POST /api/v1/pro/oportunidades-rankeadas
   Body: {
     "mi_perfil": {
       "rut": "76123456-7",
       "capacidad_produccion_mensual": 500,
       "especialidades": ["escritorios", "sillas ergonómicas"],
       "certificaciones": ["ISO9001"],
       "tiempo_entrega_dias": 20
     }
   }
   
   Response:
   {
     "licitaciones_rankeadas": [
       {
         "rank": 1,
         "codigo": "5678-90-LQ23",
         "titulo": "Mobiliario para nueva oficina regional",
         "score_oportunidad": 92,  // de 100
         "probabilidad_ganar": "68%",
         "razon_score": {
           "match_capacidad": 95,  // Puedes cumplir fácilmente
           "match_especialidad": 100,  // Justo lo que haces
           "competencia": 85,  // Competencia moderada
           "precio_historico": 90  // Tus precios son buenos aquí
         },
         "analisis_detallado": {
           "ventajas": [
             "✅ Cantidad dentro de tu capacidad (400 unidades)",
             "✅ Tu especialidad (escritorios ergonómicos)",
             "✅ Tiempo de entrega suficiente (30 días)",
             "✅ Solo 4 competidores esperados"
           ],
           "desafios": [
             "⚠️ Requiere entrega en 3 ciudades (considera logística)",
             "⚠️ 2 competidores con precios 8% más bajos"
           ],
           "estrategia_sugerida": {
             "precio": "Ofrecer en percentil 45 ($2.850.000)",
             "diferenciador": "Enfatizar entrega rápida y servicio post-venta",
             "documentos_clave": ["Certificado ISO", "Portfolio de clientes"]
           }
         },
         "prediccion_ganador": {
           "probabilidad_tu_empresa": 68,
           "principales_factores": [
             "Precio competitivo (30%)",
             "Experiencia certificada (25%)",
             "Capacidad demostrada (20%)"
           ]
         }
       }
     ],
     "resumen_oportunidades": {
       "total_disponibles": 23,
       "alta_probabilidad": 5,  // >60%
       "media_probabilidad": 12,  // 30-60%
       "baja_probabilidad": 6  // <30%
     }
   }
   ```

3. **Tendencias del Sector** → `/api/v1/pro/tendencias/muebles-oficina`
   ```json
   GET /api/v1/pro/tendencias/muebles-oficina?periodo=12m&region=RM
   
   Response:
   {
     "periodo_analizado": "2024-01 a 2024-12",
     "volumen_mercado": {
       "total_licitaciones": 234,
       "monto_total": 2890000000,
       "variacion_vs_ano_anterior": "+18.5%",
       "tendencia": "📈 Crecimiento sostenido"
     },
     "evolucion_precios": {
       "precio_promedio_actual": 125000,
       "variacion_12m": "+8.2%",
       "grafica_mensual": [  // Últimos 12 meses
         { "mes": "2024-01", "precio_avg": 118000 },
         { "mes": "2024-12", "precio_avg": 125000 }
       ]
     },
     "tendencias_producto": [
       {
         "categoria": "Sillas ergonómicas",
         "crecimiento": "+35%",
         "razon": "Mayor conciencia de salud laboral",
         "oportunidad": "Alta demanda, pocos proveedores certificados"
       },
       {
         "categoria": "Escritorios ajustables",
         "crecimiento": "+28%",
         "razon": "Trabajo híbrido requiere flexibilidad",
         "oportunidad": "Nicho premium con márgenes altos"
       }
     ],
     "insights_estacionales": {
       "mejor_mes": "Marzo",
       "razon": "Nuevos presupuestos fiscales",
       "licitaciones_promedio": 28
     },
     "recomendaciones": [
       "🎯 Enfócate en sillas ergonómicas (35% crecimiento)",
       "📅 Prepara inventario para marzo (pico de licitaciones)",
       "💡 Considera certificación ergonómica para diferenciarte"
     ]
   }
   ```

---

### 🏆 Perfil 3: Empresa Consolidada (Experto)

**Contexto**: 8 años de experiencia, busca optimización y crecimiento.

#### Journey del Cliente

1. **Dashboard de Performance** → `/api/v1/expert/dashboard/{rut}`
   ```json
   GET /api/v1/expert/dashboard/76123456-7?periodo=12m
   
   Response:
   {
     "kpis_principales": {
       "tasa_conversion": {
         "actual": 45.2,
         "objetivo": 50,
         "vs_trimestre_anterior": "+3.8%",
         "vs_ano_anterior": "+12.5%",
         "benchmark_industria": 38.5
       },
       "roi": {
         "actual": 3.2,  // $3.20 ganado por cada $1 invertido
         "vs_trimestre_anterior": "+0.4",
         "mejor_trimestre": 4.1
       },
       "pipeline_value": {
         "licitaciones_activas": 15,
         "valor_total": 125000000,
         "probabilidad_ponderada": 56000000
       }
     },
     "analisis_performance": {
       "fortalezas": [
         "✅ Tasa de conversión 17% por sobre industria",
         "✅ Excelente en licitaciones $10M-$30M (65% éxito)",
         "✅ Relación calidad-precio valorada por compradores"
       ],
       "areas_mejora": [
         "📊 Baja conversión en licitaciones grandes (+$50M): solo 25%",
         "⏰ Tiempo promedio de respuesta: 8 días (competidores: 5 días)",
         "📉 Performance en Región de Valparaíso: 12% bajo promedio"
       ],
       "oportunidades": [
         "💡 Expandir a Regiones VI y VII (poca competencia)",
         "🎯 Mejorar propuestas para licitaciones grandes",
         "⚡ Reducir tiempo de respuesta a 5 días"
       ]
     },
     "evolucion_temporal": {
       "ultimos_12_meses": [
         { "mes": "2024-01", "licitaciones": 12, "ganadas": 5, "tasa": 41.7 },
         { "mes": "2024-12", "licitaciones": 15, "ganadas": 7, "tasa": 46.7 }
       ],
       "tendencia": "📈 Mejora consistente"
     },
     "segmentacion_exito": {
       "por_monto": [
         { "rango": "$1M-$10M", "tasa_exito": 52, "licitaciones": 45 },
         { "rango": "$10M-$30M", "tasa_exito": 65, "licitaciones": 78 },
         { "rango": "+$30M", "tasa_exito": 35, "licitaciones": 15 }
       ],
       "por_organismo": [
         { "tipo": "Ministerios", "tasa_exito": 48, "mejor_estrategia": "Precio competitivo + experiencia" },
         { "tipo": "Hospitales", "tasa_exito": 61, "mejor_estrategia": "Calidad + certificaciones" }
       ]
     }
   }
   ```

2. **Predicción de Éxito** → `/api/v1/expert/predecir-exito`
   ```json
   POST /api/v1/expert/predecir-exito
   Body: {
     "codigo_licitacion": "9012-34-LQ23",
     "mi_oferta_planeada": {
       "precio_total": 28500000,
       "tiempo_entrega_dias": 25,
       "certificaciones": ["ISO9001", "ISO14001"],
       "experiencia_similar": 8
     }
   }
   
   Response:
   {
     "prediccion": {
       "probabilidad_ganar": 72.3,  // % (ML model)
       "confianza_prediccion": 88,  // Qué tan confiable es el modelo
       "ranking_estimado": "2-3",  // de ~8 ofertas esperadas
       "factores_clave": [
         {
           "factor": "Precio",
           "impacto": 35,  // % de importancia
           "tu_posicion": "Competitivo",
           "detalle": "8% bajo mediana histórica (óptimo)"
         },
         {
           "factor": "Experiencia",
           "impacto": 25,
           "tu_posicion": "Excelente",
           "detalle": "8 años vs 4.2 promedio de competidores"
         },
         {
           "factor": "Certificaciones",
           "impacto": 20,
           "tu_posicion": "Por sobre promedio",
           "detalle": "Tienes ISO14001, solo 35% de competidores la tienen"
         },
         {
           "factor": "Tiempo Entrega",
           "impacto": 15,
           "tu_posicion": "Adecuado",
           "detalle": "25 días vs 30 requeridos"
         },
         {
           "factor": "Ubicación",
           "impacto": 5,
           "tu_posicion": "Neutral"
         }
       ]
     },
     "competidores_probables": [
       {
         "nombre": "EMPRESA A SPA",
         "probabilidad_participar": 85,
         "precio_estimado": 27500000,  // Basado en histórico
         "fortaleza": "Precios bajos",
         "debilidad": "Menos experiencia"
       }
     ],
     "escenarios": {
       "optimista": {
         "probabilidad": 85,
         "condiciones": "Si reduces precio a $27M y mejoras tiempo entrega"
       },
       "conservador": {
         "probabilidad": 55,
         "condiciones": "Si hay más competidores de lo esperado"
       }
     },
     "recomendaciones_optimizacion": [
       "💰 Considera bajar precio a $27.5M para asegurar victoria (prob: 85%)",
       "⚡ Ofrece entrega en 20 días para diferenciarte",
       "📄 Enfatiza ISO14001 en propuesta (pocos competidores la tienen)",
       "🎯 Destaca experiencia con casos similares en tu portafolio"
     ],
     "analisis_sensibilidad": {
       "si_bajo_precio_5pct": "+12% probabilidad",
       "si_mejoro_entrega_5dias": "+8% probabilidad",
       "si_aparece_competidor_fuerte": "-15% probabilidad"
     }
   }
   ```

3. **Benchmarking Competitivo** → `/api/v1/expert/benchmark`
   ```json
   POST /api/v1/expert/benchmark
   Body: {
     "mi_rut": "76123456-7",
     "competidores": ["77234567-8", "78345678-9"],
     "periodo": "12m",
     "metricas": ["conversion", "precios", "tiempos", "sectores"]
   }
   
   Response:
   {
     "tu_empresa": {
       "nombre": "TU EMPRESA SPA",
       "tasa_conversion": 45.2,
       "precio_promedio": 125000,
       "tiempo_respuesta_dias": 8,
       "sectores_fuertes": ["Muebles oficina", "Mobiliario educación"]
     },
     "comparacion_detallada": [
       {
         "competidor": "EMPRESA COMPETIDORA A",
         "metricas": {
           "tasa_conversion": { "ellos": 52.1, "tu": 45.2, "gap": -6.9 },
           "precio_promedio": { "ellos": 118000, "tu": 125000, "gap": "+5.9%" },
           "tiempo_respuesta": { "ellos": 5, "tu": 8, "gap": "+3 días" }
         },
         "ventajas_competidor": [
           "⚡ Más rápidos respondiendo (5 vs 8 días)",
           "💰 Precios 5.9% más bajos",
           "🎯 Mayor tasa de conversión en licitaciones grandes"
         ],
         "tus_ventajas": [
           "✅ Mejor en calidad (rating 4.7 vs 4.2)",
           "✅ Más certificaciones",
           "✅ Servicio post-venta superior"
         ],
         "donde_los_superas": [
           "Licitaciones de hospitales (65% vs 48%)",
           "Proyectos que requieren personalización"
         ],
         "donde_te_superan": [
           "Licitaciones municipales (38% vs 55%)",
           "Proyectos con presupuesto ajustado"
         ]
       }
     ],
     "insights_estrategicos": [
       "📊 Tu precio es 5.9% más alto que comp. A, pero tu calidad lo justifica",
       "⚡ CRÍTICO: Mejorar tiempo de respuesta a 5 días podría subir conversión 8-12%",
       "🎯 Enfócate en hospitales y educación (donde eres líder)",
       "💡 Considera línea económica para competir en municipalidades"
     ],
     "matriz_posicionamiento": {
       "tu_cuadrante": "Calidad Premium",
       "descripcion": "Precios medios-altos, alta calidad, servicio superior",
       "estrategia_recomendada": "Defender posición premium, enfatizar valor agregado"
     }
   }
   ```

4. **Optimización de Portfolio** → `/api/v1/expert/optimizar-portfolio`
   ```json
   POST /api/v1/expert/optimizar-portfolio
   Body: {
     "licitaciones_disponibles": [
       { "codigo": "A1", "monto": 15000000, "esfuerzo_horas": 40, "prob_ganar": 65 },
       { "codigo": "A2", "monto": 45000000, "esfuerzo_horas": 120, "prob_ganar": 35 },
       { "codigo": "A3", "monto": 8000000, "esfuerzo_horas": 20, "prob_ganar": 75 }
     ],
     "recursos_disponibles": {
       "horas_equipo": 200,
       "presupuesto_propuestas": 5000000,
       "deadline_dias": 30
     },
     "objetivos": {
       "prioridad_valor": 60,
       "prioridad_probabilidad": 40
     }
   }
   
   Response:
   {
     "portfolio_optimo": {
       "licitaciones_recomendadas": ["A1", "A3"],  // Skip A2
       "valor_esperado": 21750000,  // A1(15M*0.65) + A3(8M*0.75)
       "horas_requeridas": 60,
       "probabilidad_al_menos_una": 92.5,
       "razon": "Maximiza valor esperado con recursos limitados"
     },
     "analisis_decision": {
       "A1": {
         "decision": "✅ Incluir",
         "razon": "Alto valor esperado (9.75M), alta probabilidad, bajo esfuerzo",
         "roi_esperado": 3.9
       },
       "A2": {
         "decision": "❌ Omitir",
         "razon": "Baja probabilidad (35%), consume muchos recursos (120h)",
         "roi_esperado": 1.3,
         "nota": "Considera solo si no hay otras opciones"
       },
       "A3": {
         "decision": "✅ Incluir",
         "razon": "Excelente probabilidad (75%), bajo esfuerzo, quick win",
         "roi_esperado": 5.0
       }
     },
     "escenarios_alternativos": [
       {
         "nombre": "Máxima Probabilidad",
         "portfolio": ["A3"],
         "prob_ganar": 75,
         "valor_esperado": 6000000,
         "razon": "Si quieres asegurar al menos una victoria"
       },
       {
         "nombre": "Alto Riesgo-Alto Retorno",
         "portfolio": ["A2"],
         "prob_ganar": 35,
         "valor_esperado": 15750000,
         "razon": "Si tienes capacidad de asumir riesgo por mayor retorno"
       }
     ],
     "recomendaciones": [
       "✅ Prioriza A1 y A3 para maximizar ROI",
       "⏰ Enfoca primero en A3 (rápida, alta prob)",
       "📊 Monitorea A2, participa solo si hay cambios favorables",
       "💡 Con las 140 horas restantes, busca más oportunidades tipo A3"
     ]
   }
   ```

---

## Implementación Técnica

### Arquitectura por Niveles

```python
# Middleware para determinar nivel de usuario
async def get_user_level(user_id: int) -> str:
    subscription = await get_subscription(user_id)
    
    if subscription.tier == "free":
        return "starter"
    elif subscription.tier == "pro":
        return "pro"
    elif subscription.tier == "enterprise":
        return "expert"
```

### Respuestas Adaptativas

```python
def format_response_for_level(data: dict, level: str) -> dict:
    if level == "starter":
        # Simplificar, añadir explicaciones, enfatizar siguiente paso
        return simplify_response(data)
    elif level == "pro":
        # Datos completos, análisis intermedio
        return standard_response(data)
    elif level == "expert":
        # Máximo detalle, ML avanzado, múltiples escenarios
        return advanced_response(data)
```

---

**Versión:** 1.0  
**Última actualización:** 2025-12-11
