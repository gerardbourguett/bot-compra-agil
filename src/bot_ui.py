"""
Módulo de Interfaz de Usuario para el Bot de Telegram
Maneja menús, ayuda interactiva y tutoriales.
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
import database_bot as db_bot

# Definir estados para el tutorial (si fuera necesario ConversationHandler)
# Por ahora el tutorial será una secuencia de mensajes con botones

async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el menú principal con botones gráficos"""
    user_id = update.effective_user.id
    perfil = db_bot.obtener_perfil(user_id)
    
    nombre = perfil['nombre_empresa'] if perfil else update.effective_user.first_name
    
    mensaje = f"👋 <b>¡Hola {nombre}!</b>\n\n"
    mensaje += "Bienvenido a tu asistente de Compra Ágil.\n"
    mensaje += "¿Qué quieres hacer hoy?\n\n"
    
    # Dashboard con estadísticas breves si tiene perfil
    if perfil:
        mensaje += f"🏢 <b>{perfil['nombre_empresa']}</b>\n"
        # Aquí podrías agregar conteo de alertas o notificaciones pendientes
    
    # Estructura del menú principal
    keyboard = [
        [
            InlineKeyboardButton("🔍 Buscar", callback_data="menu_buscar"),
            InlineKeyboardButton("🎯 Oportunidades", callback_data="menu_oportunidades")
        ],
        [
            InlineKeyboardButton("⚡ Urgentes", callback_data="menu_urgentes"),
            InlineKeyboardButton("⭐ Guardadas", callback_data="menu_guardadas")
        ],
        [
            InlineKeyboardButton("⚙️ Perfil", callback_data="menu_perfil"),
            InlineKeyboardButton("❓ Ayuda", callback_data="menu_ayuda")
        ],
        [
             InlineKeyboardButton("🎓 Tutorial", callback_data="menu_tutorial")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(mensaje, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='HTML')

async def ayuda_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el centro de ayuda interactivo"""
    mensaje = "❓ <b>Centro de Ayuda</b>\n\n"
    mensaje += "Selecciona un tema para aprender más:"
    
    keyboard = [
        [InlineKeyboardButton("🔍 Cómo Buscar", callback_data="help_buscar")],
        [InlineKeyboardButton("🤖 Inteligencia Artificial", callback_data="help_ai")],
        [InlineKeyboardButton("⚙️ Configuración", callback_data="help_config")],
        [InlineKeyboardButton("📊 Comandos", callback_data="help_comandos")],
        [InlineKeyboardButton("🔙 Volver al Menú", callback_data="menu_principal")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(mensaje, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='HTML')

async def tutorial_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el tutorial paso a paso"""
    # Paso 1
    mensaje = "🎓 <b>Tutorial: Primeros Pasos</b> (1/4)\n\n"
    mensaje += "<b>1. Configura tu Perfil</b> 📝\n"
    mensaje += "Lo primero es decirle al bot qué hace tu empresa. Usa /configurar_perfil para definir tus productos, palabras clave y ubicación.\n\n"
    mensaje += "<i>¡Sin perfil, no puedo darte recomendaciones personalizadas!</i>"
    
    keyboard = [[InlineKeyboardButton("Siguiente ➡️", callback_data="tutorial_2")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(mensaje, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='HTML')

async def ui_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja las interacciones de botones de la UI"""
    query = update.callback_query
    data = query.data
    
    # Navegación del Tutorial
    if data == "tutorial_2":
        mensaje = "🎓 <b>Tutorial: Búsqueda</b> (2/4)\n\n"
        mensaje += "<b>2. Encuentra Negocios</b> 🔍\n"
        mensaje += "• /oportunidades: Te muestra lo mejor para TI (basado en tu perfil).\n"
        mensaje += "• /urgentes: Licitaciones que cierran en 3 días.\n"
        mensaje += "• /buscar [texto]: Búsqueda manual rápida."
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Anterior", callback_data="menu_tutorial"),
             InlineKeyboardButton("Siguiente ➡️", callback_data="tutorial_3")]
        ]
        await query.edit_message_text(mensaje, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    elif data == "tutorial_3":
        mensaje = "🎓 <b>Tutorial: Inteligencia Artificial</b> (3/4)\n\n"
        mensaje += "<b>3. Analiza con IA</b> 🤖\n"
        mensaje += "Cuando veas una licitación, presiona <b>Analizar 🤖</b>.\n"
        mensaje += "La IA leerá las bases por ti y te dirá:\n"
        mensaje += "✅ Si debes participar (compatibilidad).\n"
        mensaje += "📊 Probabilidad de éxito.\n"
        mensaje += "💡 Estrategia de precio."
        
        keyboard = [
            [InlineKeyboardButton("⬅️ Anterior", callback_data="tutorial_2"),
             InlineKeyboardButton("Siguiente ➡️", callback_data="tutorial_4")]
        ]
        await query.edit_message_text(mensaje, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    elif data == "tutorial_4":
        mensaje = "🎓 <b>Tutorial: Final</b> (4/4)\n\n"
        mensaje += "<b>4. Alertas y Más</b> 🔔\n"
        mensaje += "Activa /alertas_on para recibir avisos automáticos cada mañana.\n"
        mensaje += "También puedes guardar licitaciones favoritas con ⭐."
        
        keyboard = [[InlineKeyboardButton("🎉 ¡Listo! Ir al Menú", callback_data="menu_principal")]]
        await query.edit_message_text(mensaje, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

    # Navegación del Menú Principal (Redirecciones)
    elif data == "menu_principal":
        await menu_principal(update, context)
        
    elif data == "menu_ayuda":
        await ayuda_comando(update, context)

    # El resto de botones del menú principal llaman a comandos existentes
    # Esto se manejaría mejor en bot_inteligente.py o importando las funciones aquí
    # Para evitar importes circulares, devolvemos un flag o manejamos la lógica básica
    
    elif data == "menu_tutorial":
        await tutorial_comando(update, context)
        
    # Ayuda detallada
    elif data.startswith("help_"):
        tema = data.replace("help_", "")
        titulo = ""
        texto = ""
        
        if tema == "buscar":
            titulo = "🔍 Ayuda: Búsqueda"
            texto = "• <b>/buscar [palabra]</b>: Busca en titulo y descripción.\n" \
                    "• <b>/oportunidades</b>: Algoritmo de recomendación personalizado.\n" \
                    "• <b>/urgentes</b>: Ordenado por fecha de cierre próxima.\n" \
                    "• <b>/por_monto [min] [max]</b>: Filtra por presupuesto."
                    
        elif tema == "ai":
            titulo = "🤖 Ayuda: IA Gemini"
            texto = "El bot usa IA avanzada para leer las licitaciones.\n" \
                    "• <b>Analizar</b>: Te dice si cumples los requisitos técnicos.\n" \
                    "• <b>Recomendar</b>: Analiza un lote y elige las 5 mejores.\n" \
                    "• <b>Ayuda Cotizar</b>: Te da una lista de pasos para postular."
        
        elif tema == "config":
            titulo = "⚙️ Ayuda: Configuración"
            texto = "• <b>/configurar_perfil</b>: Datos de tu empresa.\n" \
                    "• <b>/configurar_score</b>: Qué te importa más (monto, competencia, etc).\n" \
                    "• <b>/alertas_on/off</b>: Activar notificaciones diarias."
                    
        elif tema == "comandos":
            titulo = "📊 Lista de Comandos"
            texto = "/start - Inicio\n/menu - Menú Principal\n/ayuda - Esta ayuda\n/perfil - Ver perfil\n/mis_guardadas - Favoritos"
            
        mensaje = f"<b>{titulo}</b>\n\n{texto}"
        keyboard = [[InlineKeyboardButton("🔙 Volver", callback_data="menu_ayuda")]]
        await query.edit_message_text(mensaje, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')

