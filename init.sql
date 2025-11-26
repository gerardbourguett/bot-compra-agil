-- Script de inicialización para PostgreSQL
-- Se ejecuta automáticamente al crear el contenedor

-- Crear extensiones útiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- Para búsquedas de texto similares

-- Nota: Las tablas se crearán automáticamente por los scripts de Python
-- Este archivo está aquí por si necesitas agregar configuraciones adicionales

-- Crear índices de texto completo (se pueden agregar después)
-- CREATE INDEX idx_licitaciones_nombre_trgm ON licitaciones USING gin (nombre gin_trgm_ops);
-- CREATE INDEX idx_licitaciones_organismo_trgm ON licitaciones USING gin (organismo gin_trgm_ops);

-- Configurar timezone
SET timezone = 'America/Santiago';

-- Mensaje de confirmación
DO $$
BEGIN
    RAISE NOTICE 'Base de datos PostgreSQL inicializada correctamente';
END $$;
