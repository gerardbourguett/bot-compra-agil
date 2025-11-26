"""
Módulo de integración con Gemini AI para análisis de licitaciones.
"""
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Configurar Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Modelo a usar
MODEL_NAME = "gemini-2.0-flash-exp"


def analizar_licitacion_completo(licitacion, perfil_empresa, productos_detalle=None):
    """
    Realiza un análisis completo de una licitación usando Gemini AI.
    
    Args:
        licitacion: Dict con datos de la licitación
        perfil_empresa: Dict con perfil de la empresa
        productos_detalle: Lista de productos solicitados (opcional)
    
    Returns:
        dict con el análisis completo
    """
    
    # Construir prompt
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

{f"PRODUCTOS SOLICITADOS:\n" + chr(10).join([f"- {p.get('nombre')}: {p.get('cantidad')} {p.get('unidad_medida')}" for p in productos_detalle]) if productos_detalle else ""}

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
    "justificacion": "<por qué este rango>"
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

IMPORTANTE: Responde SOLO con el JSON, sin texto adicional antes o después."""

    try:
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        
        # Extraer JSON de la respuesta
        texto_respuesta = response.text.strip()
        
        # Limpiar markdown si existe
        if texto_respuesta.startswith("```json"):
            texto_respuesta = texto_respuesta[7:]
        if texto_respuesta.startswith("```"):
            texto_respuesta = texto_respuesta[3:]
        if texto_respuesta.endswith("```"):
            texto_respuesta = texto_respuesta[:-3]
        
        analisis = json.loads(texto_respuesta.strip())
        return analisis
        
    except Exception as e:
        print(f"Error en análisis de IA: {e}")
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
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        
        texto_respuesta = response.text.strip()
        if texto_respuesta.startswith("```json"):
            texto_respuesta = texto_respuesta[7:]
        if texto_respuesta.startswith("```"):
            texto_respuesta = texto_respuesta[3:]
        if texto_respuesta.endswith("```"):
            texto_respuesta = texto_respuesta[:-3]
        
        guia = json.loads(texto_respuesta.strip())
        return guia
        
    except Exception as e:
        print(f"Error al generar guía: {e}")
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
        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(prompt)
        
        texto_respuesta = response.text.strip()
        if texto_respuesta.startswith("```json"):
            texto_respuesta = texto_respuesta[7:]
        if texto_respuesta.startswith("```"):
            texto_respuesta = texto_respuesta[3:]
        if texto_respuesta.endswith("```"):
            texto_respuesta = texto_respuesta[:-3]
        
        comparacion = json.loads(texto_respuesta.strip())
        return comparacion
        
    except Exception as e:
        print(f"Error al comparar: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    # Prueba básica
    if GEMINI_API_KEY:
        print("✅ Gemini AI configurado correctamente")
        print(f"📝 Usando modelo: {MODEL_NAME}")
    else:
        print("❌ GEMINI_API_KEY no encontrada en .env")
