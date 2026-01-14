"""
Tests for database modules - database_extended.py and database_bot.py
"""
import pytest


class TestDatabaseExtended:
    """Tests for database_extended module."""
    
    def test_module_imports(self):
        """Database module should import successfully."""
        import database_extended as db
        assert db is not None
    
    def test_use_postgres_is_boolean(self):
        """USE_POSTGRES should be a boolean."""
        import database_extended as db
        assert isinstance(db.USE_POSTGRES, bool)
    
    def test_get_connection_returns_connection(self):
        """get_connection should return a valid connection."""
        import database_extended as db
        
        conn = db.get_connection()
        assert conn is not None
        
        # Should have cursor method
        assert hasattr(conn, 'cursor')
        
        conn.close()
    
    def test_get_placeholder_returns_correct_format(self):
        """get_placeholder should return correct format for DB type."""
        import database_extended as db
        
        placeholder = db.get_placeholder()
        
        if db.USE_POSTGRES:
            assert placeholder == '%s'
        else:
            assert placeholder == '?'
    
    @pytest.mark.integration
    def test_licitaciones_table_exists(self, db_connection):
        """Licitaciones table should exist."""
        import database_extended as db
        
        cursor = db_connection.cursor()
        
        if db.USE_POSTGRES:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'licitaciones'
                )
            """)
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='table' AND name='licitaciones'
            """)
        
        result = cursor.fetchone()[0]
        assert result, "Table 'licitaciones' should exist"


class TestDatabaseBot:
    """Tests for database_bot module."""
    
    def test_module_imports(self):
        """Database bot module should import successfully."""
        import database_bot as db_bot
        assert db_bot is not None
    
    def test_get_placeholder_consistency(self):
        """get_placeholder should match database_extended behavior."""
        import database_extended as db_ext
        import database_bot as db_bot
        
        # Both should return the same placeholder
        assert db_ext.get_placeholder() == db_bot.get_placeholder()
    
    def test_obtener_perfil_returns_none_for_nonexistent(self):
        """obtener_perfil should return None for non-existent user."""
        import database_bot as db_bot
        
        # Use a user ID that definitely doesn't exist
        result = db_bot.obtener_perfil(999999999999)
        assert result is None
    
    @pytest.mark.integration
    def test_guardar_y_obtener_perfil(self):
        """Should be able to save and retrieve a profile."""
        import database_bot as db_bot
        
        # Ensure tables exist
        db_bot.iniciar_db_bot()
        
        test_user_id = 123456789
        test_perfil = {
            'nombre_empresa': 'Test Company',
            'tipo_negocio': 'Testing',
            'productos_servicios': 'Test services',
            'palabras_clave': 'test, pytest',
            'capacidad_entrega_dias': 10,
            'ubicacion': 'Test City',
            'experiencia_anos': 5,
            'certificaciones': 'ISO-TEST',
            'alertas_activas': 1
        }
        
        # Save
        result = db_bot.guardar_perfil(test_user_id, test_perfil)
        assert result is True
        
        # Retrieve
        retrieved = db_bot.obtener_perfil(test_user_id)
        assert retrieved is not None
        assert retrieved['nombre_empresa'] == 'Test Company'
        assert retrieved['tipo_negocio'] == 'Testing'
        
        # Cleanup - delete the test profile
        conn = db_bot.get_connection()
        cursor = conn.cursor()
        placeholder = db_bot.get_placeholder()
        cursor.execute(
            f"DELETE FROM perfiles_empresas WHERE telegram_user_id = {placeholder}",
            (test_user_id,)
        )
        conn.commit()
        conn.close()


class TestDatabaseInitialization:
    """Tests for database initialization."""
    
    @pytest.mark.integration
    def test_iniciar_db_extendida_idempotent(self):
        """iniciar_db_extendida should be idempotent."""
        import database_extended as db
        
        # Should not raise even if called multiple times
        db.iniciar_db_extendida()
        db.iniciar_db_extendida()
        
        # Tables should exist
        conn = db.get_connection()
        cursor = conn.cursor()
        
        if db.USE_POSTGRES:
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
        else:
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master WHERE type='table'
            """)
        
        count = cursor.fetchone()[0]
        assert count > 0
        conn.close()
    
    @pytest.mark.integration
    def test_iniciar_db_bot_idempotent(self):
        """iniciar_db_bot should be idempotent."""
        import database_bot as db_bot
        
        # Should not raise even if called multiple times
        db_bot.iniciar_db_bot()
        db_bot.iniciar_db_bot()
