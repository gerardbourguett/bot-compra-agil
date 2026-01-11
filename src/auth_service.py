"""
Sistema de Autenticación para API REST v3
Gestiona API keys por usuario y validación de requests.
"""
import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import HTTPException, Security, Header
from fastapi.security import APIKeyHeader
import database_extended as db

# Header para API Key
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Secret para generar API keys (cambiar en producción)
API_SECRET = os.getenv('API_SECRET_KEY', 'change-this-in-production-please')


def generar_api_key() -> str:
    """
    Genera una API key única y segura.
    
    Returns:
        String de 64 caracteres hexadecimales
    """
    return secrets.token_hex(32)


def hash_api_key(api_key: str) -> str:
    """
    Hashea una API key para almacenamiento seguro.
    
    Args:
        api_key: API key en texto plano
        
    Returns:
        Hash SHA256 de la API key
    """
    return hashlib.sha256(f"{api_key}{API_SECRET}".encode()).hexdigest()


def crear_api_key_para_usuario(user_id: int, nombre: str = "API Key") -> Dict:
    """
    Crea una nueva API key para un usuario.
    Solo disponible para tier PROFESIONAL.
    
    Args:
        user_id: Telegram user ID
        nombre: Nombre descriptivo de la key
        
    Returns:
        Dict con la API key generada y metadata
        
    Raises:
        HTTPException: Si el usuario no tiene acceso
    """
    # Verificar que el usuario tenga tier PROFESIONAL
    import subscriptions
    
    subs = subscriptions.get_user_subscription(user_id)
    if subs['tier'] != 'profesional':
        raise HTTPException(
            status_code=403,
            detail="API access solo disponible para tier PROFESIONAL"
        )
    
    # Generar API key
    api_key = generar_api_key()
    api_key_hash = hash_api_key(api_key)
    
    # Guardar en base de datos
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        placeholder = '%s' if db.USE_POSTGRES else '?'
        
        # Crear tabla si no existe
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS api_keys (
                id {'SERIAL PRIMARY KEY' if db.USE_POSTGRES else 'INTEGER PRIMARY KEY AUTOINCREMENT'},
                user_id BIGINT NOT NULL,
                key_hash TEXT NOT NULL UNIQUE,
                nombre TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Insertar API key
        cursor.execute(f"""
            INSERT INTO api_keys (user_id, key_hash, nombre, created_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
        """, (user_id, api_key_hash, nombre, datetime.now()))
        
        conn.commit()
        
        return {
            'api_key': api_key,  # ⚠️ Solo se muestra UNA VEZ
            'nombre': nombre,
            'created_at': datetime.now().isoformat(),
            'tier': subs['tier']
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error creando API key: {str(e)}")
    finally:
        conn.close()


def validar_api_key(api_key: str) -> Optional[int]:
    """
    Valida una API key y retorna el user_id asociado.
    
    Args:
        api_key: API key en texto plano
        
    Returns:
        user_id si es válida, None si no
    """
    if not api_key:
        return None
    
    api_key_hash = hash_api_key(api_key)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        placeholder = '%s' if db.USE_POSTGRES else '?'
        
        cursor.execute(f"""
            SELECT user_id, is_active 
            FROM api_keys 
            WHERE key_hash = {placeholder}
        """, (api_key_hash,))
        
        result = cursor.fetchone()
        
        if not result:
            return None
        
        user_id, is_active = result
        
        if not is_active:
            return None
        
        # Actualizar last_used
        cursor.execute(f"""
            UPDATE api_keys 
            SET last_used = {placeholder}
            WHERE key_hash = {placeholder}
        """, (datetime.now(), api_key_hash))
        
        conn.commit()
        
        return user_id
        
    except Exception as e:
        print(f"Error validando API key: {e}")
        return None
    finally:
        conn.close()


def revocar_api_key(user_id: int, key_hash: str) -> bool:
    """
    Revoca (desactiva) una API key.
    
    Args:
        user_id: User ID dueño de la key
        key_hash: Hash de la API key a revocar
        
    Returns:
        True si se revocó exitosamente
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        placeholder = '%s' if db.USE_POSTGRES else '?'
        
        cursor.execute(f"""
            UPDATE api_keys 
            SET is_active = FALSE
            WHERE user_id = {placeholder} AND key_hash = {placeholder}
        """, (user_id, key_hash))
        
        conn.commit()
        return cursor.rowcount > 0
        
    except Exception as e:
        print(f"Error revocando API key: {e}")
        return False
    finally:
        conn.close()


def listar_api_keys(user_id: int) -> list:
    """
    Lista todas las API keys de un usuario (sin mostrar la key completa).
    
    Args:
        user_id: Telegram user ID
        
    Returns:
        Lista de diccionarios con metadata de las keys
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        placeholder = '%s' if db.USE_POSTGRES else '?'
        
        cursor.execute(f"""
            SELECT 
                key_hash,
                nombre,
                created_at,
                last_used,
                is_active
            FROM api_keys
            WHERE user_id = {placeholder}
            ORDER BY created_at DESC
        """, (user_id,))
        
        results = cursor.fetchall()
        
        keys = []
        for row in results:
            key_hash, nombre, created_at, last_used, is_active = row
            keys.append({
                'key_hash': key_hash[:16] + '...',  # Mostrar solo primeros 16 chars
                'nombre': nombre,
                'created_at': created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at),
                'last_used': last_used.isoformat() if last_used and hasattr(last_used, 'isoformat') else None,
                'is_active': is_active
            })
        
        return keys
        
    except Exception as e:
        print(f"Error listando API keys: {e}")
        return []
    finally:
        conn.close()


# Dependency para FastAPI
async def require_api_key(api_key: str = Security(api_key_header)) -> int:
    """
    Dependency de FastAPI para requerir autenticación.
    
    Args:
        api_key: API key del header X-API-Key
        
    Returns:
        user_id del usuario autenticado
        
    Raises:
        HTTPException: Si la API key es inválida o falta
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key requerida. Incluye el header 'X-API-Key: tu-api-key'"
        )
    
    user_id = validar_api_key(api_key)
    
    if not user_id:
        raise HTTPException(
            status_code=403,
            detail="API key inválida o revocada"
        )
    
    return user_id


# Dependency opcional (permite requests sin auth)
async def optional_api_key(api_key: str = Security(api_key_header)) -> Optional[int]:
    """
    Dependency de FastAPI para autenticación opcional.
    Si hay API key, la valida. Si no, retorna None.
    
    Args:
        api_key: API key del header X-API-Key (opcional)
        
    Returns:
        user_id del usuario autenticado o None
    """
    if not api_key:
        return None
    
    return validar_api_key(api_key)
