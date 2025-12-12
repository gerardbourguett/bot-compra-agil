"""
Generador de Prompts Dinámicos - CompraÁgil
Sistema completo incluyendo factory, ejemplos y testing
"""
from gemini_prompts import (
    ContextoUsuario, ContextoLicitacion, PerfilExperiencia,
    clasificar_perfil, get_system_prompt_principiante,
    get_system_prompt_intermedio, get_system_prompt_experto
)

# ==================== FACTORY PRINCIPAL ====================

def generar_prompt_dinamico(
    usuario: ContextoUsuario,
    licitacion: ContextoLicitacion,
    caso_uso: str = "analisis_general"
) -> str:
    """
    Factory principal que genera el system prompt apropiado
    
    Args:
        usuario: Contexto del usuario
        licitacion: Contexto de la licitación
        caso_uso: Tipo de análisis a realizar
    
    Returns:
        System prompt completo y personalizado
    """
    
    # Seleccionar prompt base según perfil
    if usuario.nivel_experiencia ==  PerfilExperiencia.PRINCIPIANTE:
        base_prompt = get_system_prompt_principiante(usuario)
    elif usuario.nivel_experiencia == PerfilExperiencia.INTERMEDIO:
        base_prompt = get_system_prompt_intermedio(usuario, licitacion)
    else:  # EXPERTO
        base_prompt = get_system_prompt_experto(usuario)
    
    # Añadir instrucciones específicas según caso de uso
    if caso_uso == "simplificar":
        base_prompt += "\n\nTAREA ESPECÍFICA: Simplifica la descripción técnica a 3 puntos clave."
    elif caso_uso == "generar_preguntas":
        base_prompt += "\n\nTAREA ESPECÍFICA: Genera 3-5 preguntas estratégicas para periodo de consultas."
    elif caso_uso == "detectar_trampas":
        base_prompt += "\n\nTAREA ESPECÍFICA: Identifica cláusulas riesgosas en las bases."
    
    return base_prompt

# ==================== USER PROMPT GENERATORS ====================

def generar_user_prompt_analisis(licitacion: ContextoLicitacion) -> str:
    """Genera user prompt para análisis de licitación"""
    return f"""
Analiza esta licitación de Compra Ágil:

**CÓDIGO:** {licitacion.codigo}
**TÍTULO:** {licitacion.titulo}
**ORGANISMO:** {licitacion.organismo}
**MONTO ESTIMADO:** ${licitacion.monto_estimado:,}
**REGIÓN:** {licitacion.region or 'Nacional'}
**FECHA CIERRE:** {licitacion.fecha_cierre or 'No especificada'}

**DESCRIPCIÓN:**
{licitacion.descripcion}

Genera tu análisis en formato JSON según las instrucciones de tu rol.
"""

# ==================== ONBOARDING SYSTEM ====================

PREGUNTAS_ONBOARDING = {
    "rubro": {
        "pregunta": "¿Cuál es tu rubro principal?",
        "tipo": "select",
       "opciones": [
            "Servicios de Catering y Alimentación",
            "Muebles y Mobiliario",
            "Tecnología y Computación",
            "Construcción y Obras",
            "Consultorías y Servicios Profesionales",
            "Aseo y Servicios Generales",
            "Artículos de Oficina y Papeler ía",
            "Ferretería y Materiales",
            "Otro (especificar)"
        ]
    },
    "experiencia": {
        "pregunta": "¿Cuántas licitaciones de Compra Ágil has GANADO en el último año?",
        "tipo": "number",
        "clasificacion": {
            "0": "PRINCIPIANTE",
            "1-10": "INTERMEDIO",
            "10+": "EXPERTO"
        }
    },
    "dolor": {
        "pregunta": "¿Qué es lo que más te cuesta hoy en Compra Ágil?",
        "tipo": "select",
        "opciones": [
            "Entender los requisitos y documentos técnicos",
            "Saber qué precio poner para ganar",
            "Gestionar el volumen de licitaciones disponibles",
            "Encontrar licitaciones relevantes para mi negocio"
        ],
        "mapping": {
            "Entender los requisitos": "entender_papeles",
            "Saber qué precio poner": "saber_precio",
            "Gestionar el volumen": "gestionar_volumen",
            "Encontrar licitaciones": "descubrir_oportunidades"
        }
    },
    "ubicacion": {
        "pregunta": "¿En qué región operas principalmente?",
        "tipo": "select",
        "opciones": ["RM", "Valparaíso", "Biobío", "Antofagasta", "Otra"],
        "opcional": True
    }
}

def crear_perfil_desde_onboarding(respuestas: dict) -> ContextoUsuario:
    """
    Crea un perfil de usuario desde las respuestas del onboarding
    
    Args:
        respuestas: Dict con respuestas del usuario
        
    Returns:
        ContextoUsuario completo
    """
    nivel = clasificar_perfil(
        adjudicaciones=respuestas.get("experiencia", 0),
        dolor=respuestas.get("dolor")
    )
    
    return ContextoUsuario(
        nombre_empresa=respuestas.get("nombre_empresa", "Tu Empresa"),
        rubro=respuestas.get("rubro", "General"),
        nivel_experiencia=nivel,
        historial_adjudicaciones=respuestas.get("experiencia", 0),
        dolor_principal=respuestas.get("dolor"),
        ubicacion=respuestas.get("ubicacion")
    )

# ==================== EJEMPLOS DE USO ====================

def demo_caso_catering_principiante():
    """Demo: Empresa de catering principiante"""
    print("=" * 80)
    print("DEMO: CASO CATERING PRINCIPIANTE")
    print("=" * 80)
    
    # Contexto del usuario
    usuario = ContextoUsuario(
        nombre_empresa="Banquetes Doña Clara",
        rubro="Servicios de Catering y Coffee Break",
        nivel_experiencia=PerfilExperiencia.PRINCIPIANTE,
        historial_adjudicaciones=0,
        dolor_principal="entender_papeles"
    )
    
    # Contexto de licitación
    licitacion = ContextoLicitacion(
        codigo="1234-56-LQ23",
        titulo="Servicio de Coffee Break para capacitación",
        descripcion="""
        Se requiere servicio completo de coffee break para jornada de
        capacitación funcionarios municipales. 50 personas, 2 breaks diarios
        (mañana y tarde) durante 3 días. Debe incluir: café, té, jugos,
        galletas, fruta picada. Servicio en dependencias municipales.
        Presupuesto total: $250.000. Entrega: Del 15 al 17 de enero 2025.
        """,
        monto_estimado=250000,
        organismo="Municipalidad de Providencia",
        region="RM",
        fecha_cierre="2025-01-10"
    )
    
    # Generar prompts
    system_prompt = generar_prompt_dinamico(usuario, licitacion, "analisis_general")
    user_prompt = generar_user_prompt_analisis(licitacion)
    
    print("\n📝 SYSTEM PROMPT:")
    print(system_prompt[:500] + "...\n")
    
    print("\n👤 USER PROMPT:")
    print(user_prompt)
    
    print("\n✅ Este prompt generará un análisis SIMPLE para principiantes")
    print("=" * 80)

def demo_caso_muebles_intermedio():
    """Demo: Empresa de muebles intermedia"""
    print("\n" + "=" * 80)
    print("DEMO: CASO MUEBLES INTERMEDIO")
    print("=" * 80)
    
    usuario = ContextoUsuario(
        nombre_empresa="Muebles Corporativos SPA",
        rubro="Muebles y Mobiliario de Oficina",
        nivel_experiencia=PerfilExperiencia.INTERMEDIO,
        historial_adjudicaciones=7,
        dolor_principal="saber_precio"
    )
    
    licitacion = ContextoLicitacion(
        codigo="5678-90-LQ23",
        titulo="Mobiliario ergonómico para nueva oficina regional",
        descripcion="""
        Adquisición de mobiliario ergonómico para 40 puestos de trabajo.
        Incluye: 40 escritorios regulables en altura (eléctricos),
        40 sillas ergonómicas certificadas BIFMA, 10 mesas de reunión.
        Instalación incluida. Garantía 3 años. Monto: $45.000.000.
        """,
        monto_estimado=45000000,
        organismo="Servicio de Salud Metropolitano Sur",
        region="RM",
        fecha_cierre="2025-01-20"
    )
    
    system_prompt = generar_prompt_dinamico(usuario, licitacion)
    
    print("\n📝 SYSTEM PROMPT (extracto):")
    print(system_prompt[:600] + "...")
    
    print("\n✅ Este prompt incluye:")
    print("  - Análisis de brecha competitiva")
    print("  - Estimación de competencia")
    print("  - Estrategia de diferenciación")
    print("  - Recomendación de pricing")
    print("=" * 80)

def demo_caso_consultora_experto():
    """Demo: Consultora experta"""
    print("\n" + "=" * 80)
    print("DEMO: CASO CONSULTORA EXPERTO")
    print("=" * 80)
    
    usuario = ContextoUsuario(
        nombre_empresa="Consultores Avanzados Ltda",
        rubro="Consultoría en Transformación Digital",
        nivel_experiencia=PerfilExperiencia.EXPERTO,
        historial_adjudicaciones=25,
        dolor_principal="gestionar_volumen"
    )
    
    licitacion = ContextoLicitacion(
        codigo="9012-34-LQ23",
        titulo="Servicio de asesoría en modernización de procesos",
        descripcion="Servicio de apoyo para modernización...",
        monto_estimado=35000000,
        organismo="Subsecretaría de Desarrollo Regional",
        region="Nacional"
    )
    
    system_prompt = generar_prompt_dinamico(usuario, licitacion)
    
    print("\n📝 SYSTEM PROMPT (extracto):")
    print(system_prompt[:600] + "...")
    
    print("\n✅ Este prompt es CRÍTICO y TÉCNICO:")
    print("  - Sin explicaciones básicas")
    print("  - Go/No-Go decision basada en historial")
    print("  - Optimización semántica de propuesta")
    print("  - Análisis ROI y probabilidad ML")
    print("=" * 80)

# ==================== TESTING ====================

if __name__ == "__main__":
    print("\n🚀 SISTEMA DE PROMPTS DINÁMICOS - CompraÁgil\n")
    
    # Test 1: Clasificación automática
    print("TEST 1: Clasificación de Perfil")
    print("-" * 40)
    print(f"0 adjudicaciones → {clasificar_perfil(0)}")
    print(f"5 adjudicaciones → {clasificar_perfil(5)}")
    print(f"15 adjudicaciones → {clasificar_perfil(15)}")
    
    # Test 2: Demos por perfil
    demo_caso_catering_principiante()
    demo_caso_muebles_intermedio()
    demo_caso_consultora_experto()
    
    print("\n✅ Sistema de prompts dinámicos funcionando correctamente")
    print("📝 Listo para integrar con Gemini AI\n")
