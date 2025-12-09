"""
Nuevos comandos del bot para funcionalidades ML/IA
Incluye: precio_optimo, historico, stats
"""
from telegram import Update
from telegram.ext import ContextTypes
import logging

# Importar módulos ML
from ml_precio_optimo import obtener_recomendacion_rapida, analizar_competencia_precios
from rag_historico import buscar_casos_similares, construir_contexto_historico

logger = logging.getLogger(__name__)


async def comando_precio_optimo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /precio_optimo <producto> [cantidad]
    Recomienda precio óptimo basado en datos históricos
    """
    user_id = update.effective_user.id
    
    # Parsear argumentos
    if not context.args:
        await update.message.reply_text(
            "📊 USO: /precio_optimo <producto> [cantidad]\n\n"
            "Ejemplos:\n"
            "• /precio_optimo laptop\n"
            "• /precio_optimo computador 10\n"
            "• /precio_optimo silla de oficina 50"
        )
        return
    
    # Extraer producto y cantidad
    texto_completo = ' '.join(context.args)
    partes = texto_completo.rsplit(' ', 1)
    
    try:
        cantidad = int(partes[-1])
        producto = partes[0]
    except (ValueError, IndexError):
        producto = texto_completo
        cantidad = 1
    
    # Mensaje de loading
    mensaje_loading = await update.message.reply_text(
        f"🔍 Analizando precios históricos para '{producto}'...\n"
        f"⏳ Esto puede tomar unos segundos..."
    )
    
    try:
        # Obtener recomendación
        resultado = obtener_recomendacion_rapida(producto, cantidad)
        
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=mensaje_loading.message_id,
            text=resultado
        )
        
    except Exception as e:
        logger.error(f"Error en /precio_optimo: {e}", exc_info=True)
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=mensaje_loading.message_id,
            text=f"❌ Error al calcular precio óptimo: {str(e)}"
        )


async def comando_historico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /historico <palabra_clave>
    Busca en datos históricos licitaciones similares
    """
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "🔍 USO: /historico <palabra_clave>\n\n"
            "Busca licitaciones similares en el histórico.\n\n"
            "Ejemplo: /historico laptop dell"
        )
        return
    
    busqueda = ' '.join(context.args)
    
    mensaje_loading = await update.message.reply_text(
        f"🔍 Buscando '{busqueda}' en histórico...\n"
        f"📊 Analizando 3+ millones de registros..."
    )
    
    try:
        # Buscar casos similares
        casos = buscar_casos_similares(busqueda, limite=10)
        
        if not casos:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=mensaje_loading.message_id,
                text=f"❌ No se encontraron licitaciones similares a '{busqueda}'"
            )
            return
        
        # Formatear resultados
        mensaje = f"📚 RESULTADOS HISTÓRICOS: '{busqueda}'\n"
        mensaje += f"Encontrados {len(casos)} casos similares\n\n"
        
        # Mostrar top 5
        for i, caso in enumerate(casos[:5], 1):
            emoji = "✅" if caso['es_ganador'] else "❌"
            mensaje += f"{emoji} {i}. {caso['nombre'][:60]}...\n"
            mensaje += f"   • Proveedor: {caso['proveedor']}\n"
            mensaje += f"   • Monto: ${caso['monto']:,}\n"
            mensaje += f"   • Región: {caso['region']}\n"
            mensaje += f"   • Hace {caso['antiguedad_dias']//30} meses\n"
            mensaje += f"   • Similitud: {caso['similitud']}%\n\n"
        
        if len(casos) > 5:
            mensaje += f"... y {len(casos) - 5} casos más.\n\n"
        
        mensaje += "💡 Usa /precio_optimo para ver recomendaciones de precio."
        
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=mensaje_loading.message_id,
            text=mensaje
        )
        
    except Exception as e:
        logger.error(f"Error en /historico: {e}", exc_info=True)
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=mensaje_loading.message_id,
            text=f"❌ Error al buscar en histórico: {str(e)}"
        )


async def comando_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /stats [producto]
    Muestra estadísticas generales o de un producto específico
    """
    user_id = update.effective_user.id
    
    try:
        import database_extended as db
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Estadísticas generales
        if not context.args:
            # Total de registros
            cursor.execute("SELECT COUNT(*) FROM historico_licitaciones")
            total = cursor.fetchone()[0]
            
            # Ganadores vs perdedores
            cursor.execute("SELECT COUNT(*) FROM historico_licitaciones WHERE es_ganador = TRUE")
            ganadores = cursor.fetchone()[0]
            
            tasa_conversion = (ganadores / total * 100) if total > 0 else 0
            
            # Monto promedio
            cursor.execute("SELECT AVG(monto_total) FROM historico_licitaciones WHERE monto_total > 0")
            monto_prom = cursor.fetchone()[0] or 0
            
            # Regiones más activas
            query_regiones = """
                SELECT region, COUNT(*) as total
                FROM historico_licitaciones
                WHERE region IS NOT NULL
                GROUP BY region
                ORDER BY total DESC
                LIMIT 5
            """
            cursor.execute(query_regiones)
            regiones = cursor.fetchall()
            
            mensaje = f"""📊 ESTADÍSTICAS GENERALES DEL HISTÓRICO

📈 Datos Generales:
• Total registros: {total:,}
• Ofertas ganadoras: {ganadores:,} ({tasa_conversion:.1f}%)
• Monto promedio: ${monto_prom:,.0f}

🏆 Top 5 Regiones:
"""
            for region, count in regiones:
                mensaje += f"• {region}: {count:,} ofertas\n"
            
            mensaje += "\n💡 Usa /stats <producto> para ver estadísticas de un producto específico."
            
        else:
            # Estadísticas de producto específico
            producto = ' '.join(context.args)
            
            mensaje_loading = await update.message.reply_text(
                f"📊 Analizando estadísticas de '{producto}'..."
            )
            
            try:
                from ml_precio_optimo import buscar_productos_similares
                df = buscar_productos_similares(producto, limite=1000)
                
                if df.empty:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=mensaje_loading.message_id,
                        text=f"❌ No hay datos suficientes para '{producto}'"
                    )
                    conn.close()
                    return
                
                # Calcular estadísticas
                total = len(df)
                ganadores = len(df[df['es_ganador'] == True])
                tasa = (ganadores / total * 100) if total > 0 else 0
                
                precio_min = df['precio_unitario'].min()
                precio_max = df['precio_unitario'].max()
                precio_prom = df['precio_unitario'].mean()
                precio_mediana = df['precio_unitario'].median()
                
                # Proveedores frecuentes
                top_prov = df[df['es_ganador'] == True]['nombre_proveedor'].value_counts().head(3)
                
                mensaje = f"""📊 ESTADÍSTICAS: '{producto}'

📈 Datos Generales:
• Total ofertas: {total:,}
• Ofertas ganadoras: {ganadores:,} ({tasa:.1f}%)

💰 Precios Unitarios:
• Mínimo: ${precio_min:,.0f}
• Promedio: ${precio_prom:,.0f}
• Mediana: ${precio_mediana:,.0f}
• Máximo: ${precio_max:,.0f}

🏆 Proveedores que más ganan:
"""
                for prov, count in top_prov.items():
                    mensaje += f"• {prov}: {count} victorias\n"
                
                mensaje += f"\n💡 Usa /precio_optimo {producto} para obtener recomendación."
                
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=mensaje_loading.message_id,
                    text=mensaje
                )
                conn.close()
                return
                
            except Exception as e:
                logger.error(f"Error en stats producto: {e}")
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=mensaje_loading.message_id,
                    text=f"❌ Error al calcular estadísticas: {str(e)}"
                )
                conn.close()
                return
        
        conn.close()
        await update.message.reply_text(mensaje)
        
    except Exception as e:
        logger.error(f"Error en /stats: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Error al obtener estadísticas: {str(e)}")


async def comando_competidores(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /competidores <producto>
    Muestra análisis de competencia para un producto
    """
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "🎯 USO: /competidores <producto>\n\n"
            "Analiza la competencia para un producto específico.\n\n"
            "Ejemplo: /competidores laptop"
        )
        return
    
    producto = ' '.join(context.args)
    
    mensaje_loading = await update.message.reply_text(
        f"🎯 Analizando competencia para '{producto}'...\n"
        f"⏳ Procesando datos históricos..."
    )
    
    try:
        resultado = analizar_competencia_precios(producto)
        
        if not resultado.get('success'):
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=mensaje_loading.message_id,
                text=f"❌ {resultado.get('error', 'No hay datos suficientes')}"
            )
            return
        
        mensaje = f"🎯 ANÁLISIS DE COMPETENCIA: '{producto}'\n\n"
        mensaje += f"📊 Total de competidores: {resultado['total_competidores']}\n\n"
        
        mensaje += "🏆 TOP 5 COMPETIDORES (por participación):\n"
        for i, (nombre, datos) in enumerate(list(resultado['top_competidores'].items())[:5], 1):
            mensaje += f"{i}. {nombre}\n"
            mensaje += f"   • Ofertas: {datos['monto_total_count']:.0f}\n"
            mensaje += f"   • Tasa de éxito: {datos['tasa_exito']:.1f}%\n"
            mensaje += f"   • Precio promedio: ${datos['precio_unitario_mean']:,.0f}\n\n"
        
        stats = resultado['estadisticas_generales']
        mensaje += f"💰 Rango de Precios del Mercado:\n"
        mensaje += f"   • Mínimo: ${stats['precio_min']:,.0f}\n"
        mensaje += f"   • Promedio: ${stats['precio_promedio']:,.0f}\n"
        mensaje += f"   • Máximo: ${stats['precio_max']:,.0f}\n"
        
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=mensaje_loading.message_id,
            text=mensaje
        )
        
    except Exception as e:
        logger.error(f"Error en /competidores: {e}", exc_info=True)
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=mensaje_loading.message_id,
            text=f"❌ Error al analizar competencia: {str(e)}"
        )


# Exportar comandos para registro en el bot principal
COMANDOS_ML = {
    'precio_optimo': comando_precio_optimo,
    'historico': comando_historico,
    'stats': comando_stats,
    'competidores': comando_competidores,
}
