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
import gemini_ai
import filtros
import api_client

# Importar funciones de las partes del bot
from bot_inteligente_parte1 import (
    start, configurar_perfil, recibir_nombre_empresa, recibir_tipo_negocio,
    recibir_productos, recibir_palabras_clave, recibir_capacidad,
    recibir_ubicacion, recibir_experiencia, recibir_certificaciones,
    cancelar_perfil, ver_perfil,
    NOMBRE_EMPRESA, TIPO_NEGOCIO, PRODUCTOS, PALABRAS_CLAVE,
    CAPACIDAD, UBICACION, EXPERIENCIA, CERTIFICACIONES
)
from bot_inteligente_parte2 import (
    buscar, oportunidades, urgentes, por_monto, analizar
)
from bot_inteligente_parte3 import (
    guardar_licitacion, mis_guardadas, eliminar_guardada,
    ayuda_cotizar, recomendar, alertas_on, alertas_off, stats
)

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
            UBICACION: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_ubicacion)],
            EXPERIENCIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_experiencia)],
            CERTIFICACIONES: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_certificaciones)],
        },
        fallbacks=[CommandHandler('cancelar', cancelar_perfil)]
    )
    
    # Comandos básicos
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('perfil', ver_perfil))
    application.add_handler(perfil_handler)
    
    # Comandos de búsqueda
    application.add_handler(CommandHandler('buscar', buscar))
    application.add_handler(CommandHandler('oportunidades', oportunidades))
    application.add_handler(CommandHandler('urgentes', urgentes))
    application.add_handler(CommandHandler('por_monto', por_monto))
    
    # Comandos de análisis con IA
    application.add_handler(CommandHandler('analizar', analizar))
    application.add_handler(CommandHandler('recomendar', recomendar))
    application.add_handler(CommandHandler('ayuda_cotizar', ayuda_cotizar))
    
    # Comandos de licitaciones guardadas
    application.add_handler(CommandHandler('guardar', guardar_licitacion))
    application.add_handler(CommandHandler('mis_guardadas', mis_guardadas))
    application.add_handler(CommandHandler('eliminar_guardada', eliminar_guardada))
    
    # Comandos de alertas
    application.add_handler(CommandHandler('alertas_on', alertas_on))
    application.add_handler(CommandHandler('alertas_off', alertas_off))
    
    # Estadísticas
    application.add_handler(CommandHandler('stats', stats))
    
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


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
        print(f"\n❌ Error fatal: {e}")
