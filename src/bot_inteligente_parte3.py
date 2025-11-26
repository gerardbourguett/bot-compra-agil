"""
Bot Inteligente - Parte 3: Guardadas, Ayuda para Cotizar y Alertas
"""
from telegram import Update
from telegram.ext import ContextTypes
import database_bot as db_bot
import database_extended as db
import gemini_ai


# ==================== LICITACIONES GUARDADAS ====================

async def guardar_licitacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guarda una licitación para seguimiento"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.effective_message.reply_text(
            "⚠️ Uso: /guardar [código]\n"
            "Ejemplo: /guardar 1057389-2539-COT25",
            parse_mode='HTML'
        )
        return
    
    codigo = context.args[0]
    notas = " ".join(context.args[1:]) if len(context.args) > 1 else None
    
    exito = db_bot.guardar_licitacion(user_id, codigo, notas)
    
    if exito:
        await update.effective_message.reply_text(
            f"✅ Licitación {codigo} guardada\n"
            "Ver todas: /mis_guardadas",
            parse_mode='HTML'
        )
        db_bot.registrar_interaccion(user_id, 'guardar', codigo)
    else:
        await update.effective_message.reply_text(
            f"⚠️ La licitación <b>{codigo}</b> ya está en tu lista de guardadas.",
            parse_mode='HTML'
        )


async def mis_guardadas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra las licitaciones guardadas del usuario"""
    user_id = update.effective_user.id
    guardadas = db_bot.obtener_licitaciones_guardadas(user_id)
    
    if not guardadas:
        await update.message.reply_text(
            "📭 No tienes licitaciones guardadas.\n"
            "Usa /guardar [código] para guardar una.",
            parse_mode='HTML'
        )
        return
    
    mensaje = f"⭐ <b>Tus Licitaciones Guardadas ({len(guardadas)})</b>\n\n"
    
    for g in guardadas:
        codigo, fecha_guardado, notas, nombre, organismo, monto, fecha_cierre = g
        
        mensaje += f"📄 <b>{nombre[:60]}...</b>\n"
        mensaje += f"🏢 {organismo}\n"
        mensaje += f"💰 ${monto:,} CLP\n"
        mensaje += f"📅 Cierre: {fecha_cierre}\n"
        mensaje += f"🔖 Guardada: {fecha_guardado[:10]}\n"
        if notas:
            mensaje += f"📝 Notas: {notas}\n"
        mensaje += f"🔗 /analizar {codigo}\n"
        mensaje += f"❌ /eliminar_guardada {codigo}\n\n"
    
    await update.message.reply_text(mensaje, parse_mode='HTML')


async def eliminar_guardada(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Elimina una licitación guardada"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "⚠️ Uso: /eliminar_guardada [código]\n"
            "Ejemplo: /eliminar_guardada 1057389-2539-COT25",
            parse_mode='HTML'
        )
        return
    
    codigo = context.args[0]
    exito = db_bot.eliminar_licitacion_guardada(user_id, codigo)
    
    if exito:
        await update.message.reply_text(
            f"✅ Licitación {codigo} eliminada de guardadas.",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            f"❌ No encontré la licitación {codigo} en tus guardadas.",
            parse_mode='HTML'
        )


# ==================== AYUDA PARA COTIZAR ====================

async def ayuda_cotizar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera una guía personalizada para preparar la cotización"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.effective_message.reply_text(
            "⚠️ Uso: /ayuda_cotizar [código]\n"
            "Ejemplo: /ayuda_cotizar 1057389-2539-COT25",
            parse_mode='HTML'
        )
        return
    
    codigo = context.args[0]
    
    # Verificar perfil
    perfil = db_bot.obtener_perfil(user_id)
    if not perfil:
        await update.effective_message.reply_text(
            "❌ Primero configura tu perfil con /configurar_perfil",
            parse_mode='HTML'
        )
        return
    
    await update.effective_message.reply_text(
        f"📝 Generando guía para cotizar {codigo}...",
        parse_mode='HTML'
    )
    
    # Obtener licitación
    conn = db.get_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if db.USE_POSTGRES else '?'
    cursor.execute(f'''
        SELECT id, codigo, nombre, monto_disponible, moneda, fecha_cierre
        FROM licitaciones WHERE codigo = {placeholder}
    ''', (codigo,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        await update.effective_message.reply_text(
            f"❌ No encontré la licitación {codigo}",
            parse_mode='HTML'
        )
        return
    
    licitacion = dict(zip(['id', 'codigo', 'nombre', 'monto_disponible', 'moneda', 'fecha_cierre'], row))
    
    # Obtener análisis previo
    analisis = db_bot.obtener_analisis_cache(codigo)
    if not analisis:
        await update.effective_message.reply_text(
            f"⚠️ Primero analiza la licitación con /analizar {codigo}",
            parse_mode='HTML'
        )
        return
    
    # Generar guía con IA
    guia = gemini_ai.generar_ayuda_cotizacion(licitacion, perfil, analisis)
    
    # Formatear respuesta
    mensaje = f"📝 <b>Guía para Cotizar</b>\n\n"
    mensaje += f"📄 {licitacion['nombre'][:60]}...\n"
    mensaje += f"💰 Presupuesto: ${licitacion['monto_disponible']:,} {licitacion['moneda']}\n"
    mensaje += f"📅 Cierre: {licitacion['fecha_cierre']}\n\n"
    
    # Checklist de documentos
    if 'checklist_documentos' in guia:
        mensaje += "<b>📋 Documentos Necesarios:</b>\n"
        for doc in guia['checklist_documentos'][:5]:  # Primeros 5
            obligatorio = "✅" if doc.get('obligatorio') else "⚪"
            mensaje += f"{obligatorio} {doc['item']}\n"
        mensaje += "\n"
    
    # Consejos
    if 'consejos_presentacion' in guia:
        mensaje += "<b>💡 Consejos Clave:</b>\n"
        for consejo in guia['consejos_presentacion'][:3]:  # Primeros 3
            mensaje += f"• {consejo}\n"
        mensaje += "\n"
    
    # Errores a evitar
    if 'errores_evitar' in guia:
        mensaje += "<b>⚠️ Evita:</b>\n"
        for error in guia['errores_evitar'][:3]:  # Primeros 3
            mensaje += f"❌ {error}\n"
        mensaje += "\n"
    
    mensaje += f"🔗 Ver análisis completo: /analizar {codigo}\n"
    mensaje += f"⭐ Guardar: /guardar {codigo}"
    
    await update.effective_message.reply_text(mensaje, parse_mode='HTML')
    db_bot.registrar_interaccion(user_id, 'ayuda_cotizar', codigo)


async def recomendar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra top 5 licitaciones recomendadas con análisis"""
    user_id = update.effective_user.id
    perfil = db_bot.obtener_perfil(user_id)
    
    if not perfil:
        await update.message.reply_text(
            "❌ Primero configura tu perfil con /configurar_perfil",
            parse_mode='HTML'
        )
        return
    
    await update.message.reply_text(
        "🤖 Analizando las mejores oportunidades para ti...\n"
        "Esto puede tomar un momento.",
        parse_mode='HTML'
    )
    
    # Obtener licitaciones compatibles
    import filtros
    licitaciones = filtros.buscar_compatibles_con_perfil(perfil, limite=5)
    
    if not licitaciones:
        await update.message.reply_text(
            "😔 No encontré licitaciones compatibles en este momento.",
            parse_mode='HTML'
        )
        return
    
    mensaje = f"🎯 <b>Top 5 Recomendaciones para {perfil['nombre_empresa']}</b>\n\n"
    
    for i, lic in enumerate(licitaciones, 1):
        score = filtros.calcular_score_compatibilidad_simple(lic, perfil)
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
        
        mensaje += f"{emoji} <b>#{i} - Score: {score}/100</b>\n"
        mensaje += f"📄 {lic['nombre'][:60]}...\n"
        mensaje += f"🏢 {lic['organismo']}\n"
        mensaje += f"💰 ${lic['monto_disponible']:,} {lic['moneda']}\n"
        mensaje += f"📅 Cierre: {lic['fecha_cierre']}\n"
        mensaje += f"👥 Competencia: {lic['cantidad_proveedores_cotizando']} proveedores\n"
        mensaje += f"🔗 /analizar {lic['codigo']}\n\n"
    
    await update.message.reply_text(mensaje, parse_mode='HTML')
    db_bot.registrar_interaccion(user_id, 'recomendar')


# ==================== ALERTAS ====================

async def alertas_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Activa las alertas automáticas"""
    user_id = update.effective_user.id
    perfil = db_bot.obtener_perfil(user_id)
    
    if not perfil:
        await update.message.reply_text(
            "❌ Primero configura tu perfil con /configurar_perfil",
            parse_mode='HTML'
        )
        return
    
    perfil['alertas_activas'] = 1
    db_bot.guardar_perfil(user_id, perfil)
    
    await update.message.reply_text(
        "🔔 <b>Alertas activadas</b>\n\n"
        "Recibirás notificaciones sobre:\n"
        "• Nuevas licitaciones compatibles con tu perfil\n"
        "• Licitaciones guardadas próximas a cerrar\n"
        "• Cambios en licitaciones de interés\n\n"
        "Desactivar: /alertas_off",
        parse_mode='HTML'
    )


async def alertas_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Desactiva las alertas automáticas"""
    user_id = update.effective_user.id
    perfil = db_bot.obtener_perfil(user_id)
    
    if not perfil:
        return
    
    perfil['alertas_activas'] = 0
    db_bot.guardar_perfil(user_id, perfil)
    
    await update.message.reply_text(
        "🔕 Alertas desactivadas\n"
        "Activar: /alertas_on",
        parse_mode='HTML'
    )


# ==================== ESTADÍSTICAS ====================

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra estadísticas de la base de datos"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Total de licitaciones
    cursor.execute('SELECT COUNT(*) FROM licitaciones')
    total_lic = cursor.fetchone()[0]
    
    # Con detalles
    cursor.execute('SELECT COUNT(*) FROM licitaciones WHERE detalle_obtenido = 1')
    con_detalles = cursor.fetchone()[0]
    
    # Activas
    cursor.execute('SELECT COUNT(*) FROM licitaciones WHERE id_estado = 2')
    activas = cursor.fetchone()[0]
    
    # Total productos
    cursor.execute('SELECT COUNT(*) FROM productos_solicitados')
    total_productos = cursor.fetchone()[0]
    
    # Usuarios con perfil
    cursor.execute('SELECT COUNT(*) FROM perfiles_empresas')
    usuarios = cursor.fetchone()[0]
    
    conn.close()
    
    mensaje = "📊 <b>Estadísticas del Sistema</b>\n\n"
    mensaje += f"📋 Total licitaciones: <b>{total_lic:,}</b>\n"
    mensaje += f"✅ Con detalles completos: <b>{con_detalles:,}</b>\n"
    mensaje += f"🟢 Activas: <b>{activas:,}</b>\n"
    mensaje += f"📦 Productos catalogados: <b>{total_productos:,}</b>\n"
    mensaje += f"👥 Empresas registradas: <b>{usuarios:,}</b>\n"
    
    await update.message.reply_text(mensaje, parse_mode='HTML')
