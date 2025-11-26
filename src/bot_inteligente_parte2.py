"""
Bot Inteligente - Parte 2: Comandos de Búsqueda y Análisis
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database_bot as db_bot
import database_extended as db
import filtros
import gemini_ai
import api_client


# ==================== BÚSQUEDAS ====================

async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Busca licitaciones por palabra clave"""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Uso: /buscar [palabra clave]\n"
            "Ejemplo: /buscar sillas",
            parse_mode='HTML'
        )
        return
    
    palabra = " ".join(context.args)
    await update.message.reply_text(f"🔍 Buscando '{palabra}'...")
    
    resultados = filtros.buscar_por_palabras_clave(palabra, limite=10)
    
    if not resultados:
        await update.message.reply_text(
            f"No encontré licitaciones con '{palabra}' 😔\n"
            "Intenta con otras palabras clave.",
            parse_mode='HTML'
        )
        return
    
    mensaje = f"📋 Encontré <b>{len(resultados)}</b> licitaciones:\n\n"
    
    for lic in resultados:
        mensaje += f"📄 <b>{lic['nombre'][:80]}...</b>\n"
        mensaje += f"🏢 {lic['organismo']}\n"
        mensaje += f"💰 ${lic['monto_disponible']:,} {lic['moneda']}\n"
        mensaje += f"📅 Cierre: {lic['fecha_cierre']}\n"
        mensaje += f"👥 Cotizando: {lic['cantidad_proveedores_cotizando']}\n"
        mensaje += f"🔗 /analizar {lic['codigo']}\n\n"
    
    await update.message.reply_text(mensaje, parse_mode='HTML')
    
    # Registrar búsqueda
    db_bot.registrar_interaccion(update.effective_user.id, 'busqueda', palabra)


async def oportunidades(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra licitaciones compatibles con el perfil del usuario"""
    user_id = update.effective_user.id
    perfil = db_bot.obtener_perfil(user_id)
    
    if not perfil:
        await update.message.reply_text(
            "❌ Primero configura tu perfil con /configurar_perfil\n"
            "Así podré recomendarte las mejores licitaciones.",
            parse_mode='HTML'
        )
        return
    
    await update.message.reply_text("🔍 Buscando oportunidades para ti...")
    
    # Buscar licitaciones compatibles
    licitaciones = filtros.buscar_compatibles_con_perfil(perfil, limite=10)
    
    if not licitaciones:
        await update.message.reply_text(
            "😔 No encontré licitaciones compatibles en este momento.\n"
            "Intenta actualizar tus palabras clave en /configurar_perfil",
            parse_mode='HTML'
        )
        return
    
    mensaje = f"🎯 <b>Oportunidades para {perfil['nombre_empresa']}</b>\n\n"
    
    for lic in licitaciones:
        # Calcular score simple
        score = filtros.calcular_score_compatibilidad_simple(lic, perfil)
        
        emoji_score = "🟢" if score >= 70 else "🟡" if score >= 40 else "🔴"
        
        mensaje += f"{emoji_score} <b>Score: {score}/100</b>\n"
        mensaje += f"📄 {lic['nombre'][:70]}...\n"
        mensaje += f"🏢 {lic['organismo']}\n"
        mensaje += f"💰 ${lic['monto_disponible']:,} {lic['moneda']}\n"
        mensaje += f"📅 Cierre: {lic['fecha_cierre']}\n"
        mensaje += f"🔗 /analizar {lic['codigo']}\n\n"
    
    await update.message.reply_text(mensaje, parse_mode='HTML')
    db_bot.registrar_interaccion(user_id, 'oportunidades')


async def urgentes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra licitaciones que cierran pronto"""
    dias = 3
    if context.args:
        try:
            dias = int(context.args[0])
        except ValueError:
            pass
    
    await update.message.reply_text(f"⏰ Buscando licitaciones que cierran en {dias} días...")
    
    licitaciones = filtros.buscar_urgentes(dias=dias, limite=10)
    
    if not licitaciones:
        await update.message.reply_text(
            f"✅ No hay licitaciones cerrando en los próximos {dias} días.",
            parse_mode='HTML'
        )
        return
    
    mensaje = f"⚠️ <b>{len(licitaciones)} licitaciones urgentes</b>\n"
    mensaje += f"(Cierran en {dias} días o menos)\n\n"
    
    for lic in licitaciones:
        mensaje += f"📄 <b>{lic['nombre'][:70]}...</b>\n"
        mensaje += f"🏢 {lic['organismo']}\n"
        mensaje += f"💰 ${lic['monto_disponible']:,} {lic['moneda']}\n"
        mensaje += f"⏰ <b>Cierre: {lic['fecha_cierre']}</b>\n"
        mensaje += f"🔗 /analizar {lic['codigo']}\n\n"
    
    await update.message.reply_text(mensaje, parse_mode='HTML')
    db_bot.registrar_interaccion(update.effective_user.id, 'urgentes')


async def por_monto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Busca licitaciones por rango de monto"""
    if len(context.args) < 2:
        await update.message.reply_text(
            "⚠️ Uso: /por_monto [mínimo] [máximo]\n"
            "Ejemplo: /por_monto 500000 2000000\n"
            "(Montos en CLP)",
            parse_mode='HTML'
        )
        return
    
    try:
        monto_min = int(context.args[0])
        monto_max = int(context.args[1])
        
        await update.message.reply_text(
            f"🔍 Buscando licitaciones entre ${monto_min:,} y ${monto_max:,}..."
        )
        
        licitaciones = filtros.buscar_por_monto(monto_min, monto_max, limite=10)
        
        if not licitaciones:
            await update.message.reply_text(
                "No encontré licitaciones en ese rango de monto.",
                parse_mode='HTML'
            )
            return
        
        mensaje = f"💰 <b>{len(licitaciones)} licitaciones encontradas</b>\n\n"
        
        for lic in licitaciones:
            mensaje += f"📄 <b>{lic['nombre'][:70]}...</b>\n"
            mensaje += f"🏢 {lic['organismo']}\n"
            mensaje += f"💰 ${lic['monto_disponible']:,} {lic['moneda']}\n"
            mensaje += f"📅 Cierre: {lic['fecha_cierre']}\n"
            mensaje += f"🔗 /analizar {lic['codigo']}\n\n"
        
        await update.message.reply_text(mensaje, parse_mode='HTML')
        db_bot.registrar_interaccion(update.effective_user.id, 'por_monto')
        
    except ValueError:
        await update.message.reply_text(
            "❌ Los montos deben ser números.\n"
            "Ejemplo: /por_monto 500000 2000000",
            parse_mode='HTML'
        )


# ==================== ANÁLISIS CON IA ====================

async def analizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analiza una licitación con Gemini AI"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.effective_message.reply_text(
            "⚠️ Uso: /analizar [código]\n"
            "Ejemplo: /analizar 1057389-2539-COT25",
            parse_mode='HTML'
        )
        return
    
    codigo = context.args[0]
    
    # Verificar perfil
    perfil = db_bot.obtener_perfil(user_id)
    if not perfil:
        await update.effective_message.reply_text(
            "❌ Primero configura tu perfil con /configurar_perfil\n"
            "El análisis se personaliza según tu empresa.",
            parse_mode='HTML'
        )
        return
    
    await update.effective_message.reply_text(
        f"🤖 Analizando licitación {codigo}...\n"
        "Esto puede tomar unos segundos.",
        parse_mode='HTML'
    )
    
    # Buscar licitación en BD
    conn = db.sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, codigo, nombre, fecha_publicacion, fecha_cierre, organismo, 
               unidad, estado, monto_disponible, moneda, cantidad_proveedores_cotizando
        FROM licitaciones WHERE codigo = ?
    ''', (codigo,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        await update.effective_message.reply_text(
            f"❌ No encontré la licitación {codigo}\n"
            "Verifica el código e intenta de nuevo.",
            parse_mode='HTML'
        )
        return
    
    licitacion = dict(zip(['id', 'codigo', 'nombre', 'fecha_publicacion', 'fecha_cierre',
                          'organismo', 'unidad', 'estado', 'monto_disponible', 'moneda',
                          'cantidad_proveedores_cotizando'], row))
    
    # Obtener productos si existen
    cursor.execute('''
        SELECT nombre, cantidad, unidad_medida
        FROM productos_solicitados WHERE codigo_licitacion = ?
    ''', (codigo,))
    productos = [dict(zip(['nombre', 'cantidad', 'unidad_medida'], p)) for p in cursor.fetchall()]
    conn.close()
    
    # Verificar caché
    analisis = db_bot.obtener_analisis_cache(codigo)
    
    if not analisis:
        # Analizar con IA
        analisis = gemini_ai.analizar_licitacion_completo(licitacion, perfil, productos)
        # Guardar en caché
        db_bot.guardar_analisis_cache(codigo, analisis)
    
    # Formatear respuesta
    mensaje = f"🤖 <b>Análisis de Licitación</b>\n\n"
    mensaje += f"📄 <b>{licitacion['nombre']}</b>\n"
    mensaje += f"🏢 {licitacion['organismo']}\n"
    mensaje += f"💰 ${licitacion['monto_disponible']:,} {licitacion['moneda']}\n\n"
    
    # Compatibilidad
    comp = analisis.get('compatibilidad', {})
    score = comp.get('score', 0)
    emoji = "🟢" if score >= 70 else "🟡" if score >= 40 else "🔴"
    
    mensaje += f"{emoji} <b>Compatibilidad: {score}/100</b>\n"
    mensaje += f"{comp.get('explicacion', 'N/A')}\n"
    mensaje += f"<i>💡 Score basado en: palabras clave, competencia y monto</i>\n\n"
    
    # Recomendación
    rec = analisis.get('recomendaciones', {})
    debe_participar = rec.get('debe_participar', False)
    prob = rec.get('probabilidad_exito', 'media')
    
    mensaje += f"{'✅' if debe_participar else '❌'} <b>Recomendación: "
    mensaje += f"{'PARTICIPAR' if debe_participar else 'NO PARTICIPAR'}</b>\n"
    mensaje += f"📊 Probabilidad de éxito: <b>{prob.upper()}</b>\n\n"
    
    # Resumen ejecutivo
    mensaje += f"📝 <b>Resumen:</b>\n{analisis.get('resumen_ejecutivo', 'N/A')}\n\n"
    
    # Estrategia de precio (sin mostrar precio específico ni rango)
    precio = analisis.get('recomendacion_precio', {})
    if precio.get('estrategia'):
        mensaje += f"💡 <b>Estrategia de Precio:</b>\n{precio.get('estrategia', 'N/A')}\n\n"
    
    mensaje += f"📋 <b>Código:</b> <code>{codigo}</code> (toca para copiar)\n"
    
    # Botones de acción
    keyboard = [
        [
            InlineKeyboardButton("💡 Ayuda Cotizar", callback_data=f"ayuda_{codigo}"),
            InlineKeyboardButton("⭐ Guardar", callback_data=f"guardar_{codigo}")
        ],
        [
            InlineKeyboardButton("🌐 Ver en MercadoPublico", url=f"https://www.mercadopublico.cl/PurchaseOrders/Details.aspx?BidCode={codigo}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.effective_message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='HTML')
    db_bot.registrar_interaccion(user_id, 'analisis', codigo)
