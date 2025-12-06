"""
Sistema de Suscripciones y Monetización para Bot Compra Ágil
Gestiona tiers de usuarios, límites de uso y validaciones.
"""
import os
from datetime import datetime, timedelta
from enum import Enum
import database_extended as db

# Tiers de suscripción
class SubscriptionTier(Enum):
    FREE = "free"
    EMPRENDEDOR = "emprendedor"
    PYME = "pyme"
    PROFESIONAL = "profesional"

# Límites por tier
TIER_LIMITS = {
    SubscriptionTier.FREE.value: {
        "ai_analyses_per_day": 2,
        "saved_tenders": 5,
        "alerts": 0,
        "excel_exports_per_month": 0,
        "users": 1,
        "dashboard_web": False,
        "api_access": False,
    },
    SubscriptionTier.EMPRENDEDOR.value: {
        "ai_analyses_per_day": 5,
        "saved_tenders": 30,
        "alerts": 3,
        "excel_exports_per_month": 5,
        "users": 1,
        "dashboard_web": False,
        "api_access": False,
    },
    SubscriptionTier.PYME.value: {
        "ai_analyses_per_day": 10,
        "saved_tenders": -1,  # ilimitado
        "alerts": 10,
        "excel_exports_per_month": -1,  # ilimitado
        "users": 2,
        "dashboard_web": True,
        "api_access": False,
    },
    SubscriptionTier.PROFESIONAL.value: {
        "ai_analyses_per_day": -1,  # ilimitado
        "saved_tenders": -1,
        "alerts": -1,
        "excel_exports_per_month": -1,
        "users": 5,
        "dashboard_web": True,
        "api_access": True,
    }
}

# Precios en CLP
TIER_PRICES = {
    SubscriptionTier.FREE.value: 0,
    SubscriptionTier.EMPRENDEDOR.value: 4990,
    SubscriptionTier.PYME.value: 9990,
    SubscriptionTier.PROFESIONAL.value: 19990,
}


def get_user_subscription(user_id):
    """
    Obtiene la suscripción activa del usuario.
    Si no tiene, retorna FREE por defecto.
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        if db.USE_POSTGRES:
            cursor.execute("""
                SELECT tier, status, current_period_end 
                FROM subscriptions 
                WHERE user_id = %s
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT tier, status, current_period_end 
                FROM subscriptions 
                WHERE user_id = ?
            """, (user_id,))
        
        result = cursor.fetchone()
        
        if not result:
            # Usuario nuevo, crear suscripción FREE
            return create_free_subscription(user_id)
        
        tier, status, period_end = result
        
        # Verificar si expiró
        if status == 'active' and period_end:
            if db.USE_POSTGRES:
                from datetime import date
                if isinstance(period_end, str):
                    period_end = datetime.strptime(period_end, '%Y-%m-%d').date()
                if period_end < date.today():
                    # Expiró, downgrade a FREE
                    update_subscription_status(user_id, 'expired')
                    tier = SubscriptionTier.FREE.value
        
        return {
            'tier': tier,
            'status': status,
            'limits': TIER_LIMITS.get(tier, TIER_LIMITS[SubscriptionTier.FREE.value])
        }
        
    except Exception as e:
        print(f"Error al obtener suscripción: {e}")
        return {
            'tier': SubscriptionTier.FREE.value,
            'status': 'active',
            'limits': TIER_LIMITS[SubscriptionTier.FREE.value]
        }
    finally:
        conn.close()


def create_free_subscription(user_id):
    """Crea una suscripción FREE para usuario nuevo"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        if db.USE_POSTGRES:
            cursor.execute("""
                INSERT INTO subscriptions (user_id, tier, status, created_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO NOTHING
            """, (user_id, SubscriptionTier.FREE.value, 'active', datetime.now()))
        else:
            cursor.execute("""
                INSERT OR IGNORE INTO subscriptions (user_id, tier, status, created_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, SubscriptionTier.FREE.value, 'active', datetime.now()))
        
        conn.commit()
        
        return {
            'tier': SubscriptionTier.FREE.value,
            'status': 'active',
            'limits': TIER_LIMITS[SubscriptionTier.FREE.value]
        }
    except Exception as e:
        print(f"Error al crear suscripción FREE: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def check_usage_limit(user_id, action_type):
    """
    Verifica si el usuario puede realizar una acción según su tier.
    
    Args:
        user_id: ID del usuario
        action_type: 'ai_analysis', 'excel_export', 'save_tender'
    
    Returns:
        dict: {'allowed': bool, 'reason': str, 'current_usage': int, 'limit': int}
    """
    subscription = get_user_subscription(user_id)
    tier = subscription['tier']
    limits = subscription['limits']
    
    # Mapeo de acciones a límites
    limit_map = {
        'ai_analysis': 'ai_analyses_per_day',
        'excel_export': 'excel_exports_per_month',
        'save_tender': 'saved_tenders',
    }
    
    limit_key = limit_map.get(action_type)
    if not limit_key:
        return {'allowed': False, 'reason': 'Acción no reconocida'}
    
    limit_value = limits.get(limit_key, 0)
    
    # -1 significa ilimitado
    if limit_value == -1:
        return {'allowed': True, 'current_usage': 0, 'limit': -1}
    
    # Obtener uso actual
    current_usage = get_current_usage(user_id, action_type)
    
    if current_usage >= limit_value:
        return {
            'allowed': False,
            'reason': f'Límite alcanzado ({current_usage}/{limit_value})',
            'current_usage': current_usage,
            'limit': limit_value,
            'tier': tier
        }
    
    return {
        'allowed': True,
        'current_usage': current_usage,
        'limit': limit_value,
        'tier': tier
    }


def get_current_usage(user_id, action_type):
    """Obtiene el uso actual del usuario para una acción específica"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # Determinar el período según el tipo de acción
        if '_per_day' in action_type or action_type == 'ai_analysis':
            # Límite diario
            today = datetime.now().date()
            start_time = datetime.combine(today, datetime.min.time())
        else:
            # Límite mensual
            today = datetime.now()
            start_time = today.replace(day=1, hour=0, minute=0, second=0)
        
        if db.USE_POSTGRES:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM usage_tracking 
                WHERE user_id = %s 
                AND action = %s 
                AND timestamp >= %s
            """, (user_id, action_type, start_time))
        else:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM usage_tracking 
                WHERE user_id = ? 
                AND action = ? 
                AND timestamp >= ?
            """, (user_id, action_type, start_time))
        
        result = cursor.fetchone()
        return result[0] if result else 0
        
    except Exception as e:
        print(f"Error al obtener uso: {e}")
        return 0
    finally:
        conn.close()


def track_usage(user_id, action_type, resource_id=None, metadata=None):
    """Registra el uso de una feature"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        import json
        metadata_json = json.dumps(metadata) if metadata else None
        
        if db.USE_POSTGRES:
            cursor.execute("""
                INSERT INTO usage_tracking (user_id, action, resource_id, timestamp, metadata)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, action_type, resource_id, datetime.now(), metadata_json))
        else:
            cursor.execute("""
                INSERT INTO usage_tracking (user_id, action, resource_id, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, action_type, resource_id, datetime.now(), metadata_json))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error al trackear uso: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def update_subscription_status(user_id, new_status):
    """Actualiza el estado de la suscripción"""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        if db.USE_POSTGRES:
            cursor.execute("""
                UPDATE subscriptions 
                SET status = %s, updated_at = %s 
                WHERE user_id = %s
            """, (new_status, datetime.now(), user_id))
        else:
            cursor.execute("""
                UPDATE subscriptions 
                SET status = ?, updated_at = ? 
                WHERE user_id = ?
            """, (new_status, datetime.now(), user_id))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error al actualizar suscripción: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_tier_info(tier_name):
    """Obtiene información detallada de un tier"""
    return {
        'name': tier_name,
        'price': TIER_PRICES.get(tier_name, 0),
        'limits': TIER_LIMITS.get(tier_name, {}),
        'currency': 'CLP'
    }


def format_usage_message(user_id):
    """Genera mensaje formateado con el uso actual del usuario"""
    subscription = get_user_subscription(user_id)
    tier = subscription['tier']
    limits = subscription['limits']
    
    # Uso de análisis IA
    ai_usage = get_current_usage(user_id, 'ai_analysis')
    ai_limit = limits.get('ai_analyses_per_day', 0)
    
    message = f"📊 <b>Tu Plan: {tier.upper()}</b>\n\n"
    message += f"🤖 <b>Análisis IA hoy:</b> {ai_usage}"
    message += f"/{ai_limit if ai_limit != -1 else '∞'}\n"
    
    # Precio
    price = TIER_PRICES.get(tier, 0)
    if price > 0:
        message += f"💰 <b>Precio:</b> ${price:,} CLP/mes\n"
    else:
        message += f"💰 <b>Plan GRATIS</b>\n"
    
    # Agregar upgrade CTA si es FREE
    if tier == SubscriptionTier.FREE.value:
        message += f"\n💡 <b>Upgrade a EMPRENDEDOR por solo $4.990/mes</b>\n"
        message += "Usa /upgrade para ver planes"
    
    return message


if __name__ == "__main__":
    # Test
    print("Sistema de suscripciones inicializado")
    print(f"Tiers disponibles: {list(SubscriptionTier)}")
    print(f"Precios: {TIER_PRICES}")
