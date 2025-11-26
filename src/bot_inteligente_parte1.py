"""
Bot de Telegram Inteligente para Compra Ágil
Incluye análisis con Gemini AI, perfiles de empresa y búsquedas avanzadas.
"""
import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    ConversationHandler, MessageHandler, filters, CallbackQueryHandler
)
import database_extended as db
import database_bot as db_bot
import gemini_ai
import filtros
import api_client

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Configurar logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Estados para el ConversationHandler del perfil
(NOMBRE_EMPRESA, TIPO_NEGOCIO, PRODUCTOS, PALABRAS_CLAVE, 
 CAPACIDAD, UBICACION, EXPERIENCIA, CERTIFICACIONES,
 MONTO_MIN, MONTO_MAX) = range(10)

# Estados para configuración de score
(PESO_PALABRAS, PESO_COMPETENCIA, PESO_MONTO) = range(10, 13)


# ==================== COMANDOS BÁSICOS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Bienvenida y ayuda"""
    user_id = update.effective_user.id
    perfil = db_bot.obtener_perfil(user_id)
    
    if perfil:
        mensaje = f"¡Hola de nuevo, {perfil['nombre_empresa']}! 👋\n\n"
    else:
        mensaje = "¡Bienvenido al Bot Inteligente de Compra Ágil! 🤖\n\n"
        mensaje += "Para comenzar, configura tu perfil de empresa con /configurar_perfil\n\n"
    
    mensaje += "<b>Comandos disponibles:</b>\n\n"
    mensaje += "<b>📋 Perfil y Configuración:</b>\n"
    mensaje += "/configurar_perfil - Configurar perfil de empresa\n"
    mensaje += "/configurar_score - Ajustar prioridades de score\n"
    mensaje += "/perfil - Ver tu perfil actual\n\n"
    
    mensaje += "<b>🔍 Búsqueda:</b>\n"
    mensaje += "/buscar [palabra] - Buscar licitaciones\n"
    mensaje += "/oportunidades - Licitaciones para ti\n"
    mensaje += "/urgentes - Cierran pronto\n"
    mensaje += "/por_monto [min] [max] - Por rango de monto\n\n"
    
    mensaje += "<b>🤖 Análisis con IA:</b>\n"
    mensaje += "/analizar [código] - Análisis completo\n"
    mensaje += "/recomendar - Top 5 recomendadas\n"
    mensaje += "/ayuda_cotizar [código] - Guía para cotizar\n\n"
    
    mensaje += "<b>⭐ Guardadas:</b>\n"
    mensaje += "/guardar [código] - Guardar licitación\n"
    mensaje += "/mis_guardadas - Ver guardadas\n"
    mensaje += "/eliminar_guardada [código] - Eliminar\n\n"
    
    mensaje += "<b>🔔 Alertas:</b>\n"
    mensaje += "/alertas_on - Activar alertas\n"
    mensaje += "/alertas_off - Desactivar alertas\n"
    
    await update.message.reply_text(mensaje, parse_mode='HTML')


# ==================== CONFIGURACIÓN DE PERFIL ====================

async def configurar_perfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el proceso de configuración del perfil"""
    await update.message.reply_text(
        "📝 <b>Configuración de Perfil</b>\n\n"
        "Vamos a configurar tu perfil empresarial para darte mejores recomendaciones.\n\n"
        "¿Cuál es el <b>nombre de tu empresa</b>?\n"
        "(Escribe /cancelar para cancelar en cualquier momento)",
        parse_mode='HTML'
    )
    return NOMBRE_EMPRESA


async def recibir_nombre_empresa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el nombre de la empresa"""
    context.user_data['perfil'] = {'nombre_empresa': update.message.text}
    
    keyboard = [
        [InlineKeyboardButton("Productos", callback_data='tipo_productos')],
        [InlineKeyboardButton("Servicios", callback_data='tipo_servicios')],
        [InlineKeyboardButton("Ambos", callback_data='tipo_ambos')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "¿Tu empresa vende principalmente <b>productos</b> o <b>servicios</b>?",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return TIPO_NEGOCIO


async def recibir_tipo_negocio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el tipo de negocio"""
    query = update.callback_query
    await query.answer()
    
    tipo_map = {
        'tipo_productos': 'Productos',
        'tipo_servicios': 'Servicios',
        'tipo_ambos': 'Productos y Servicios'
    }
    
    context.user_data['perfil']['tipo_negocio'] = tipo_map[query.data]
    
    await query.edit_message_text(
        f"Tipo de negocio: <b>{tipo_map[query.data]}</b> ✅\n\n"
        "Describe brevemente los <b>productos o servicios</b> que ofreces:\n"
        "(Ejemplo: 'Sillas de oficina, escritorios, mobiliario escolar')",
        parse_mode='HTML'
    )
    return PRODUCTOS


async def recibir_productos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la descripción de productos/servicios"""
    context.user_data['perfil']['productos_servicios'] = update.message.text
    
    await update.message.reply_text(
        "Ahora, escribe <b>palabras clave</b> separadas por comas que describan tu negocio:\n"
        "(Ejemplo: 'sillas, mobiliario, oficina, ergonómico')\n\n"
        "Esto ayudará a encontrar licitaciones relevantes.",
        parse_mode='HTML'
    )
    return PALABRAS_CLAVE


async def recibir_palabras_clave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe las palabras clave"""
    context.user_data['perfil']['palabras_clave'] = update.message.text
    
    await update.message.reply_text(
        "¿En cuántos <b>días</b> puedes entregar típicamente?\n"
        "(Escribe solo el número, ejemplo: 7)",
        parse_mode='HTML'
    )
    return CAPACIDAD


async def recibir_capacidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la capacidad de entrega"""
    try:
        dias = int(update.message.text)
        context.user_data['perfil']['capacidad_entrega_dias'] = dias
        
        await update.message.reply_text(
            "¿En qué <b>ciudad o región</b> está ubicada tu empresa?\n"
            "(Ejemplo: 'Santiago', 'Valparaíso', 'Región Metropolitana')",
            parse_mode='HTML'
        )
        return UBICACION
    except ValueError:
        await update.message.reply_text(
            "Por favor escribe solo un número. ¿Cuántos días?",
            parse_mode='HTML'
        )
        return CAPACIDAD


async def recibir_ubicacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe la ubicación"""
    context.user_data['perfil']['ubicacion'] = update.message.text
    
    await update.message.reply_text(
        "¿Cuántos <b>años de experiencia</b> tiene tu empresa?\n"
        "(Escribe solo el número, o 0 si es nueva)",
        parse_mode='HTML'
    )
    return EXPERIENCIA


async def recibir_experiencia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe los años de experiencia"""
    try:
        anos = int(update.message.text)
        context.user_data['perfil']['experiencia_anos'] = anos
        
        await update.message.reply_text(
            "Por último, ¿tienes alguna <b>certificación</b> relevante?\n"
            "(Ejemplo: 'ISO 9001, Registro en ChileProveedores')\n"
            "Escribe 'ninguna' si no tienes.",
            parse_mode='HTML'
        )
        return CERTIFICACIONES
    except ValueError:
        await update.message.reply_text(
            "Por favor escribe solo un número. ¿Cuántos años?",
            parse_mode='HTML'
        )
        return EXPERIENCIA


async def recibir_certificaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe las certificaciones"""
    context.user_data['perfil']['certificaciones'] = update.message.text
    
    await update.message.reply_text(
        "💰 <b>Configuración de Montos</b>\n\n"
        "¿Cuál es el <b>monto mínimo</b> de licitaciones que te interesa?\n"
        "(Escribe el número, ejemplo: 500000 para $500.000)\n"
        "Escribe 0 si no tienes mínimo.",
        parse_mode='HTML'
    )
    return MONTO_MIN


async def recibir_monto_min(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el monto mínimo"""
    try:
        texto = update.message.text.replace('.', '').replace(',', '').replace('$', '').strip()
        monto = int(texto)
        context.user_data['perfil']['monto_minimo_interes'] = monto
        
        await update.message.reply_text(
            "¿Cuál es el <b>monto máximo</b> que puedes manejar?\n"
            "(Escribe el número, ejemplo: 5000000 para $5.000.000)\n"
            "Escribe 0 si no tienes límite.",
            parse_mode='HTML'
        )
        return MONTO_MAX
    except ValueError:
        await update.message.reply_text(
            "Por favor escribe solo un número válido (ej: 500000).",
            parse_mode='HTML'
        )
        return MONTO_MIN


async def recibir_monto_max(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe el monto máximo y guarda el perfil"""
    user_id = update.effective_user.id
    try:
        texto = update.message.text.replace('.', '').replace(',', '').replace('$', '').strip()
        monto = int(texto)
        context.user_data['perfil']['monto_maximo_capacidad'] = monto
        
        # Validar que max >= min (si ambos son > 0)
        minimo = context.user_data['perfil'].get('monto_minimo_interes', 0)
        if 0 < monto < minimo:
            await update.message.reply_text(
                f"⚠️ El monto máximo (${monto:,}) no puede ser menor al mínimo (${minimo:,}).\n"
                "Por favor ingresa un monto máximo válido.",
                parse_mode='HTML'
            )
            return MONTO_MAX
            
        # Guardar perfil en BD
        exito = db_bot.guardar_perfil(user_id, context.user_data['perfil'])
        
        if exito:
            perfil = context.user_data['perfil']
            mensaje = "✅ <b>¡Perfil guardado exitosamente!</b>\n\n"
            mensaje += f"<b>Empresa:</b> {perfil['nombre_empresa']}\n"
            mensaje += f"<b>Tipo:</b> {perfil['tipo_negocio']}\n"
            mensaje += f"<b>Productos/Servicios:</b> {perfil['productos_servicios']}\n"
            mensaje += f"<b>Palabras clave:</b> {perfil['palabras_clave']}\n"
            mensaje += f"<b>Capacidad de entrega:</b> {perfil['capacidad_entrega_dias']} días\n"
            mensaje += f"<b>Ubicación:</b> {perfil['ubicacion']}\n"
            mensaje += f"<b>Experiencia:</b> {perfil['experiencia_anos']} años\n"
            mensaje += f"<b>Certificaciones:</b> {perfil['certificaciones']}\n"
            mensaje += f"<b>Rango Montos:</b> ${perfil.get('monto_minimo_interes', 0):,} - ${perfil.get('monto_maximo_capacidad', 0):,}\n\n"
            mensaje += "Ahora puedes usar /oportunidades para ver licitaciones recomendadas 🎯"
            
            await update.message.reply_text(mensaje, parse_mode='HTML')
            
            # Registrar interacción
            db_bot.registrar_interaccion(user_id, 'perfil_configurado')
        else:
            await update.message.reply_text(
                "❌ Hubo un error al guardar el perfil. Intenta de nuevo con /configurar_perfil",
                parse_mode='HTML'
            )
        
        return ConversationHandler.END
        
    except ValueError:
        await update.message.reply_text(
            "Por favor escribe solo un número válido (ej: 5000000).",
            parse_mode='HTML'
        )
        return MONTO_MAX


async def cancelar_perfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela la configuración del perfil"""
    await update.message.reply_text(
        "Configuración cancelada. Usa /configurar_perfil cuando quieras configurar tu perfil.",
        parse_mode='HTML'
    )
    return ConversationHandler.END


async def ver_perfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el perfil actual del usuario"""
    user_id = update.effective_user.id
    perfil = db_bot.obtener_perfil(user_id)
    
    if not perfil:
        await update.message.reply_text(
            "❌ No tienes un perfil configurado.\n"
            "Usa /configurar_perfil para crear uno.",
            parse_mode='HTML'
        )
        return
    
    mensaje = "📋 <b>Tu Perfil Empresarial</b>\n\n"
    mensaje += f"<b>Empresa:</b> {perfil['nombre_empresa']}\n"
    mensaje += f"<b>Tipo:</b> {perfil['tipo_negocio']}\n"
    mensaje += f"<b>Productos/Servicios:</b> {perfil['productos_servicios']}\n"
    mensaje += f"<b>Palabras clave:</b> {perfil['palabras_clave']}\n"
    mensaje += f"<b>Capacidad de entrega:</b> {perfil['capacidad_entrega_dias']} días\n"
    mensaje += f"<b>Ubicación:</b> {perfil['ubicacion']}\n"
    mensaje += f"<b>Experiencia:</b> {perfil['experiencia_anos']} años\n"
    mensaje += f"<b>Certificaciones:</b> {perfil['certificaciones']}\n"
    mensaje += f"<b>Rango Montos:</b> ${perfil.get('monto_minimo_interes', 0):,} - ${perfil.get('monto_maximo_capacidad', 0):,}\n"
    mensaje += f"<b>Alertas:</b> {'✅ Activas' if perfil['alertas_activas'] else '❌ Desactivadas'}\n\n"
    
    # Mostrar configuración de score
    p_palabras = {1: 'Baja', 2: 'Media', 3: 'Alta'}.get(perfil.get('peso_palabras', 2), 'Media')
    p_competencia = {1: 'Baja', 2: 'Media', 3: 'Alta'}.get(perfil.get('peso_competencia', 2), 'Media')
    p_monto = {1: 'Baja', 2: 'Media', 3: 'Alta'}.get(perfil.get('peso_monto', 2), 'Media')
    
    mensaje += "<b>📊 Prioridades de Score:</b>\n"
    mensaje += f"• Palabras Clave: <b>{p_palabras}</b>\n"
    mensaje += f"• Competencia: <b>{p_competencia}</b>\n"
    mensaje += f"• Monto: <b>{p_monto}</b>\n\n"
    
    mensaje += "Usa /configurar_perfil para actualizar datos o /configurar_score para ajustar prioridades."
    
    await update.message.reply_text(mensaje, parse_mode='HTML')


# ==================== CONFIGURACIÓN DE SCORE ====================

async def configurar_score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia la configuración de pesos del score"""
    user_id = update.effective_user.id
    perfil = db_bot.obtener_perfil(user_id)
    
    if not perfil:
        await update.message.reply_text("❌ Primero debes crear tu perfil con /configurar_perfil")
        return ConversationHandler.END
        
    keyboard = [
        [InlineKeyboardButton("Baja", callback_data='1'),
         InlineKeyboardButton("Media", callback_data='2'),
         InlineKeyboardButton("Alta", callback_data='3')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📊 <b>Configuración de Score</b>\n\n"
        "Vamos a ajustar qué tan importante es cada factor para ti.\n\n"
        "1️⃣ <b>Coincidencia de Palabras Clave</b>\n"
        "¿Qué tanta importancia le das a que las palabras coincidan exactamente?",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return PESO_PALABRAS

async def recibir_peso_palabras(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    peso = int(query.data)
    context.user_data['score_config'] = {'peso_palabras': peso}
    
    niveles = {1: 'Baja', 2: 'Media', 3: 'Alta'}
    
    keyboard = [
        [InlineKeyboardButton("Baja", callback_data='1'),
         InlineKeyboardButton("Media", callback_data='2'),
         InlineKeyboardButton("Alta", callback_data='3')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ Palabras Clave: <b>{niveles[peso]}</b>\n\n"
        "2️⃣ <b>Baja Competencia</b>\n"
        "¿Qué tan importante es que haya POCOS competidores cotizando?",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return PESO_COMPETENCIA

async def recibir_peso_competencia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    peso = int(query.data)
    context.user_data['score_config']['peso_competencia'] = peso
    
    niveles = {1: 'Baja', 2: 'Media', 3: 'Alta'}
    
    keyboard = [
        [InlineKeyboardButton("Baja", callback_data='1'),
         InlineKeyboardButton("Media", callback_data='2'),
         InlineKeyboardButton("Alta", callback_data='3')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ Competencia: <b>{niveles[peso]}</b>\n\n"
        "3️⃣ <b>Monto Ideal</b>\n"
        "¿Qué tan importante es que el monto esté dentro de tu rango?",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    return PESO_MONTO

async def recibir_peso_monto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    peso = int(query.data)
    context.user_data['score_config']['peso_monto'] = peso
    
    # Guardar en BD
    user_id = update.effective_user.id
    perfil = db_bot.obtener_perfil(user_id)
    
    # Actualizar solo los pesos
    perfil['peso_palabras'] = context.user_data['score_config']['peso_palabras']
    perfil['peso_competencia'] = context.user_data['score_config']['peso_competencia']
    perfil['peso_monto'] = context.user_data['score_config']['peso_monto']
    
    db_bot.guardar_perfil(user_id, perfil)
    
    niveles = {1: 'Baja', 2: 'Media', 3: 'Alta'}
    p_palabras = niveles[perfil['peso_palabras']]
    p_competencia = niveles[perfil['peso_competencia']]
    p_monto = niveles[perfil['peso_monto']]
    
    await query.edit_message_text(
        "✅ <b>¡Configuración Guardada!</b>\n\n"
        "Tus nuevas prioridades de Score:\n"
        f"• Palabras Clave: <b>{p_palabras}</b>\n"
        f"• Competencia: <b>{p_competencia}</b>\n"
        f"• Monto: <b>{p_monto}</b>\n\n"
        "Ahora los resultados de /oportunidades se adaptarán a esto. 🚀",
        parse_mode='HTML'
    )
    return ConversationHandler.END


if __name__ == '__main__':
    if not TOKEN:
        print("Error: No encontré el Token en el archivo .env")
        exit()
    
    if not GEMINI_API_KEY:
        print("⚠️ Advertencia: GEMINI_API_KEY no encontrada. El análisis de IA no funcionará.")
    
    # Inicializar base de datos
    db.iniciar_db_extendida()
    db_bot.iniciar_db_bot()
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Handler para configuración de perfil
    perfil_handler = ConversationHandler(
        entry_points=[CommandHandler('configurar_perfil', configurar_perfil)],
        states={
            NOMBRE_EMPRESA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre_empresa)],
            TIPO_NEGOCIO: [CallbackQueryHandler(recibir_tipo_negocio)],
            PRODUCTOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_productos)],
            PALABRAS_CLAVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_palabras_clave)],
            CAPACIDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_capacidad)],
            UBICACION: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_ubicacion)],
            EXPERIENCIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_experiencia)],
            CERTIFICACIONES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_certificaciones)],
            MONTO_MIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_monto_min)],
            MONTO_MAX: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_monto_max)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar_perfil)]
    )
    
    # Registrar handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('perfil', ver_perfil))
    application.add_handler(perfil_handler)
    
    print("🤖 Bot Inteligente escuchando...")
    print(f"✅ Gemini AI: {'Configurado' if GEMINI_API_KEY else 'No configurado'}")
    application.run_polling()
