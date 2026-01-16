"""
Circuit Breaker Pattern Implementation

Protege servicios externos (API Mercado Público, Gemini, etc.) 
de sobrecarga y cascading failures.

Estados:
- CLOSED: Normal operation (permite todas las requests)
- OPEN: Circuit abierto (todas las requests fallan rápido)
- HALF_OPEN: Permitiendo requests de prueba

Flujo:
1. CLOSED → OPEN: Después de N fallos consecutivos
2. OPEN → HALF_OPEN: Después de timeout de recuperación
3. HALF_OPEN → CLOSED: Si request de prueba tiene éxito
4. HALF_OPEN → OPEN: Si request de prueba falla
"""
import time
import logging
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger('compra_agil.circuit_breaker')


class CircuitState(Enum):
    """Estados del circuit breaker"""
    CLOSED = 0      # Normal - permite requests
    OPEN = 1        # Abierto - rechaza requests
    HALF_OPEN = 2   # Medio abierto - permite 1 request de prueba


class CircuitBreakerError(Exception):
    """Exception cuando el circuit breaker está abierto"""
    pass


class CircuitBreaker:
    """
    Implementación del patrón Circuit Breaker.
    
    Args:
        name: Nombre del servicio (para logging/métricas)
        failure_threshold: Número de fallos para abrir el circuito (default: 5)
        recovery_timeout: Segundos antes de intentar recuperación (default: 60)
        expected_exception: Tipo de excepción que cuenta como fallo (default: Exception)
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        # Estado
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._last_success_time = None
        
        logger.info(
            f"Circuit breaker '{name}' initialized "
            f"(threshold={failure_threshold}, timeout={recovery_timeout}s)"
        )
    
    @property
    def state(self) -> CircuitState:
        """Obtiene el estado actual del circuit breaker"""
        # Si está abierto, verificar si es tiempo de intentar recuperación
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
                self._state = CircuitState.HALF_OPEN
        
        return self._state
    
    @property
    def state_name(self) -> str:
        """Nombre del estado actual"""
        return self._state.name
    
    @property
    def is_closed(self) -> bool:
        """True si el circuito está cerrado (normal)"""
        return self.state == CircuitState.CLOSED
    
    @property
    def is_open(self) -> bool:
        """True si el circuito está abierto (rechazando requests)"""
        return self.state == CircuitState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        """Verifica si es tiempo de intentar recuperación"""
        if self._last_failure_time is None:
            return False
        
        return (time.time() - self._last_failure_time) >= self.recovery_timeout
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Ejecuta una función protegida por el circuit breaker.
        
        Args:
            func: Función a ejecutar
            *args, **kwargs: Argumentos para la función
        
        Returns:
            Resultado de la función
        
        Raises:
            CircuitBreakerError: Si el circuito está abierto
            Exception: Si la función falla
        """
        # Si está abierto, rechazar inmediatamente
        if self.state == CircuitState.OPEN:
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Service temporarily unavailable."
            )
        
        try:
            # Ejecutar la función
            result = func(*args, **kwargs)
            
            # Si tiene éxito, registrar y cerrar el circuito
            self._on_success()
            return result
            
        except self.expected_exception as e:
            # Si falla, registrar y posiblemente abrir el circuito
            self._on_failure()
            raise
    
    def _on_success(self):
        """Maneja una ejecución exitosa"""
        self._last_success_time = time.time()
        
        # Si estaba en HALF_OPEN, volver a CLOSED
        if self._state == CircuitState.HALF_OPEN:
            logger.info(
                f"Circuit breaker '{self.name}' recovered! "
                f"Returning to CLOSED state."
            )
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            
            # Registrar métrica de éxito
            try:
                from metrics_server import circuit_breaker_successes
                circuit_breaker_successes.labels(service=self.name).inc()
            except:
                pass
        
        # Si estaba CLOSED, resetear contador de fallos
        elif self._state == CircuitState.CLOSED:
            self._failure_count = 0
    
    def _on_failure(self):
        """Maneja una ejecución fallida"""
        self._last_failure_time = time.time()
        self._failure_count += 1
        
        # Registrar métrica de fallo
        try:
            from metrics_server import circuit_breaker_failures
            circuit_breaker_failures.labels(service=self.name).inc()
        except:
            pass
        
        # Si estaba en HALF_OPEN, volver a OPEN
        if self._state == CircuitState.HALF_OPEN:
            logger.warning(
                f"Circuit breaker '{self.name}' test failed! "
                f"Returning to OPEN state."
            )
            self._state = CircuitState.OPEN
        
        # Si alcanzamos el threshold, abrir el circuito
        elif self._failure_count >= self.failure_threshold:
            logger.error(
                f"Circuit breaker '{self.name}' OPENED! "
                f"Threshold reached: {self._failure_count}/{self.failure_threshold} failures"
            )
            self._state = CircuitState.OPEN
            
            # Registrar estado en métrica
            try:
                from metrics_server import circuit_breaker_state
                circuit_breaker_state.labels(service=self.name).set(
                    self._state.value
                )
            except:
                pass
    
    def reset(self):
        """Resetea manualmente el circuit breaker a CLOSED"""
        logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED")
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
    
    def get_stats(self) -> dict:
        """Obtiene estadísticas del circuit breaker"""
        return {
            'name': self.name,
            'state': self.state_name,
            'failure_count': self._failure_count,
            'failure_threshold': self.failure_threshold,
            'last_failure_time': self._last_failure_time,
            'last_success_time': self._last_success_time,
            'recovery_timeout': self.recovery_timeout,
        }


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60,
    expected_exception: type = Exception
):
    """
    Decorador para proteger funciones con circuit breaker.
    
    Usage:
        @circuit_breaker('mercado_publico', failure_threshold=3, recovery_timeout=30)
        def fetch_licitaciones():
            # código que llama a API externa
            pass
    
    Args:
        name: Nombre del servicio
        failure_threshold: Fallos antes de abrir circuito
        recovery_timeout: Segundos de timeout
        expected_exception: Tipo de excepción a capturar
    """
    # Crear instancia del circuit breaker (singleton por nombre)
    if not hasattr(circuit_breaker, '_instances'):
        circuit_breaker._instances = {}
    
    if name not in circuit_breaker._instances:
        circuit_breaker._instances[name] = CircuitBreaker(
            name, failure_threshold, recovery_timeout, expected_exception
        )
    
    breaker = circuit_breaker._instances[name]
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        # Exponer el breaker para acceso directo
        wrapper.circuit_breaker = breaker
        return wrapper
    
    return decorator


def get_circuit_breaker(name: str) -> Optional[CircuitBreaker]:
    """Obtiene un circuit breaker por nombre"""
    if hasattr(circuit_breaker, '_instances'):
        return circuit_breaker._instances.get(name)
    return None


def get_all_circuit_breakers() -> dict:
    """Obtiene todos los circuit breakers activos"""
    if hasattr(circuit_breaker, '_instances'):
        return circuit_breaker._instances
    return {}


# ==================== CIRCUIT BREAKERS PRE-CONFIGURADOS ====================

# Circuit breaker para API Mercado Público
mercado_publico_breaker = CircuitBreaker(
    name='mercado_publico',
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=Exception
)

# Circuit breaker para Gemini AI
gemini_breaker = CircuitBreaker(
    name='gemini_ai',
    failure_threshold=3,
    recovery_timeout=30,
    expected_exception=Exception
)

# Circuit breaker para Redis
redis_breaker = CircuitBreaker(
    name='redis',
    failure_threshold=5,
    recovery_timeout=10,
    expected_exception=Exception
)


if __name__ == "__main__":
    # Test del circuit breaker
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("TEST: Circuit Breaker")
    print("=" * 60)
    
    # Función de prueba que falla
    failure_count = 0
    
    def unreliable_service():
        global failure_count
        failure_count += 1
        if failure_count < 7:  # Falla las primeras 6 veces
            raise Exception(f"Service failure #{failure_count}")
        return "Success!"
    
    # Crear circuit breaker
    breaker = CircuitBreaker(
        name='test_service',
        failure_threshold=3,
        recovery_timeout=2
    )
    
    # Intentar llamar al servicio
    for i in range(10):
        print(f"\n--- Attempt {i+1} ---")
        print(f"State: {breaker.state_name}")
        print(f"Failures: {breaker._failure_count}/{breaker.failure_threshold}")
        
        try:
            result = breaker.call(unreliable_service)
            print(f"✅ SUCCESS: {result}")
        except CircuitBreakerError as e:
            print(f"⚡ CIRCUIT OPEN: {e}")
        except Exception as e:
            print(f"❌ FAILED: {e}")
        
        # Esperar un poco entre intentos
        if i == 5:
            print("\n💤 Waiting for recovery timeout...")
            time.sleep(2.5)
    
    print("\n" + "=" * 60)
    print("Final stats:", breaker.get_stats())
