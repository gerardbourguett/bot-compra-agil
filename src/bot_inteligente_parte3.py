"""
Bot Inteligente - Parte 3: Guardadas, Ayuda para Cotizar y Alertas
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
    
    mensaje_inicial = f"🎯 <b>Top 5 Recomendaciones para {perfil['nombre_empresa']}</b>"
    await update.message.reply_text(mensaje_inicial, parse_mode='HTML')
    
    for i, lic in enumerate(licitaciones, 1):
        score = filtros.calcular_score_compatibilidad_simple(lic, perfil)
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
        
        texto = f"{emoji} <b>#{i} - Score: {score}/100</b>\n"
        texto += f"📄 {lic['nombre'][:60]}...\n"
        texto += f"🏢 {lic['organismo']}\n"
        texto += f"💰 ${lic['monto_disponible']:,} {lic['moneda']}\n"
        texto += f"📅 Cierre: {lic['fecha_cierre']}\n"
        texto += f"👥 Competencia: {lic['cantidad_proveedores_cotizando']} proveedores"
        
        keyboard = [
            [
                InlineKeyboardButton("Analizar 🤖", callback_data=f"analizar_{lic['codigo']}"),
                InlineKeyboardButton("📋 Detalle", callback_data=f"detalle_{lic['codigo']}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(texto, reply_markup=reply_markup, parse_mode='HTML')
    
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
    
    # Desglose por estado
    cursor.execute('SELECT estado, COUNT(*) FROM licitaciones GROUP BY estado ORDER BY COUNT(*) DESC')
    estados = cursor.fetchall()
    
    # Total productos
    cursor.execute('SELECT COUNT(*) FROM productos_solicitados')
    total_productos = cursor.fetchone()[0]
    
    # Usuarios con perfil
    # Nota: perfiles_empresas está en la otra BD (db_bot), pero aquí usamos 'conn' que es db_extended
    # Debemos abrir conexión a db_bot para esto o quitarlo si da error.
    # Asumimos que db_bot.obtener_perfil usa su propia conexión, así que aquí deberíamos usar db_bot
    # Pero el código original usaba 'cursor' de db_extended para consultar 'perfiles_empresas'?
    # Espera, 'perfiles_empresas' está en database_bot.py, NO en database_extended.py
    # El código original línea 326: cursor.execute('SELECT COUNT(*) FROM perfiles_empresas')
    # Si 'conn' viene de db.get_connection() (database_extended), entonces fallaría si las tablas no están juntas.
    # En SQLite pueden estar en archivos distintos. En Postgres en la misma DB.
    # Para evitar errores, usaré db_bot para contar usuarios.
    
    conn.close()
    
    # Contar usuarios usando db_bot
    conn_bot = db_bot.get_connection()
    cursor_bot = conn_bot.cursor()
    cursor_bot.execute('SELECT COUNT(*) FROM perfiles_empresas')
    usuarios = cursor_bot.fetchone()[0]
    conn_bot.close()
    
    mensaje = "📊 <b>Estadísticas del Sistema</b>\n\n"
    mensaje += f"📋 Total licitaciones: <b>{total_lic:,}</b>\n"
    mensaje += f"✅ Con detalles completos: <b>{con_detalles:,}</b>\n\n"
    
    mensaje += "<b>📌 Desglose por Estado:</b>\n"
    for estado, cantidad in estados:
        icono = "🟢" if "Publicada" in estado else "🔴" if "Cerrada" in estado else "⚖️" if "Adjudicada" in estado else "⚪"
        mensaje += f"{icono} {estado}: <b>{cantidad:,}</b>\n"
        
    mensaje += f"\n📦 Productos catalogados: <b>{total_productos:,}</b>\n"
    mensaje += f"👥 Empresas registradas: <b>{usuarios:,}</b>\n\n"
    
    # Tiempos de actualización
    from datetime import datetime
    
    last_list = db_bot.get_system_status('last_scrape_list')
    last_details = db_bot.get_system_status('last_scrape_details')
    
    def format_time_ago(iso_str):
        if not iso_str: return "Nunca"
        dt = datetime.fromisoformat(iso_str)
        diff = datetime.now() - dt
        minutes = int(diff.total_seconds() / 60)
        if minutes < 60:
            return f"hace {minutes} min"
        hours = int(minutes / 60)
        return f"hace {hours} horas"

    mensaje += "<b>🕒 Última Actualización:</b>\n"
    mensaje += f"• Listado: {format_time_ago(last_list['value'] if last_list else None)}\n"
    mensaje += f"• Detalles: {format_time_ago(last_details['value'] if last_details else None)}\n"
    
    await update.message.reply_text(mensaje, parse_mode='HTML')


# ==================== REDACCIÓN DE OFERTAS (IA) ====================

async def redactar_oferta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el proceso de redacción de una oferta"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "⚠️ Uso: /redactar_oferta [código]\n"
            "Ejemplo: /redactar_oferta 1057389-2539-COT25",
            parse_mode='HTML'
        )
        return
    
    codigo = context.args[0]
    
    # Verificar perfil
    perfil = db_bot.obtener_perfil(user_id)
    if not perfil:
        await update.message.reply_text("❌ Primero configura tu perfil con /configurar_perfil")
        return
        
    # Verificar si existe la licitación
    conn = db.get_connection()
    cursor = conn.cursor()
    placeholder = '%s' if db.USE_POSTGRES else '?'
    cursor.execute(f'SELECT nombre FROM licitaciones WHERE codigo = {placeholder}', (codigo,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        await update.message.reply_text(f"❌ No encontré la licitación {codigo}")
        return
        
    nombre_lic = row[0]
    
    # Preguntar formato
    keyboard = [
        [
            InlineKeyboardButton("📝 Texto Telegram", callback_data=f"redactar_texto_{codigo}"),
            InlineKeyboardButton("📄 PDF (Markdown)", callback_data=f"redactar_pdf_{codigo}")
        ],
        [
            InlineKeyboardButton("📧 Correo", callback_data=f"redactar_correo_{codigo}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✍️ <b>Redactar Oferta para:</b>\n"
        f"{nombre_lic}\n\n"
        "¿En qué formato quieres el borrador?",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )


async def ejecutar_redaccion(update: Update, context: ContextTypes.DEFAULT_TYPE, codigo, formato):
    """Ejecuta la generación del borrador"""
    user_id = update.effective_user.id
    perfil = db_bot.obtener_perfil(user_id)
    
    await update.effective_message.reply_text(f"🤖 Generando borrador en formato <b>{formato.upper()}</b>...", parse_mode='HTML')
    
    # Obtener datos completos de la licitación
    conn = db.get_connection()
    cursor = conn.cursor()
    placeholder = '%s' if db.USE_POSTGRES else '?'
    
    # Consultar columnas básicas
    cursor.execute(f'''
        SELECT codigo, nombre, organismo, descripcion, monto_disponible, fecha_cierre 
        FROM licitaciones WHERE codigo = {placeholder}
    ''', (codigo,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        await update.effective_message.reply_text("❌ Error al obtener datos de la licitación.")
        return
        
    licitacion = {
        'codigo': row[0],
        'nombre': row[1],
        'organismo': row[2],
        'descripcion': row[3],
        'monto_disponible': row[4],
        'fecha_cierre': row[5]
    }
    
    # Generar con IA
    borrador = gemini_ai.generar_borrador_oferta(licitacion, perfil, formato)
    
    # Enviar resultado
    if len(borrador) > 4000:
        # Si es muy largo, enviar en partes o archivo
        # Por simplicidad, enviamos los primeros 4000 caracteres
        await update.effective_message.reply_text(borrador[:4000])
        if len(borrador) > 4000:
            await update.effective_message.reply_text(borrador[4000:])
    else:
        await update.effective_message.reply_text(borrador)
        
    # Sugerencia final
    await update.effective_message.reply_text(
        "💡 Puedes copiar y editar este texto antes de enviarlo.\n"
        "Si necesitas ajustes, puedes pedirlo de nuevo con otro formato."
    )
