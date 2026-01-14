"""
Script de Testing para API v3.0
Tests todos los endpoints principales
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8001"

def print_test(name, success, data=None):
    """Imprime resultado de test"""
    symbol = "✅" if success else "❌"
    print(f"\n{symbol} {name}")
    if data:
        print(f"   {json.dumps(data, indent=2, ensure_ascii=False)[:200]}...")

def test_root():
    """Test endpoint raíz"""
    try:
        r = requests.get(f"{BASE_URL}/")
        print_test("GET /", r.status_code == 200, r.json())
        return r.json()
    except Exception as e:
        print_test("GET /", False)
        print(f"   Error: {e}")
        return None

def test_health():
    """Test health check"""
    try:
        r = requests.get(f"{BASE_URL}/health")
        data = r.json()
        print_test("GET /health", r.status_code == 200 and data.get('status') == 'healthy', data)
        return data
    except Exception as e:
        print_test("GET /health", False)
        print(f"   Error: {e}")
        return None

def test_licitaciones():
    """Test listado de licitaciones"""
    try:
        r = requests.get(f"{BASE_URL}/api/v3/licitaciones/", params={"page": 1, "limit": 3})
        data = r.json()
        success = r.status_code == 200 and data.get('success') == True
        print_test("GET /api/v3/licitaciones/", success)
        if success:
            print(f"   Total: {data['pagination']['total']} licitaciones")
            print(f"   Mostrando: {len(data['data'])} de {data['pagination']['pages']} páginas")
        return data
    except Exception as e:
        print_test("GET /api/v3/licitaciones/", False)
        print(f"   Error: {e}")
        return None

def test_stats():
    """Test estadísticas"""
    try:
        r = requests.get(f"{BASE_URL}/api/v3/stats")
        data = r.json()
        print_test("GET /api/v3/stats", r.status_code == 200)
        if r.status_code == 200:
            print(f"   Total registros: {data.get('total_registros', 0):,}")
            print(f"   Ofertas ganadoras: {data.get('ofertas_ganadoras', 0):,}")
            print(f"   Tasa conversión: {data.get('tasa_conversion', 0):.2f}%")
        return data
    except Exception as e:
        print_test("GET /api/v3/stats", False)
        print(f"   Error: {e}")
        return None

def test_analisis_con_perfil():
    """Test análisis con perfil (endpoint estrella)"""
    try:
        payload = {
            "nombre_empresa": "Banquetes Doña Clara",
            "rubro": "Servicios de Catering",
            "historial_adjudicaciones": 0,
            "dolor_principal": "entender_papeles",
            "codigo_licitacion": "TEST-123",
            "titulo": "Servicio de Coffee Break",
            "descripcion": "Coffee break para 50 personas durante 3 días",
            "monto_estimado": 250000,
            "organismo": "Municipalidad de Providencia",
            "region": "RM"
        }
        
        r = requests.post(f"{BASE_URL}/api/v3/ai/analizar-con-perfil", json=payload)
        data = r.json()
        success = r.status_code == 200 and data.get('success') == True
        
        print_test("POST /api/v3/ai/analizar-con-perfil ⭐", success)
        if success:
            print(f"   Perfil detectado: {data.get('perfil_detectado')}")
            print(f"   Prompt length: {len(data.get('system_prompt', ''))} caracteres")
            print(f"   Mensaje: {data.get('mensaje')}")
        return data
    except Exception as e:
        print_test("POST /api/v3/ai/analizar-con-perfil ⭐", False)
        print(f"   Error: {e}")
        return None

def test_productos():
    """Test búsqueda de productos"""
    try:
        r = requests.get(f"{BASE_URL}/api/v3/productos/search", params={"q": "notebook", "limit": 5})
        data = r.json()
        success = r.status_code == 200 and data.get('success') == True
        print_test("GET /api/v3/productos/search", success)
        if success:
            print(f"   Encontrados: {data.get('total', 0)} productos")
        return data
    except Exception as e:
        print_test("GET /api/v3/productos/search", False)
        print(f"   Error: {e}")
        return None

def main():
    """Ejecuta todos los tests"""
    print("=" * 80)
    print("🧪 TESTING API v3.0 - CompraÁgil")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Base URL: {BASE_URL}")
    
    tests = [
        ("Root Endpoint", test_root),
        ("Health Check", test_health),
        ("Licitaciones", test_licitaciones),
        ("Stats", test_stats),
        ("Productos", test_productos),
        ("Análisis con Perfil (NUEVO)", test_analisis_con_perfil),
    ]
    
    results = {}
    for name, test_func in tests:
        print(f"\n{'─' * 80}")
        print(f"Testing: {name}")
        print('─' * 80)
        try:
            result = test_func()
            results[name] = result is not None
        except Exception as e:
            print(f"❌ Error general: {e}")
            results[name] = False
    
    # Resumen
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE TESTS")
    print("=" * 80)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"Success Rate: {(passed/total*100):.1f}%")
    
    print("\nDetalle:")
    for name, success in results.items():
        symbol = "✅" if success else "❌"
        print(f"  {symbol} {name}")
    
    print("\n" + "=" * 80)
    if passed == total:
        print("🎉 ¡TODOS LOS TESTS PASARON!")
    else:
        print("⚠️  Algunos tests fallaron. Revisa los errores arriba.")
    print("=" * 80)

if __name__ == "__main__":
    main()
