"""
Bot de Telegram mejorado para Compra Ágil
Incluye comandos para buscar licitaciones y ver detalles completos
Usa botones inline para mejor experiencia de usuario
"""
import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
import database_extended as db
import api_client
import sqlite3

# Cargar variables de entorno (.env)
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')

# Configurar logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Muestra ayuda"""
    await update.message.reply_text(
        "¡Hola! Soy el Bot de Compra Ágil 🤖\n\n"
        "Comandos disponibles:\n"
        "📋 /buscar [palabra] - Busca licitaciones\n"
        "🔍 /detalle [código] - Ver detalles completos\n"
        "📊 /stats - Estadísticas de la base de datos\n\n"
        "Ejemplos:\n"
        "/buscar computadores\n"
        "/detalle 1057389-2539-COT25"
    )


async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /buscar - Busca licitaciones por palabra clave"""
    if not context.args:
        await update.message.reply_text("⚠️ Por favor escribe qué buscar. Ej: /buscar computadores")
        return

    palabra = " ".join(context.args)
    await update.message.reply_text(f"🔍 Buscando '{palabra}' en la base de datos...")

    resultados = db.buscar_por_palabra(palabra)

    if not resultados:
        await update.message.reply_text("No encontré nada reciente con ese nombre. 😔")
    else:
        await update.message.reply_text(f"✅ Encontré {len(resultados)} coincidencias:")
        
        # Enviar cada resultado con su botón
        for row in resultados:
            # row es (codigo, nombre, organismo, fecha_cierre)
            codigo = row[0]
            nombre = row[1][:80]
            organismo = row[2]
            fecha_cierre = row[3]
            
            # Crear botón para ver detalles
            keyboard = [[InlineKeyboardButton("🔍 Ver Detalles", callback_data=f"detalle_{codigo}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            mensaje = f"📄 <b>{nombre}</b>\n" \
                     f"🏢 {organismo}\n" \
                     f"🆔 <code>{codigo}</code>\n" \
                     f"📅 Cierre: {fecha_cierre}"
            
            await update.message.reply_text(
                mensaje,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los callbacks de los botones inline"""
    query = update.callback_query
    await query.answer()
    
    # Extraer el código de la licitación del callback_data
    if query.data.startswith("detalle_"):
        codigo = query.data.replace("detalle_", "")
        
        # Editar el mensaje para mostrar que está cargando
        await query.edit_message_text(f"🔍 Cargando detalles de {codigo}...")
        
        # Buscar y mostrar detalles
        await mostrar_detalle(query.message, codigo)


async def detalle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /detalle - Muestra detalles completos de una licitación"""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Por favor proporciona el código de la licitación.\n"
            "Ejemplo: /detalle 1057389-2539-COT25"
        )
        return

    codigo = context.args[0]
    await update.message.reply_text(f"🔍 Buscando detalles de {codigo}...")
    
    await mostrar_detalle(update.message, codigo)


async def mostrar_detalle(message, codigo):
    """Muestra los detalles de una licitación"""
    # Primero buscar en la base de datos
    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM licitaciones_detalle WHERE codigo = ?
    ''', (codigo,))
    
    detalle_db = cursor.fetchone()
    
    if detalle_db:
        # Tenemos los detalles en la BD
        await enviar_detalle_desde_db(message, codigo, cursor)
    else:
        # No está en la BD, obtener de la API
        await message.reply_text("📡 Obteniendo información desde la API...")
        
        ficha = api_client.obtener_ficha_detalle(codigo)
        
        if ficha:
            # Guardar en BD para futuras consultas
            historial = api_client.obtener_historial(codigo)
            adjuntos = api_client.obtener_adjuntos(codigo)
            db.guardar_detalle_completo(codigo, ficha, historial, adjuntos)
            
            await enviar_detalle_desde_ficha(message, ficha, historial, adjuntos)
        else:
            await message.reply_text(
                f"❌ No se encontró la licitación {codigo}\n"
                "Verifica que el código sea correcto."
            )
    
    conn.close()


async def enviar_detalle_desde_db(message, codigo, cursor):
    """Envía los detalles de una licitación desde la base de datos"""
    cursor.execute('SELECT * FROM licitaciones_detalle WHERE codigo = ?', (codigo,))
    row = cursor.fetchone()
    
    if not row:
        await message.reply_text("❌ No se encontraron detalles")
        return
    
    # Construir mensaje con los detalles
    mensaje = f"📋 <b>{row[2]}</b>\n\n"  # nombre
    mensaje += f"🆔 Código: <code>{codigo}</code>\n"
    mensaje += f"📝 Descripción: {row[3][:200] if row[3] else 'N/A'}...\n\n"
    mensaje += f"🏢 Organismo: {row[14]}\n"  # organismo_comprador
    mensaje += f"📍 RUT: {row[15]}\n"  # rut_organismo_comprador
    mensaje += f"🏛️ División: {row[16]}\n\n"  # division
    mensaje += f"💰 Presupuesto: ${row[10]:,} {row[11]}\n"  # presupuesto_estimado, moneda
    mensaje += f"📅 Publicación: {row[4]}\n"  # fecha_publicacion
    mensaje += f"⏰ Cierre: {row[5]}\n"  # fecha_cierre
    mensaje += f"📦 Plazo entrega: {row[9]} días\n\n"  # plazo_entrega
    
    # Productos
    cursor.execute('SELECT * FROM productos_solicitados WHERE codigo_licitacion = ?', (codigo,))
    productos = cursor.fetchall()
    
    if productos:
        mensaje += f"📦 <b>Productos solicitados ({len(productos)}):</b>\n"
        for prod in productos[:3]:  # Mostrar máximo 3
            mensaje += f"  • {prod[2]} - {prod[4]} {prod[5]}\n"  # nombre, cantidad, unidad
        if len(productos) > 3:
            mensaje += f"  ... y {len(productos) - 3} más\n"
    
    # Adjuntos
    cursor.execute('SELECT * FROM adjuntos WHERE codigo_licitacion = ?', (codigo,))
    adjuntos = cursor.fetchall()
    
    if adjuntos:
        mensaje += f"\n📎 <b>Adjuntos ({len(adjuntos)}):</b>\n"
        for adj in adjuntos[:3]:
            mensaje += f"  • {adj[2]}\n"  # nombre_archivo
        if len(adjuntos) > 3:
            mensaje += f"  ... y {len(adjuntos) - 3} más\n"
    
    mensaje += f"\n🔗 <a href='https://buscador.mercadopublico.cl/ficha?code={codigo}'>Ver en Mercado Público</a>"
    
    await message.reply_text(mensaje, parse_mode='HTML', disable_web_page_preview=True)


async def enviar_detalle_desde_ficha(message, ficha, historial, adjuntos):
    """Envía los detalles de una licitación desde la ficha de la API"""
    codigo = ficha.get('codigo')
    info_inst = ficha.get('informacion_institucion', {})
    
    mensaje = f"📋 <b>{ficha.get('nombre')}</b>\n\n"
    mensaje += f"🆔 Código: <code>{codigo}</code>\n"
    
    desc = ficha.get('descripcion', '')
    if desc:
        mensaje += f"📝 Descripción: {desc[:200]}...\n\n"
    
    mensaje += f"🏢 Organismo: {info_inst.get('organismo_comprador')}\n"
    mensaje += f"📍 RUT: {info_inst.get('rut_organismo_comprador')}\n"
    mensaje += f"🏛️ División: {info_inst.get('division')}\n\n"
    
    presupuesto = ficha.get('presupuesto_estimado')
    if presupuesto:
        mensaje += f"💰 Presupuesto: ${presupuesto:,} {ficha.get('moneda')}\n"
    
    mensaje += f"📅 Publicación: {ficha.get('fecha_publicacion')}\n"
    mensaje += f"⏰ Cierre: {ficha.get('fecha_cierre')}\n"
    mensaje += f"📦 Plazo entrega: {ficha.get('plazo_entrega')} días\n\n"
    
    # Productos
    productos = ficha.get('productos_solicitados', [])
    if productos:
        mensaje += f"📦 <b>Productos solicitados ({len(productos)}):</b>\n"
        for prod in productos[:3]:
            mensaje += f"  • {prod.get('nombre')} - {prod.get('cantidad')} {prod.get('unidad_medida')}\n"
        if len(productos) > 3:
            mensaje += f"  ... y {len(productos) - 3} más\n"
    
    # Adjuntos
    if adjuntos:
        mensaje += f"\n📎 <b>Adjuntos ({len(adjuntos)}):</b>\n"
        for adj in adjuntos[:3]:
            mensaje += f"  • {adj.get('nombreArchivo')}\n"
        if len(adjuntos) > 3:
            mensaje += f"  ... y {len(adjuntos) - 3} más\n"
    
    mensaje += f"\n🔗 <a href='https://buscador.mercadopublico.cl/ficha?code={codigo}'>Ver en Mercado Público</a>"
    
    await message.reply_text(mensaje, parse_mode='HTML', disable_web_page_preview=True)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /stats - Muestra estadísticas de la base de datos"""
    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    
    # Total de licitaciones
    cursor.execute('SELECT COUNT(*) FROM licitaciones')
    total_licitaciones = cursor.fetchone()[0]
    
    # Licitaciones con detalle
    cursor.execute('SELECT COUNT(*) FROM licitaciones WHERE detalle_obtenido = 1')
    con_detalle = cursor.fetchone()[0]
    
    # Total de productos
    cursor.execute('SELECT COUNT(*) FROM productos_solicitados')
    total_productos = cursor.fetchone()[0]
    
    # Total de adjuntos
    cursor.execute('SELECT COUNT(*) FROM adjuntos')
    total_adjuntos = cursor.fetchone()[0]
    
    conn.close()
    
    mensaje = "📊 <b>Estadísticas de la Base de Datos</b>\n\n"
    mensaje += f"📋 Total de licitaciones: {total_licitaciones}\n"
    mensaje += f"✅ Con detalles completos: {con_detalle}\n"
    mensaje += f"⏳ Pendientes de detalle: {total_licitaciones - con_detalle}\n\n"
    mensaje += f"📦 Total de productos: {total_productos}\n"
    mensaje += f"📎 Total de adjuntos: {total_adjuntos}\n"
    
    await update.message.reply_text(mensaje, parse_mode='HTML')


if __name__ == '__main__':
    if not TOKEN:
        print("Error: No encontré el Token en el archivo .env")
        exit()
    
    # Inicializar base de datos
    db.iniciar_db_extendida()
    
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Registrar comandos
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('buscar', buscar))
    application.add_handler(CommandHandler('detalle', detalle))
    application.add_handler(CommandHandler('stats', stats))
    
    # Registrar handler para botones inline
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("🤖 Bot escuchando...")
    application.run_polling()