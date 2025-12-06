"""
Bot de Telegram Inteligente para Compra Ágil - VERSIÓN COMPLETA
Incluye análisis con Gemini AI, perfiles de empresa y búsquedas avanzadas.

Para ejecutar:
1. Configura TELEGRAM_TOKEN y GEMINI_API_KEY en .env
2. python bot_inteligente.py
"""
import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    ConversationHandler, MessageHandler, filters, CallbackQueryHandler
)

# Importar módulos del proyecto
import database_extended as db
import database_bot as db_bot
import ml_utils
import reportes

# Importar funciones de las partes del bot
from bot_inteligente_parte1 import (
    start, configurar_perfil, recibir_nombre_empresa, recibir_tipo_negocio,
    recibir_productos, recibir_palabras_clave, recibir_capacidad,
    recibir_ubicacion, recibir_experiencia, recibir_certificaciones,
    recibir_monto_min, recibir_monto_max,
    configurar_score, recibir_peso_palabras, recibir_peso_competencia, recibir_peso_monto,
    cancelar_perfil, ver_perfil,
    NOMBRE_EMPRESA, TIPO_NEGOCIO, PRODUCTOS, PALABRAS_CLAVE,
    CAPACIDAD, UBICACION, EXPERIENCIA, CERTIFICACIONES,
    MONTO_MIN, MONTO_MAX,
    PESO_PALABRAS, PESO_COMPETENCIA, PESO_MONTO
)
from bot_inteligente_parte2 import (
    buscar, oportunidades, urgentes, por_monto, analizar,
    mostrar_pagina, exportar_excel, detalle_licitacion
)
from bot_inteligente_parte3 import (
    guardar_licitacion, mis_guardadas, eliminar_guardada,
    ayuda_cotizar, recomendar, alertas_on, alertas_off, stats,
    redactar_oferta, ejecutar_redaccion
)
from subscription_commands import upgrade, mi_plan

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Configurar logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Función principal del bot"""
    
    if not TOKEN:
        logger.error("❌ Error: TELEGRAM_TOKEN no encontrado en .env")
        print("❌ Error: No encontré el Token en el archivo .env")
        print("Por favor configura TELEGRAM_TOKEN en tu archivo .env")
        return
    
    if not GEMINI_API_KEY:
        logger.warning("⚠️ GEMINI_API_KEY no encontrada. El análisis de IA no funcionará.")
        print("⚠️ Advertencia: GEMINI_API_KEY no encontrada en .env")
        print("El bot funcionará pero sin análisis de IA.")
        print("Configura GEMINI_API_KEY para habilitar el análisis inteligente.")
    
    # Inicializar base de datos
    print("📊 Inicializando base de datos...")
    db.iniciar_db_extendida()
    db_bot.iniciar_db_bot()
    
    # Crear aplicación
    application = ApplicationBuilder().token(TOKEN).build()
    
    # ==================== HANDLERS ====================
    
    # Handler para configuración de perfil (ConversationHandler)
    perfil_handler = ConversationHandler(
        entry_points=[CommandHandler('configurar_perfil', configurar_perfil)],
        states={
            NOMBRE_EMPRESA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre_empresa)],
            TIPO_NEGOCIO: [CallbackQueryHandler(recibir_tipo_negocio)],
            PRODUCTOS: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_productos)],
            PALABRAS_CLAVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_palabras_clave)],
            CAPACIDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_capacidad)],
            UBICACION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_ubicacion),
                CallbackQueryHandler(recibir_ubicacion)
            ],
            EXPERIENCIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_experiencia)],
            CERTIFICACIONES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_certificaciones)],
            MONTO_MIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_monto_min)],
            MONTO_MAX: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_monto_max)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar_perfil)]
    )
    
    # Handler para configuración de score (ConversationHandler)
    score_handler = ConversationHandler(
        entry_points=[CommandHandler('configurar_score', configurar_score)],
        states={
            PESO_PALABRAS: [CallbackQueryHandler(recibir_peso_palabras)],
            PESO_COMPETENCIA: [CallbackQueryHandler(recibir_peso_competencia)],
            PESO_MONTO: [CallbackQueryHandler(recibir_peso_monto)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar_perfil)]
    )
    
    # Comandos básicos
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('perfil', ver_perfil))
    application.add_handler(perfil_handler)
    application.add_handler(score_handler)
    
    # Comandos de búsqueda
    application.add_handler(CommandHandler('buscar', buscar))
    application.add_handler(CommandHandler('oportunidades', oportunidades))
    application.add_handler(CommandHandler('urgentes', urgentes))
    application.add_handler(CommandHandler('por_monto', por_monto))
    
    # Comandos de análisis con IA
    application.add_handler(CommandHandler('analizar', analizar))
    application.add_handler(CommandHandler('detalle', detalle_licitacion))
    application.add_handler(CommandHandler('recomendar', recomendar))
    application.add_handler(CommandHandler('ayuda_cotizar', ayuda_cotizar))
    application.add_handler(CommandHandler('redactar_oferta', redactar_oferta))
    
    # Comandos de licitaciones guardadas
    application.add_handler(CommandHandler('guardar', guardar_licitacion))
    application.add_handler(CommandHandler('mis_guardadas', mis_guardadas))
    application.add_handler(CommandHandler('eliminar_guardada', eliminar_guardada))
    
    # Comandos de alertas
    application.add_handler(CommandHandler('alertas_on', alertas_on))
    application.add_handler(CommandHandler('alertas_off', alertas_off))
    
    # Estadísticas
    application.add_handler(CommandHandler('stats', stats))
    
    # ML - Optimización de perfil
    application.add_handler(CommandHandler('optimizar_perfil', optimizar_perfil))
    
    # ML - Alertas de competencia
    application.add_handler(CommandHandler('check_alertas', check_alertas))
    
    # Reportes Admin
    application.add_handler(CommandHandler('reporte', reporte))
    application.add_handler(CommandHandler('exportar_reporte', exportar_reporte))
    
    # Comandos de Suscripción (Monetización)
    application.add_handler(CommandHandler('upgrade', upgrade))
    application.add_handler(CommandHandler('mi_plan', mi_plan))
    
    # Handler genérico de botones (para analizar, guardar, ayuda)
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Iniciar bot
    print("\n" + "="*60)
    print("🤖 BOT INTELIGENTE DE COMPRA ÁGIL")
    print("="*60)
    print(f"✅ Bot iniciado correctamente")
    print(f"✅ Base de datos: Configurada")
    print(f"{'✅' if GEMINI_API_KEY else '❌'} Gemini AI: {'Configurado' if GEMINI_API_KEY else 'No configurado'}")
    print(f"\n📱 El bot está escuchando mensajes...")
    print(f"💡 Presiona Ctrl+C para detener\n")
    print("="*60 + "\n")
    
    # Ejecutar bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


async def reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera un reporte de inteligencia de mercado"""
    user_id = update.effective_user.id
    # Aquí podrías validar si el usuario es admin, por ahora abierto
    
    await update.message.reply_text("📊 Generando reporte de inteligencia de mercado...")
    
    try:
        # Datos de competencia
        comp_data = reportes.generar_reporte_competencia()
        mercado_data = reportes.generar_reporte_mercado()
        
        mensaje = "🏆 <b>TOP COMPETIDORES (Ganadores)</b>\n"
        for i, (nombre, total) in enumerate(comp_data['top_ganadores'], 1):
            mensaje += f"{i}. {nombre}: <b>{total}</b> adjudicaciones\n"
            
        mensaje += "\n🦈 <b>TOP PARTICIPATIVOS (Más ofertas)</b>\n"
        for i, (nombre, total) in enumerate(comp_data['top_participativos'], 1):
            mensaje += f"{i}. {nombre}: <b>{total}</b> ofertas\n"
            
        mensaje += "\n📈 <b>ESTADÍSTICAS DE MERCADO</b>\n"
        mensaje += f"💰 Promedio Adjudicado: <b>${mercado_data['promedio_adjudicado']:,}</b>\n"
        
        mensaje += "\n🏢 <b>Organismos más activos:</b>\n"
        for org, total in mercado_data['top_organismos']:
            mensaje += f"• {org}: {total}\n"
            
        await update.message.reply_text(mensaje, parse_mode='HTML')
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error al generar reporte: {e}")


async def exportar_reporte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera y envía un reporte Excel"""
    user_id = update.effective_user.id
    
    await update.message.reply_text("📊 Generando archivo Excel... (esto puede tomar unos segundos)")
    
    try:
        excel_file = reportes.generar_excel_mercado()
        
        from datetime import datetime
        fecha = datetime.now().strftime("%Y-%m-%d")
        filename = f"reporte_mercado_{fecha}.xlsx"
        
        await update.message.reply_document(
            document=excel_file,
            filename=filename,
            caption=f"📊 Reporte de Mercado - {fecha}"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error al exportar: {e}")


async def check_alertas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Verifica si hay oportunidades de baja competencia"""
    user_id = update.effective_user.id
    
    # Obtener perfil
    perfil = db_bot.obtener_perfil(user_id)
    if not perfil:
        await update.message.reply_text("❌ Primero configura tu perfil con /configurar_perfil")
        return
        
    await update.message.reply_text("🕵️ Buscando oportunidades de baja competencia...")
    
    oportunidades = filtros.buscar_oportunidades_baja_competencia(perfil, dias=3, max_competencia=2)
    
    if not oportunidades:
        await update.message.reply_text(
            "✅ No encontré licitaciones urgentes con baja competencia por ahora.\n"
            "¡Eso es bueno! Significa que no te estás perdiendo nada obvio."
        )
        return
        
    await update.message.reply_text(
        f"🚀 <b>¡Encontré {len(oportunidades)} oportunidades!</b>\n"
        "Estas licitaciones cierran pronto y tienen poca competencia:",
        parse_mode='HTML'
    )
    
    for lic in oportunidades:
        competencia = lic.get('cantidad_proveedores_cotizando', 0)
        texto = f"🔥 <b>{lic['nombre'][:80]}...</b>\n"
        texto += f"💰 ${lic['monto_disponible']:,} {lic['moneda']}\n"
        texto += f"👥 Competencia: <b>{competencia} ofertas</b>\n"
        texto += f"📅 Cierre: {lic['fecha_cierre']}\n"
        
        keyboard = [[
            InlineKeyboardButton("Analizar 🤖", callback_data=f"analizar_{lic['codigo']}"),
            InlineKeyboardButton("🌐 Ver", url=f"https://buscador.mercadopublico.cl/ficha?code={lic['codigo']}")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(texto, reply_markup=reply_markup, parse_mode='HTML')


async def optimizar_perfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analiza likes y sugiere mejoras al perfil"""
    user_id = update.effective_user.id
    
    await update.message.reply_text("🧠 Analizando tus preferencias...")
    
    sugerencias = ml_utils.analizar_preferencias(user_id)
    
    if not sugerencias:
        await update.message.reply_text(
            "No tengo suficientes datos para sugerirte cambios aún.\n"
            "Sigue dando 👍 a las licitaciones que te interesen."
        )
        return
        
    texto_sugerencias = ", ".join(sugerencias)
    
    keyboard = [[
        InlineKeyboardButton("✅ Agregar sugerencias", callback_data=f"agregar_sugerencias_{texto_sugerencias}")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"💡 He notado que te interesan estas palabras:\n\n"
        f"<b>{texto_sugerencias}</b>\n\n"
        f"¿Quieres agregarlas a tu perfil?",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja las interacciones con botones inline"""
    query = update.callback_query
    await query.answer() # Confirmar recepción
    
    data = query.data
    
    # Extraer acción y código
    if data.startswith('feedback_like_'):
        codigo = data.replace('feedback_like_', '')
        db_bot.registrar_feedback(update.effective_user.id, codigo, 1)
        await query.edit_message_reply_markup(reply_markup=None) # Quitar botones
        await update.effective_message.reply_text(f"👍 ¡Gracias! Tendré en cuenta que te gusta esta licitación ({codigo}).")
        
    elif data.startswith('feedback_dislike_'):
        codigo = data.replace('feedback_dislike_', '')
        db_bot.registrar_feedback(update.effective_user.id, codigo, 0)
        await query.edit_message_reply_markup(reply_markup=None) # Quitar botones
        await update.effective_message.reply_text(f"👎 ¡Entendido! Evitaré recomendarte licitaciones similares a ({codigo}).")

    elif data == 'show_upgrade':
        # NUEVO: Mostrar planes cuando el usuario hace click en upgrade
        from subscription_commands import upgrade
        # Simular que viene del comando directamente
        await upgrade(update, context)
    elif data.startswith('agregar_sugerencias_'):
        nuevas_palabras = data.replace('agregar_sugerencias_', '')
        user_id = update.effective_user.id
        
        # Obtener perfil actual
        perfil = db_bot.obtener_perfil(user_id)
        if perfil:
            palabras_actuales = perfil['palabras_clave']
            if palabras_actuales:
                palabras_finales = f"{palabras_actuales}, {nuevas_palabras}"
            else:
                palabras_finales = nuevas_palabras
            
            # Actualizar solo palabras clave
            perfil['palabras_clave'] = palabras_finales
            db_bot.guardar_perfil(user_id, perfil)
            
            await query.edit_message_reply_markup(reply_markup=None)
            await update.effective_message.reply_text(
                f"✅ ¡Perfil actualizado!\n"
                f"Nuevas palabras clave: <b>{palabras_finales}</b>",
                parse_mode='HTML'
            )

    elif data.startswith('ayuda_'):
        codigo = data.replace('ayuda_', '')
        context.args = [codigo]
        await ayuda_cotizar(update, context)
        
    elif data.startswith('guardar_'):
        codigo = data.replace('guardar_', '')
        context.args = [codigo]
        await guardar_licitacion(update, context)
        
    elif data.startswith('analizar_'):
        codigo = data.replace('analizar_', '')
        context.args = [codigo]
        await analizar(update, context)
        
    elif data.startswith('detalle_'):
        codigo = data.replace('detalle_', '')
        context.args = [codigo]
        await detalle_licitacion(update, context)
        
    elif data.startswith('redactar_'):
        # Formato: redactar_TIPO_CODIGO
        parts = data.split('_')
        if len(parts) >= 3:
            tipo = parts[1] # texto, pdf, correo
            codigo = parts[2]
            await ejecutar_redaccion(update, context, codigo, tipo)
        
    # Paginación y Exportación
    elif data == 'pag_ant':
        busqueda = context.user_data.get('busqueda_actual')
        if busqueda and busqueda['pagina'] > 0:
            busqueda['pagina'] -= 1
            await mostrar_pagina(update, context)
            
    elif data == 'pag_sig':
        busqueda = context.user_data.get('busqueda_actual')
        if busqueda:
            total_paginas = (busqueda['total'] + 5 - 1) // 5
            if busqueda['pagina'] < total_paginas - 1:
                busqueda['pagina'] += 1
                await mostrar_pagina(update, context)
                
    elif data == 'exportar_excel':
        await exportar_excel(update, context)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
        print(f"\n❌ Error fatal: {e}")
