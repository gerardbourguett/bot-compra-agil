"""
Módulo de integración con AI para análisis de licitaciones.
NUEVO: Soporta múltiples proveedores (Gemini, Groq, Cerebras) via ai_providers.py
Mantiene backward compatibility con código existente.
"""
import logging
import json

# Importar abstracción de proveedores AI
try:
    from ai_providers import (
        generate_completion,
        get_ai_provider,
        get_available_providers,
        AIResponse
    )
    AI_PROVIDERS_AVAILABLE = True
except ImportError:
    AI_PROVIDERS_AVAILABLE = False

# Importar configuración centralizada
try:
    from config import GEMINI_API_KEY, GEMINI_MODEL, AI_PROVIDER
except ImportError:
    import os
    from dotenv import load_dotenv
    load_dotenv()
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-exp')
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini')

# Logger para este módulo
logger = logging.getLogger('compra_agil.gemini_ai')

# Configurar proveedor de AI
_ai_provider = None

def _get_provider():
    """Obtiene el proveedor de AI configurado (lazy loading)."""
    global _ai_provider
    if _ai_provider is None:
        if AI_PROVIDERS_AVAILABLE:
            try:
                _ai_provider = get_ai_provider()
                logger.info(f"Proveedor AI configurado: {_ai_provider.name} (modelo: {_ai_provider.model})")
            except Exception as e:
                logger.warning(f"Error configurando proveedor AI: {e}")
                # Fallback a Gemini directo
                _ai_provider = _setup_legacy_gemini()
        else:
            _ai_provider = _setup_legacy_gemini()
    return _ai_provider

def _setup_legacy_gemini():
    """Configuración legacy de Gemini (fallback)."""
    try:
        import google.generativeai as genai
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            logger.info(f"Gemini configurado (modo legacy): {GEMINI_MODEL}")
            return {'type': 'legacy_gemini', 'genai': genai, 'model': GEMINI_MODEL}
    except ImportError:
        logger.error("google-generativeai no instalado")
    return None

def _generate_text(prompt: str, **kwargs) -> str:
    """
    Genera texto usando el proveedor de AI configurado.
    Esta función abstrae la llamada al proveedor.
    """
    provider = _get_provider()
    
    if provider is None:
        raise RuntimeError("No hay proveedor de AI configurado")
    
    # Si es el nuevo sistema de proveedores
    if AI_PROVIDERS_AVAILABLE and hasattr(provider, 'generate'):
        response = provider.generate(prompt, **kwargs)
        return response.text
    
    # Fallback: modo legacy Gemini
    if isinstance(provider, dict) and provider.get('type') == 'legacy_gemini':
        genai = provider['genai']
        model = genai.GenerativeModel(provider['model'])
        response = model.generate_content(prompt)
        return response.text
    
    raise RuntimeError("Proveedor de AI no válido")

def _parse_json_response(text: str) -> dict:
    """Parsea respuesta de AI como JSON, limpiando markdown si existe."""
    texto_respuesta = text.strip()
    
    # Limpiar markdown si existe
    if texto_respuesta.startswith("```json"):
        texto_respuesta = texto_respuesta[7:]
    if texto_respuesta.startswith("```"):
        texto_respuesta = texto_respuesta[3:]
    if texto_respuesta.endswith("```"):
        texto_respuesta = texto_respuesta[:-3]
    
    return json.loads(texto_respuesta.strip())


# Backward compatibility: exponer MODEL_NAME para código legacy
MODEL_NAME = GEMINI_MODEL


def analizar_licitacion_completo(licitacion, perfil_empresa, productos_detalle=None, usar_historicos=True):
    """
    Realiza un análisis completo de una licitación usando Gemini AI.
    MEJORADO: Ahora incluye datos históricos reales (RAG) y recomendaciones ML.
    
    Args:
        licitacion: Dict con datos de la licitación
        perfil_empresa: Dict con perfil de la empresa
        productos_detalle: Lista de productos solicitados (opcional)
        usar_historicos: Si True, enriquece con datos históricos (RAG)
    
    Returns:
        dict con el análisis completo + datos históricos
    """
    
    # Construir lista de productos si existe
    productos_texto = ""
    if productos_detalle:
        productos_lineas = [f"- {p.get('nombre')}: {p.get('cantidad')} {p.get('unidad_medida')}" for p in productos_detalle]
        productos_texto = "PRODUCTOS SOLICITADOS:\n" + "\n".join(productos_lineas)
    
    # ========== NUEVO: INTEGRACIÓN CON SISTEMA RAG ==========
    contexto_historico = ""
    insights_historicos = ""
    recomendacion_precio_ml = None
    datos_rag = {}  # Inicializar vacío para evitar 'unbound'
    
    if usar_historicos:
        try:
            # Importar módulos ML (lazy import para evitar errores si no están disponibles)
            from rag_historico import enriquecer_analisis_licitacion
            from ml_precio_optimo import calcular_precio_optimo
            
            # Buscar casos históricos similares
            logger.info("Buscando casos históricos similares...")
            datos_rag = enriquecer_analisis_licitacion(
                nombre_licitacion=licitacion.get('nombre', ''),
                monto_estimado=licitacion.get('monto_disponible'),
                descripcion=productos_texto
            )
            
            if datos_rag.get('tiene_datos'):
                contexto_historico = datos_rag['contexto_para_prompt']
                insights_historicos = datos_rag['insights']
                logger.info(f"Encontrados {datos_rag['n_casos_encontrados']} casos históricos")
            
            # Calcular precio óptimo si hay productos
            if productos_detalle and len(productos_detalle) > 0:
                producto_principal = productos_detalle[0].get('nombre', '')
                cantidad = productos_detalle[0].get('cantidad', 1)
                
                if producto_principal:
                    logger.info(f"Calculando precio óptimo para '{producto_principal}'...")
                    recomendacion_precio_ml = calcular_precio_optimo(
                        producto=producto_principal,
                        cantidad=cantidad,
                        solo_ganadores=True
                    )
                    
                    if recomendacion_precio_ml.get('success'):
                        logger.info(f"Precio recomendado: ${recomendacion_precio_ml['precio_total']['recomendado']:,}")
        
        except ImportError as e:
            logger.warning(f"Módulos ML no disponibles: {e}")
        except Exception as e:
            logger.warning(f"Error al obtener datos históricos: {e}")
    
    # ========== FIN INTEGRACIÓN RAG ==========
    
    # Construir prompt enriquecido
    prompt = f"""Eres un experto en licitaciones públicas de Chile, especializado en Compra Ágil. 
Analiza la siguiente licitación para ayudar a una PYME a decidir si participar y cómo ganar.

PERFIL DE LA EMPRESA:
- Nombre: {perfil_empresa.get('nombre_empresa', 'No especificado')}
- Tipo de negocio: {perfil_empresa.get('tipo_negocio', 'No especificado')}
- Productos/Servicios: {perfil_empresa.get('productos_servicios', 'No especificado')}
- Palabras clave: {perfil_empresa.get('palabras_clave', 'No especificado')}
- Capacidad de entrega: {perfil_empresa.get('capacidad_entrega_dias', 'No especificado')} días
- Ubicación: {perfil_empresa.get('ubicacion', 'No especificado')}
- Experiencia: {perfil_empresa.get('experiencia_anos', 'No especificado')} años
- Certificaciones: {perfil_empresa.get('certificaciones', 'Ninguna')}

LICITACIÓN:
- Código: {licitacion.get('codigo')}
- Nombre: {licitacion.get('nombre')}
- Organismo: {licitacion.get('organismo')}
- Unidad: {licitacion.get('unidad', 'No especificado')}
- Presupuesto estimado: ${licitacion.get('monto_disponible', 0):,} CLP
- Moneda: {licitacion.get('moneda', 'CLP')}
- Fecha de cierre: {licitacion.get('fecha_cierre')}
- Fecha de publicación: {licitacion.get('fecha_publicacion')}
- Proveedores cotizando: {licitacion.get('cantidad_proveedores_cotizando', 0)}
- Estado: {licitacion.get('estado')}

{productos_texto}

{"=" * 60}
ANÁLISIS BASADO EN DATOS HISTÓRICOS REALES:
{"=" * 60}

{insights_historicos if insights_historicos else "No hay datos históricos disponibles para esta licitación."}

{contexto_historico}

{"=" * 60}
RECOMENDACIÓN DE PRECIO (ML):
{"=" * 60}
"""

    # Añadir recomendación de precio ML si existe
    if recomendacion_precio_ml and recomendacion_precio_ml.get('success'):
        prompt += f"""
{recomendacion_precio_ml['recomendacion']}

Estadísticas detalladas:
- {recomendacion_precio_ml['estadisticas']['n_registros']} licitaciones similares analizadas
- {recomendacion_precio_ml['estadisticas']['n_ganadores']} ofertas ganadoras
- Tasa de conversión histórica: {recomendacion_precio_ml['estadisticas']['tasa_conversion']:.1f}%

IMPORTANTE: Usa esta información REAL para fundamentar tu recomendación de precio.
"""
    else:
        prompt += "\nNo hay datos suficientes para calcular precio óptimo con ML.\n"

    prompt +=f"""
{"=" * 60}

Proporciona un análisis estructurado en formato JSON con los siguientes campos:

{{
  "compatibilidad": {{
    "score": <número 0-100>,
    "explicacion": "<por qué este score>",
    "fortalezas": ["<fortaleza 1>", "<fortaleza 2>", ...],
    "debilidades": ["<debilidad 1>", "<debilidad 2>", ...]
  }},
  "recomendacion_precio": {{
    "rango_minimo": <número>,
    "rango_maximo": <número>,
    "precio_sugerido": <número>,
    "estrategia": "<explicación de la estrategia de precio>",
    "justificacion": "<por qué este rango - cita los datos históricos si los usaste>"
  }},
  "analisis_competencia": {{
    "nivel_competencia": "<bajo/medio/alto>",
    "ventajas_competitivas": ["<ventaja 1>", "<ventaja 2>", ...],
    "riesgos": ["<riesgo 1>", "<riesgo 2>", ...]
  }},
  "recomendaciones": {{
    "debe_participar": <true/false>,
    "probabilidad_exito": "<baja/media/alta>",
    "acciones_clave": ["<acción 1>", "<acción 2>", ...],
    "que_destacar": ["<punto 1>", "<punto 2>", ...],
    "consejos_cotizacion": ["<consejo 1>", "<consejo 2>", ...]
  }},
  "resumen_ejecutivo": "<resumen en 2-3 oraciones sobre si conviene participar y por qué>"
}}

IMPORTANTE: 
- Responde SOLO con el JSON, sin texto adicional antes o después.
- Fundamenta tus recomendaciones en los DATOS HISTÓRICOS REALES proporcionados arriba.
- Menciona específicamente insights de casos históricos en tu análisis."""
    
    try:
        texto_respuesta = _generate_text(prompt)
        analisis = _parse_json_response(texto_respuesta)
        
        # Añadir metadatos sobre datos históricos usados
        analisis['_metadata'] = {
            'uso_datos_historicos': usar_historicos,
            'casos_historicos_encontrados': datos_rag.get('n_casos_encontrados', 0) if usar_historicos and datos_rag.get('tiene_datos') else 0,
            'precio_ml_calculado': recomendacion_precio_ml is not None and recomendacion_precio_ml.get('success', False),
            'confianza_precio_ml': recomendacion_precio_ml.get('confianza', 0) if recomendacion_precio_ml else 0
        }
        
        return analisis
        
    except Exception as e:
        logger.error(f"Error en análisis de IA: {e}")
        return {
            "error": str(e),
            "compatibilidad": {"score": 0, "explicacion": "Error al analizar"},
            "recomendacion_precio": {"precio_sugerido": 0, "estrategia": "No disponible"},
            "analisis_competencia": {"nivel_competencia": "desconocido"},
            "recomendaciones": {"debe_participar": False, "probabilidad_exito": "desconocida"},
            "resumen_ejecutivo": "No se pudo completar el análisis"
        }



def generar_ayuda_cotizacion(licitacion, perfil_empresa, analisis):
    """
    Genera una guía personalizada para preparar la cotización.
    
    Returns:
        dict con checklist, plantilla y consejos
    """
    
    prompt = f"""Basándote en el siguiente análisis de licitación, genera una guía práctica para preparar la cotización.

LICITACIÓN:
- Código: {licitacion.get('codigo')}
- Nombre: {licitacion.get('nombre')}
- Presupuesto: ${licitacion.get('monto_disponible', 0):,} CLP

PERFIL EMPRESA:
- {perfil_empresa.get('nombre_empresa')}
- {perfil_empresa.get('productos_servicios')}

ANÁLISIS PREVIO:
- Score compatibilidad: {analisis.get('compatibilidad', {}).get('score', 0)}
- Precio sugerido: ${analisis.get('recomendacion_precio', {}).get('precio_sugerido', 0):,} CLP

Genera en formato JSON:

{{
  "checklist_documentos": [
    {{"item": "<documento>", "obligatorio": true/false, "descripcion": "<breve descripción>"}}
  ],
  "estructura_cotizacion": {{
    "seccion_1": "<qué incluir>",
    "seccion_2": "<qué incluir>",
    ...
  }},
  "consejos_presentacion": ["<consejo 1>", "<consejo 2>", ...],
  "errores_evitar": ["<error 1>", "<error 2>", ...],
  "timeline_sugerido": {{
    "dias_antes_cierre": [
      {{"dias": 7, "tarea": "<qué hacer>"}},
      {{"dias": 3, "tarea": "<qué hacer>"}},
      {{"dias": 1, "tarea": "<qué hacer>"}}
    ]
  }}
}}

Responde SOLO con el JSON."""

    try:
        texto_respuesta = _generate_text(prompt)
        guia = _parse_json_response(texto_respuesta)
        return guia
        
    except Exception as e:
        logger.error(f"Error al generar guía: {e}")
        return {
            "error": str(e),
            "checklist_documentos": [],
            "consejos_presentacion": ["No disponible"]
        }


def comparar_licitaciones(licitacion1, licitacion2, perfil_empresa):
    """
    Compara dos licitaciones y recomienda cuál es mejor para la empresa.
    """
    
    prompt = f"""Compara estas dos licitaciones para la empresa y recomienda cuál es mejor opción.

PERFIL EMPRESA:
- {perfil_empresa.get('nombre_empresa')}
- {perfil_empresa.get('productos_servicios')}

LICITACIÓN A:
- Código: {licitacion1.get('codigo')}
- Nombre: {licitacion1.get('nombre')}
- Presupuesto: ${licitacion1.get('monto_disponible', 0):,} CLP
- Cierre: {licitacion1.get('fecha_cierre')}
- Competidores: {licitacion1.get('cantidad_proveedores_cotizando', 0)}

LICITACIÓN B:
- Código: {licitacion2.get('codigo')}
- Nombre: {licitacion2.get('nombre')}
- Presupuesto: ${licitacion2.get('monto_disponible', 0):,} CLP
- Cierre: {licitacion2.get('fecha_cierre')}
- Competidores: {licitacion2.get('cantidad_proveedores_cotizando', 0)}

Responde en formato JSON:

{{
  "recomendacion": "A" o "B",
  "razon_principal": "<por qué>",
  "ventajas_opcion_recomendada": ["<ventaja 1>", ...],
  "desventajas_otra_opcion": ["<desventaja 1>", ...],
  "consideraciones": ["<consideración 1>", ...],
  "resumen": "<resumen ejecutivo>"
}}

Responde SOLO con el JSON."""

    try:
        texto_respuesta = _generate_text(prompt)
        comparacion = _parse_json_response(texto_respuesta)
        return comparacion
        
    except Exception as e:
        logger.error(f"Error al comparar: {e}")
        return {"error": str(e)}


def generar_borrador_oferta(licitacion, perfil_empresa, formato="texto", instrucciones_extra=""):
    """
    Genera un borrador de oferta para una licitación.
    
    Args:
        licitacion: Dict con datos de la licitación
        perfil_empresa: Dict con perfil de la empresa
        formato: "texto", "pdf" (estructura formal), "correo"
        instrucciones_extra: Instrucciones adicionales del usuario
        
    Returns:
        str: El contenido generado
    """
    
    tipo_formato = {
        "texto": "un mensaje de texto para Telegram, conciso y directo, resaltando los puntos clave.",
        "pdf": "una propuesta formal estructurada (Introducción, Propuesta Técnica, Propuesta Económica, Plazos, Experiencia). Usa formato Markdown.",
        "correo": "un correo electrónico profesional, con asunto sugerido, saludo formal y cuerpo persuasivo."
    }
    
    desc_formato = tipo_formato.get(formato, tipo_formato["texto"])
    
    prompt = f"""Actúa como un experto en ventas B2B y licitaciones públicas.
Redacta {desc_formato} para postular a la siguiente licitación de Compra Ágil.

PERFIL DE MI EMPRESA:
- Nombre: {perfil_empresa.get('nombre_empresa', 'No especificado')}
- Giro: {perfil_empresa.get('tipo_negocio', 'No especificado')}
- Productos/Servicios: {perfil_empresa.get('productos_servicios', 'No especificado')}
- Fortalezas: {perfil_empresa.get('palabras_clave', '')}
- Experiencia: {perfil_empresa.get('experiencia_anos', 0)} años
- Ubicación: {perfil_empresa.get('ubicacion', 'No especificado')}

DATOS DE LA LICITACIÓN:
- Código: {licitacion.get('codigo')}
- Nombre: {licitacion.get('nombre')}
- Organismo: {licitacion.get('organismo')}
- Descripción: {licitacion.get('descripcion', 'Ver detalles en ficha')}
- Presupuesto: ${licitacion.get('monto_disponible', 0):,} (Referencial)
- Fecha Cierre: {licitacion.get('fecha_cierre')}

INSTRUCCIONES ADICIONALES:
{instrucciones_extra}

OBJETIVO:
Persuadir al comprador de que somos la mejor opción por calidad, confianza y cumplimiento.
Si es formato PDF, estructura el contenido con títulos claros.
Si es correo, incluye el Asunto.

Genera SOLO el contenido del borrador."""

    try:
        texto_respuesta = _generate_text(prompt)
        return texto_respuesta.strip()
        
    except Exception as e:
        logger.error(f"Error al generar borrador: {e}")
        return f"Lo siento, hubo un error al generar el borrador: {str(e)}"


if __name__ == "__main__":
    # Prueba básica - configurar logging para ver output
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    
    logger.info("=" * 60)
    logger.info("COMPRA AGIL - AI Module Status")
    logger.info("=" * 60)
    
    # Mostrar info del proveedor configurado
    logger.info(f"Proveedor configurado: {AI_PROVIDER}")
    
    try:
        provider = _get_provider()
        if hasattr(provider, 'name'):
            logger.info(f"Proveedor activo: {provider.name} (modelo: {provider.model})")
            logger.info("Estado: OK")
        elif isinstance(provider, dict) and provider.get('type') == 'legacy_gemini':
            logger.info(f"Proveedor activo: Gemini (modo legacy, modelo: {provider['model']})")
            logger.info("Estado: OK")
        else:
            logger.warning("Proveedor no configurado correctamente")
    except Exception as e:
        logger.error(f"Error al obtener proveedor: {e}")
    
    # Listar proveedores disponibles si ai_providers está disponible
    if AI_PROVIDERS_AVAILABLE:
        try:
            available = get_available_providers()
            logger.info(f"Proveedores disponibles: {', '.join(available) if available else 'Ninguno'}")
        except Exception:
            pass
    
    logger.info("=" * 60)
