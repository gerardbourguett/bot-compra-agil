"""
Comandos de Telegram para manejo de suscripciones.
Agregar estos comandos al bot principal (bot_inteligente.py).
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import subscriptions as subs

async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los planes disponibles y opciones de upgrade"""
    user_id = update.effective_user.id
    
    current_sub = subs.get_user_subscription(user_id)
    current_tier = current_sub['tier']
    
    mensaje = "💎 <b>PLANES DISPONIBLES</b>\n\n"
    
    # FREE
    mensaje += "🆓 <b>GRATIS</b> - $0/mes\n"
    mensaje += "  • 2 análisis IA/día\n"
    mensaje += "  • 5 licitaciones guardadas\n"
    mensaje += "  • Búsquedas ilimitadas\n\n"
    
    # EMPRENDEDOR
    mensaje += "⭐ <b>EMPRENDEDOR</b> - $4.990/mes\n"
    mensaje += "  • 5 análisis IA/día\n"
    mensaje += "  • 30 licitaciones guardadas\n"
    mensaje += "  • 3 alertas automáticas\n"
    mensaje += "  • Exportar Excel (5/mes)\n"
    mensaje += "  • Filtros avanzados\n\n"
    
    # PYME
    mensaje += "🏢 <b>PYME</b> - $9.990/mes\n"
    mensaje += "  • 10 análisis IA/día\n"
    mensaje += "  • Licitaciones ilimitadas\n"
    mensaje += "  • 10 alertas automáticas\n"
    mensaje += "  • Excel ilimitado\n"
    mensaje += "  • Dashboard web\n"
    mensaje += "  • 2 usuarios\n\n"
    
    # PROFESIONAL
    mensaje += "💼 <b>PROFESIONAL</b> - $19.990/mes\n"
    mensaje += "  • Análisis IA ilimitados\n"
    mensaje += "  • 5 usuarios\n"
    mensaje += "  • API REST\n"
    mensaje += "  • Redacción automática ofertas\n"
    mensaje += "  • Soporte prioritario\n\n"
    
    mensaje += f"📍 Tu plan actual: <b>{current_tier.upper()}</b>\n\n"
    mensaje += "💡 <i>Contacta con nosotros para suscribirte:</i>\n"
    mensaje += "📧 contacto@compraagil.cl"
    
    keyboard = [[
        InlineKeyboardButton("💼 Ver más info", url="https://compraagil.cl/pricing")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(mensaje, parse_mode='HTML', reply_markup=reply_markup)


async def mi_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra el plan actual y uso del mes"""
    user_id = update.effective_user.id
    
    mensaje = subs.format_usage_message(user_id)
    
    # Agregar detalles adicionales
    subscription = subs.get_user_subscription(user_id)
    limits = subscription['limits']
    
    mensaje += "\n📋 <b>Límites de tu plan:</b>\n"
    mensaje += f"  • Análisis IA/día: {limits['ai_analyses_per_day']}\n"
    mensaje += f"  • Licitaciones guardadas: {limits['saved_tenders'] if limits['saved_tenders'] != -1 else '♾️'}\n"
    mensaje += f"  • Alertas: {limits['alerts'] if limits['alerts'] != -1 else '♾️'}\n"
    mensaje += f"  • Excel/mes: {limits['excel_exports_per_month'] if limits['excel_exports_per_month'] != -1 else '♾️'}\n"
    
    keyboard = []
    if subscription['tier'] == subs.SubscriptionTier.FREE.value:
        keyboard.append([InlineKeyboardButton("⬆️ Hacer Upgrade", callback_data="show_upgrade")])
    
    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
    
    await update.message.reply_text(mensaje, parse_mode='HTML', reply_markup=reply_markup)


async def check_and_notify_limit(update: Update, context: ContextTypes.DEFAULT_TYPE, action_type: str):
    """
    Verifica límites antes de ejecutar una acción.
    Retorna True si puede proceder, False si alcanzó el límite.
    
    Args:
        update: Telegram update
        context: Context
        action_type: 'ai_analysis', 'excel_export', 'save_tender'
    """
    user_id = update.effective_user.id
    
    check_result = subs.check_usage_limit(user_id, action_type)
    
    if not check_result['allowed']:
        tier = check_result.get('tier', 'free')
        current = check_result.get('current_usage', 0)
        limit = check_result.get('limit', 0)
        
        # Mensaje de límite alcanzado
        action_names = {
            'ai_analysis': 'análisis con IA',
            'excel_export': 'exportaciones a Excel',
            'save_tender': 'licitaciones guardadas'
        }
        
        action_name = action_names.get(action_type, 'esta acción')
        
        mensaje = f"🚫 <b>Límite alcanzado</b>\n\n"
        mensaje += f"Has usado {current}/{limit} {action_name} permitidos en tu plan <b>{tier.upper()}</b>.\n\n"
        
        # Sugerir upgrade según el tier
        upgrade_suggestions = {
            subs.SubscriptionTier.FREE.value: (
                "⭐ Upgradea a plan <b>EMPRENDEDOR</b> por solo $4.990/mes:\n"
                "  • 5 análisis IA por día\n"
                "  • 30 licitaciones guardadas\n"
                "  • Alertas automáticas\n"
            ),
            subs.SubscriptionTier.EMPRENDEDOR.value: (
                "🏢 Upgradea a plan <b>PYME</b> por $9.990/mes:\n"
                "  • 10 análisis IA por día\n"
                "  • Licitaciones ilimitadas\n"
                "  • Dashboard web\n"
            ),
            subs.SubscriptionTier.PYME.value: (
                "💼 Upgradea a plan <b>PROFESIONAL</b> por $19.990/mes:\n"
                "  • Análisis IA ilimitados\n"
                "  • API REST\n"
                "  • 5 usuarios\n"
            )
        }
        
        mensaje += upgrade_suggestions.get(tier, "Contacta con nosotros para más información.")
        mensaje += "\n\n💡 Usa /upgrade para ver todos los planes"
        
        keyboard = [[
            InlineKeyboardButton("⬆️ Ver Planes", callback_data="show_upgrade")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(mensaje, parse_mode='HTML', reply_markup=reply_markup)
        return False
    
    # Trackear el uso
    subs.track_usage(user_id, action_type)
    return True


# Ejemplo de uso en comando analizar (modificación sugerida)
async def analizar_con_limite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Versión del comando analizar que verifica límites.
    Reemplazar en bot_inteligente_parte2.py
    """
    # Verificar límite primero
    can_proceed = await check_and_notify_limit(update, context, 'ai_analysis')
    
    if not can_proceed:
        return  # Ya se mostró mensaje de límite
    
    # Continuar con análisis normal
    # ... (código existente de analizar)
    

if __name__ == "__main__":
    print("Comandos de suscripción listos para integrar")
    print("\nComandos a agregar al bot:")
    print("  - /upgrade")
    print("  - /mi_plan")
    print("\nFunciones helper:")
    print("  - check_and_notify_limit()")
