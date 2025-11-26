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
import io
import pandas as pd


# ==================== BÚSQUEDAS ====================

async def buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Busca licitaciones por palabra clave con paginación"""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Uso: /buscar [palabra clave]\n"
            "Ejemplo: /buscar sillas",
            parse_mode='HTML'
        )
        return
    
    palabra = " ".join(context.args)
    await update.message.reply_text(f"🔍 Buscando '{palabra}'...")
    
    # Buscar SIN límite (o con uno muy alto)
    resultados = filtros.buscar_por_palabras_clave(palabra, limite=100)
    
    if not resultados:
        await update.message.reply_text(
            f"No encontré licitaciones con '{palabra}' 😔\n"
            "Intenta con otras palabras clave.",
            parse_mode='HTML'
        )
        return
    
    # Guardar en contexto para paginación
    context.user_data['busqueda_actual'] = {
        'resultados': resultados,
        'pagina': 0,
        'total': len(resultados),
        'tipo': 'busqueda'
    }
    
    await mostrar_pagina(update, context)
    
    # Registrar búsqueda
    db_bot.registrar_interaccion(update.effective_user.id, 'busqueda', palabra)


async def mostrar_pagina(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra una página de resultados"""
    data = context.user_data.get('busqueda_actual')
    if not data:
        return

    resultados = data['resultados']
    pagina = data['pagina']
    total = data['total']
    items_por_pagina = 5
    
    inicio = pagina * items_por_pagina
    fin = inicio + items_por_pagina
    items_pagina = resultados[inicio:fin]
    
    total_paginas = (total + items_por_pagina - 1) // items_por_pagina
    
    # Mensaje de cabecera
    if update.callback_query:
        # Si viene de un botón, no enviamos mensaje nuevo, solo editamos o enviamos items
        # Pero como son mensajes separados, es complejo editar.
        # Estrategia: Enviar items nuevos.
        await update.effective_message.reply_text(
            f"📄 <b>Página {pagina + 1}/{total_paginas}</b> (Resultados {inicio + 1}-{min(fin, total)} de {total})",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            f"📋 Encontré <b>{total}</b> licitaciones.\n"
            f"📄 <b>Página {pagina + 1}/{total_paginas}</b>",
            parse_mode='HTML'
        )
    
    # Mostrar items
    for lic in items_pagina:
        # Verificar si tiene score pre-calculado
        if 'score' in lic:
            score = lic['score']
            emoji_score = "🟢" if score >= 70 else "🟡" if score >= 40 else "🔴"
            texto = f"{emoji_score} <b>Score: {score}/100</b>\n"
        else:
            texto = ""
            
        texto += f"📄 <b>{lic['nombre'][:80]}...</b>\n"
        texto += f"🏢 {lic['organismo']}\n"
        texto += f"💰 ${lic['monto_disponible']:,} {lic['moneda']}\n"
        texto += f"📅 Cierre: {lic['fecha_cierre']}\n"
        if 'cantidad_proveedores_cotizando' in lic:
            texto += f"👥 Cotizando: {lic['cantidad_proveedores_cotizando']}"
        
        keyboard = [
            [
                InlineKeyboardButton("Analizar 🤖", callback_data=f"analizar_{lic['codigo']}"),
                InlineKeyboardButton("📋 Detalle", callback_data=f"detalle_{lic['codigo']}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.effective_message.reply_text(texto, reply_markup=reply_markup, parse_mode='HTML')
        
    # Botones de navegación (en un mensaje separado al final)
    botones = []
    if pagina > 0:
        botones.append(InlineKeyboardButton("⬅️ Anterior", callback_data="pag_ant"))
    if fin < total:
        botones.append(InlineKeyboardButton("➡️ Siguiente", callback_data="pag_sig"))
        
    # Botón exportar si hay muchos
    fila_extra = []
    if total > 10:
        fila_extra.append(InlineKeyboardButton("📥 Exportar Excel", callback_data="exportar_excel"))
        
    keyboard_nav = []
    if botones:
        keyboard_nav.append(botones)
    if fila_extra:
        keyboard_nav.append(fila_extra)
        
    if keyboard_nav:
        reply_markup_nav = InlineKeyboardMarkup(keyboard_nav)
        await update.effective_message.reply_text("Navegación:", reply_markup=reply_markup_nav)


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
    
    # Buscar licitaciones compatibles (más resultados)
    licitaciones = filtros.buscar_compatibles_con_perfil(perfil, limite=50)
    
    if not licitaciones:
        await update.message.reply_text(
            "😔 No encontré licitaciones compatibles en este momento.\n"
            "Intenta actualizar tus palabras clave en /configurar_perfil",
            parse_mode='HTML'
        )
        return
    
    # Pre-calcular scores para mostrar en paginación
    resultados_con_score = []
    for lic in licitaciones:
        score = filtros.calcular_score_compatibilidad_simple(lic, perfil)
        lic['score'] = score # Guardar score en el dict
        resultados_con_score.append(lic)
        
    # Ordenar por score descendente
    resultados_con_score.sort(key=lambda x: x['score'], reverse=True)
    
    context.user_data['busqueda_actual'] = {
        'resultados': resultados_con_score,
        'pagina': 0,
        'total': len(resultados_con_score),
        'tipo': 'oportunidades'
    }
    
    await mostrar_pagina(update, context)
    
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
    
    licitaciones = filtros.buscar_urgentes(dias=dias, limite=50)
    
    if not licitaciones:
        await update.message.reply_text(
            f"✅ No hay licitaciones cerrando en los próximos {dias} días.",
            parse_mode='HTML'
        )
        return
    
    context.user_data['busqueda_actual'] = {
        'resultados': licitaciones,
        'pagina': 0,
        'total': len(licitaciones),
        'tipo': 'urgentes'
    }
    
    await mostrar_pagina(update, context)
    
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
        
        licitaciones = filtros.buscar_por_monto(monto_min, monto_max, limite=50)
        
        if not licitaciones:
            await update.message.reply_text(
                "No encontré licitaciones en ese rango de monto.",
                parse_mode='HTML'
            )
            return
        
        context.user_data['busqueda_actual'] = {
            'resultados': licitaciones,
            'pagina': 0,
            'total': len(licitaciones),
            'tipo': 'por_monto'
        }
        
        await mostrar_pagina(update, context)
        
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
    conn = db.get_connection()
    cursor = conn.cursor()
    
    placeholder = '%s' if db.USE_POSTGRES else '?'
    
    cursor.execute(f'''
        SELECT id, codigo, nombre, fecha_publicacion, fecha_cierre, organismo, 
               unidad, estado, monto_disponible, moneda, cantidad_proveedores_cotizando
        FROM licitaciones WHERE codigo = {placeholder}
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
    cursor.execute(f'''
        SELECT nombre, cantidad, unidad_medida
        FROM productos_solicitados WHERE codigo_licitacion = {placeholder}
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


async def exportar_excel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Genera y envía un Excel con los resultados de la búsqueda actual"""
    data = context.user_data.get('busqueda_actual')
    if not data:
        await update.effective_message.reply_text("⚠️ No hay búsqueda activa para exportar.")
        return
        
    resultados = data['resultados']
    
    # Crear DataFrame
    df = pd.DataFrame(resultados)
    
    # Seleccionar y renombrar columnas relevantes
    columnas = {
        'codigo': 'Código',
        'nombre': 'Nombre',
        'organismo': 'Organismo',
        'monto_disponible': 'Monto',
        'moneda': 'Moneda',
        'fecha_cierre': 'Cierre',
        'estado': 'Estado'
    }
    
    # Si tiene score, agregarlo
    if 'score' in df.columns:
        columnas['score'] = 'Score Compatibilidad'
        
    # Filtrar columnas que existen
    cols_existentes = [c for c in columnas.keys() if c in df.columns]
    df = df[cols_existentes]
    df = df.rename(columns=columnas)
    
    # Guardar en buffer
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Licitaciones')
    output.seek(0)
    
    # Enviar archivo
    await update.effective_message.reply_document(
        document=output,
        filename=f"licitaciones_{data['tipo']}.xlsx",
        caption=f"📊 Aquí tienes el reporte con {len(resultados)} licitaciones."
    )


async def detalle_licitacion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el detalle completo de una licitación almacenada en BD"""
    if not context.args:
        await update.effective_message.reply_text("⚠️ Uso: /detalle [código]")
        return
        
    codigo = context.args[0]
    
    conn = db.get_connection()
    cursor = conn.cursor()
    placeholder = '%s' if db.USE_POSTGRES else '?'
    
    # 1. Obtener detalle principal
    cursor.execute(f'''
        SELECT nombre, descripcion, organismo_comprador, rut_organismo_comprador,
               direccion_entrega, plazo_entrega, presupuesto_estimado, moneda,
               estado, fecha_cierre, tipo_presupuesto, cantidad_proveedores_invitados
        FROM licitaciones_detalle
        WHERE codigo = {placeholder}
    ''', (codigo,))
    
    row = cursor.fetchone()
    
    if not row:
        # Intentar buscar en tabla básica si no hay detalle
        cursor.execute(f'''
            SELECT nombre, 'Sin descripción detallada', organismo, '',
                   '', 0, monto_disponible, moneda,
                   estado, fecha_cierre, '', 0
            FROM licitaciones WHERE codigo = {placeholder}
        ''', (codigo,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            await update.effective_message.reply_text(f"❌ No encontré información para {codigo}")
            return
            
        es_basico = True
    else:
        es_basico = False
        
    # Mapear datos
    (nombre, descripcion, organismo, rut_organismo, direccion, plazo, 
     presupuesto, moneda, estado, cierre, tipo_presup, invitados) = row
     
    # 2. Obtener productos
    cursor.execute(f'''
        SELECT nombre, descripcion, cantidad, unidad_medida
        FROM productos_solicitados
        WHERE codigo_licitacion = {placeholder}
    ''', (codigo,))
    productos = cursor.fetchall()
    
    conn.close()
    
    # Construir mensaje
    mensaje = f"📋 <b>Detalle de Licitación</b>\n"
    mensaje += f"<code>{codigo}</code>\n\n"
    
    mensaje += f"🏢 <b>{organismo}</b>\n"
    if rut_organismo: mensaje += f"RUT: {rut_organismo}\n"
    mensaje += f"📍 {direccion or 'No especificada'}\n\n"
    
    mensaje += f"📄 <b>{nombre}</b>\n"
    if descripcion:
        mensaje += f"<i>{descripcion[:300]}{'...' if len(descripcion)>300 else ''}</i>\n\n"
    
    if presupuesto:
        mensaje += f"💰 <b>Presupuesto:</b> ${presupuesto:,.0f} {moneda}\n"
    mensaje += f"📅 <b>Cierre:</b> {cierre}\n"
    mensaje += f"📊 <b>Estado:</b> {estado}\n"
    if plazo: mensaje += f"⏱️ <b>Plazo Entrega:</b> {plazo} días\n"
    if invitados: mensaje += f"📩 <b>Invitados:</b> {invitados}\n"
    
    if productos:
        mensaje += f"\n📦 <b>Productos ({len(productos)}):</b>\n"
        for p in productos:
            p_nombre, p_desc, p_cant, p_unidad = p
            mensaje += f"• <b>{p_cant} {p_unidad}</b>: {p_nombre}\n"
            if p_desc and p_desc != p_nombre:
                mensaje += f"  <i>{p_desc[:50]}...</i>\n"
    
    if es_basico:
        mensaje += "\n⚠️ <i>Nota: Solo se encontró información básica. El scraper aún no ha obtenido los detalles completos.</i>"
        
    # Botones
    keyboard = [
        [
            InlineKeyboardButton("Analizar 🤖", callback_data=f"analizar_{codigo}"),
            InlineKeyboardButton("⭐ Guardar", callback_data=f"guardar_{codigo}")
        ],
        [
            InlineKeyboardButton("🌐 Ver en MercadoPublico", url=f"https://www.mercadopublico.cl/PurchaseOrders/Details.aspx?BidCode={codigo}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.effective_message.reply_text(mensaje, reply_markup=reply_markup, parse_mode='HTML')
