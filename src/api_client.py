"""
Cliente para interactuar con la API de Mercado Público - Compra Ágil
Incluye funciones para obtener listados, fichas detalladas, historial y adjuntos
"""
import time
from datetime import datetime
from curl_cffi import requests

# Configuración de la API
API_BASE_URL = "https://api.buscador.mercadopublico.cl/compra-agil"
API_KEY = "e93089e4-437c-4723-b343-4fa20045e3bc"


def obtener_headers():
    """
    Construye los headers necesarios para las peticiones a la API.
    Solo necesitamos la X-API-Key, no se requiere token Bearer.
    """
    return {
        "accept": "application/json, text/plain, */*",
        "accept-language": "es-ES,es;q=0.9",
        "origin": "https://buscador.mercadopublico.cl",
        "referer": "https://buscador.mercadopublico.cl/",
        "sec-ch-ua": '"Chromium";v="142", "Google Chrome";v="142", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/142.0.0.0 Safari/537.36"
        ),
        "x-api-key": API_KEY
    }


def obtener_licitaciones(date_from, date_to, status=2, page_number=1):
    """
    Obtiene el listado de licitaciones de la API para una página específica.

    Args:
        date_from: Fecha inicial (formato: YYYY-MM-DD)
        date_to: Fecha final (formato: YYYY-MM-DD)
        status: Estado de las licitaciones (2 = Publicada)
        page_number: Número de página a obtener

    Returns:
        dict: Respuesta JSON de la API o None si hay error
    """
    params = {
        "date_from": date_from,
        "date_to": date_to,
        "order_by": "recent",
        "page_number": page_number,
        "status": status
    }

    headers = obtener_headers()

    try:
        response = requests.get(
            API_BASE_URL,
            params=params,
            headers=headers,
            impersonate="chrome120"
        )
        response.raise_for_status()
        return response.json()
    except Exception as error:
        print(f"❌ Error al obtener licitaciones (página {page_number}): {error}")
        return None


def obtener_ficha_detalle(codigo):
    """
    Obtiene la ficha detallada de una licitación específica.

    Args:
        codigo: Código de la licitación (ej: "1057389-2539-COT25")

    Returns:
        dict: Datos detallados de la licitación o None si hay error
    """
    params = {
        "action": "ficha",
        "code": codigo
    }

    headers = obtener_headers()

    try:
        response = requests.get(
            API_BASE_URL,
            params=params,
            headers=headers,
            impersonate="chrome120"
        )
        response.raise_for_status()
        data = response.json()

        if data.get('success') == 'OK':
            return data.get('payload')
        return None
    except Exception as error:
        print(f"❌ Error al obtener ficha de {codigo}: {error}")
        return None


def obtener_historial(codigo):
    """
    Obtiene el historial de acciones de una licitación específica.

    Args:
        codigo: Código de la licitación (ej: "1057389-2539-COT25")

    Returns:
        list: Lista de registros del historial o None si hay error
    """
    params = {
        "action": "historial",
        "code": codigo
    }

    headers = obtener_headers()

    try:
        response = requests.get(
            API_BASE_URL,
            params=params,
            headers=headers,
            impersonate="chrome120"
        )
        response.raise_for_status()
        data = response.json()

        if data.get('success') == 'OK':
            payload = data.get('payload', {})
            return payload.get('registros', [])
        return None
    except Exception as error:
        print(f"❌ Error al obtener historial de {codigo}: {error}")
        return None


def obtener_adjuntos(codigo):
    """
    Obtiene la lista de archivos adjuntos de una licitación específica.

    Args:
        codigo: Código de la licitación (ej: "1057389-2539-COT25")

    Returns:
        list: Lista de archivos adjuntos o lista vacía si hay error
    """
    # Intentar primero con el endpoint de adjuntos
    url = (
        "https://adjunto.mercadopublico.cl/adjunto-compra-agil/v1/"
        f"adjuntos-compra-agil/listar/{codigo}"
    )

    headers = obtener_headers()

    try:
        response = requests.get(url, headers=headers, impersonate="chrome120")

        # Si funciona, retornar los adjuntos
        if response.status_code == 200:
            data = response.json()
            if data.get('success') == 'OK':
                payload = data.get('payload', {})
                return payload.get('files', [])

        # Si falla (403 u otro error), retornar lista vacía
        # Los adjuntos no son críticos, podemos continuar sin ellos
        return []

    except Exception:
        # En caso de error, retornar lista vacía en lugar de None
        # Esto permite que el proceso continúe
        return []


def obtener_detalle_completo(codigo, incluir_historial=True, incluir_adjuntos=True):
    """
    Obtiene toda la información disponible de una licitación.

    Args:
        codigo: Código de la licitación
        incluir_historial: Si se debe obtener el historial (default: True)
        incluir_adjuntos: Si se debe obtener los adjuntos (default: True)

    Returns:
        dict: Diccionario con toda la información disponible
    """
    resultado = {
        'codigo': codigo,
        'ficha': None,
        'historial': None,
        'adjuntos': None
    }

    # Obtener ficha detallada
    resultado['ficha'] = obtener_ficha_detalle(codigo)
    time.sleep(0.3)  # Pequeña pausa entre requests

    # Obtener historial si se solicita
    if incluir_historial:
        resultado['historial'] = obtener_historial(codigo)
        time.sleep(0.3)

    # Obtener adjuntos si se solicita
    if incluir_adjuntos:
        resultado['adjuntos'] = obtener_adjuntos(codigo)
        time.sleep(0.3)

    return resultado


if __name__ == "__main__":
    # Ejemplo de uso
    print("🧪 Probando cliente de API...\n")

    # Probar obtención de listado
    print("1. Obteniendo listado de licitaciones...")
    FECHA = datetime.now().strftime("%Y-%m-%d")
    DATOS = obtener_licitaciones(FECHA, FECHA, page_number=1)
    if DATOS and DATOS.get('success') == 'OK':
        PAYLOAD = DATOS.get('payload', {})
        RESULTADOS = PAYLOAD.get('resultados', [])
        print(f"   ✅ Encontradas {len(RESULTADOS)} licitaciones")

        if RESULTADOS:
            CODIGO_EJEMPLO = RESULTADOS[0].get('codigo')
            print(f"\n2. Obteniendo detalles de: {CODIGO_EJEMPLO}")

            # Obtener ficha
            FICHA = obtener_ficha_detalle(CODIGO_EJEMPLO)
            if FICHA:
                print(f"   ✅ Ficha obtenida")
                print(f"      Nombre: {FICHA.get('nombre')}")
                print(f"      Presupuesto: {FICHA.get('presupuesto_estimado')} {FICHA.get('moneda')}")

            # Obtener historial
            HISTORIAL = obtener_historial(CODIGO_EJEMPLO)
            if HISTORIAL:
                print(f"   ✅ Historial obtenido ({len(HISTORIAL)} registros)")

            # Obtener adjuntos
            ADJUNTOS = obtener_adjuntos(CODIGO_EJEMPLO)
            if ADJUNTOS:
                print(f"   ✅ Adjuntos obtenidos ({len(ADJUNTOS)} archivos)")
                for ADJ in ADJUNTOS:
                    print(f"      - {ADJ.get('nombreArchivo')}")
    else:
        print("   ❌ Error al obtener listado")
