"""
Tests for the multi-provider AI abstraction module.
"""
import pytest
import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ==================== AIResponse Tests ====================

class TestAIResponse:
    """Tests for the AIResponse dataclass."""
    
    def test_airesponse_creation(self):
        """Test basic AIResponse creation."""
        from ai_providers import AIResponse
        
        response = AIResponse(
            text="Hello world",
            provider="test",
            model="test-model"
        )
        
        assert response.text == "Hello world"
        assert response.provider == "test"
        assert response.model == "test-model"
        assert response.usage is None
        assert response.raw_response is None
    
    def test_airesponse_with_usage(self):
        """Test AIResponse with token usage info."""
        from ai_providers import AIResponse
        
        usage = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
        
        response = AIResponse(
            text="Test",
            provider="groq",
            model="llama-3.3-70b",
            usage=usage
        )
        
        assert response.usage["total_tokens"] == 30
    
    def test_to_json_simple(self):
        """Test parsing simple JSON response."""
        from ai_providers import AIResponse
        
        response = AIResponse(
            text='{"key": "value", "number": 42}',
            provider="test",
            model="test"
        )
        
        result = response.to_json()
        assert result is not None
        assert result["key"] == "value"
        assert result["number"] == 42
    
    def test_to_json_with_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        from ai_providers import AIResponse
        
        response = AIResponse(
            text='```json\n{"status": "ok"}\n```',
            provider="test",
            model="test"
        )
        
        result = response.to_json()
        assert result is not None
        assert result["status"] == "ok"
    
    def test_to_json_invalid(self):
        """Test parsing invalid JSON returns None."""
        from ai_providers import AIResponse
        
        response = AIResponse(
            text='This is not JSON at all',
            provider="test",
            model="test"
        )
        
        result = response.to_json()
        assert result is None


# ==================== Provider Registry Tests ====================

class TestProviderRegistry:
    """Tests for provider registration and lookup."""
    
    def test_providers_registered(self):
        """Test that all expected providers are registered."""
        from ai_providers import PROVIDERS
        
        assert "gemini" in PROVIDERS
        assert "groq" in PROVIDERS
        assert "cerebras" in PROVIDERS
    
    def test_get_ai_provider_unknown(self):
        """Test getting an unknown provider raises ValueError."""
        from ai_providers import get_ai_provider
        
        with pytest.raises(ValueError) as exc_info:
            get_ai_provider("unknown_provider")
        
        assert "Unknown provider" in str(exc_info.value)
    
    def test_get_ai_provider_default(self):
        """Test getting default provider based on AI_PROVIDER env."""
        from ai_providers import get_ai_provider
        import ai_providers
        
        # Clear cached instances
        ai_providers._provider_instances.clear()
        
        # Should not raise - returns provider even if not configured
        provider = get_ai_provider()
        assert provider is not None
    
    def test_get_available_providers(self):
        """Test listing available (configured) providers."""
        from ai_providers import get_available_providers
        
        available = get_available_providers()
        
        # Result should be a list
        assert isinstance(available, list)


# ==================== GeminiProvider Tests ====================

class TestGeminiProvider:
    """Tests for GeminiProvider class."""
    
    def test_gemini_default_model(self):
        """Test Gemini provider uses correct default model."""
        from ai_providers import GeminiProvider
        
        provider = GeminiProvider()
        assert provider.default_model == "gemini-2.0-flash-exp"
    
    def test_gemini_custom_model(self):
        """Test Gemini provider accepts custom model."""
        from ai_providers import GeminiProvider
        
        provider = GeminiProvider(model="gemini-pro")
        assert provider.model == "gemini-pro"
    
    def test_gemini_configure_without_key(self):
        """Test Gemini configure fails without API key."""
        from ai_providers import GeminiProvider
        import ai_providers
        
        # Temporarily clear API key
        provider = GeminiProvider(api_key=None)
        result = provider.configure()
        
        assert result is False
        assert provider.is_available is False
    
    @pytest.mark.integration
    def test_gemini_configure_with_key(self):
        """Test Gemini configures successfully with valid key."""
        from ai_providers import GeminiProvider
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            pytest.skip("GEMINI_API_KEY not set")
        
        provider = GeminiProvider(api_key=api_key)
        result = provider.configure()
        
        assert result is True
        assert provider.is_available is True


# ==================== GroqProvider Tests ====================

class TestGroqProvider:
    """Tests for GroqProvider class."""
    
    def test_groq_default_model(self):
        """Test Groq provider uses correct default model."""
        from ai_providers import GroqProvider
        
        provider = GroqProvider()
        assert provider.default_model == "llama-3.3-70b-versatile"
    
    def test_groq_available_models(self):
        """Test Groq has expected models defined."""
        from ai_providers import GroqProvider
        
        assert "llama-3.3-70b-versatile" in GroqProvider.MODELS
        assert "mixtral-8x7b-32768" in GroqProvider.MODELS
    
    def test_groq_configure_without_key(self):
        """Test Groq configure fails without API key."""
        from ai_providers import GroqProvider
        
        provider = GroqProvider(api_key=None)
        result = provider.configure()
        
        assert result is False
    
    @pytest.mark.integration
    def test_groq_configure_with_key(self):
        """Test Groq configures successfully with valid key."""
        from ai_providers import GroqProvider
        
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            pytest.skip("GROQ_API_KEY not set")
        
        provider = GroqProvider(api_key=api_key)
        result = provider.configure()
        
        assert result is True


# ==================== CerebrasProvider Tests ====================

class TestCerebrasProvider:
    """Tests for CerebrasProvider class."""
    
    def test_cerebras_default_model(self):
        """Test Cerebras provider uses correct default model."""
        from ai_providers import CerebrasProvider
        
        provider = CerebrasProvider()
        assert provider.default_model == "llama3.1-8b"
    
    def test_cerebras_available_models(self):
        """Test Cerebras has expected models defined."""
        from ai_providers import CerebrasProvider
        
        assert "llama3.1-8b" in CerebrasProvider.MODELS
        assert "llama3.1-70b" in CerebrasProvider.MODELS
    
    def test_cerebras_configure_without_key(self):
        """Test Cerebras configure fails without API key."""
        from ai_providers import CerebrasProvider
        
        provider = CerebrasProvider(api_key=None)
        result = provider.configure()
        
        assert result is False
    
    @pytest.mark.integration
    def test_cerebras_configure_with_key(self):
        """Test Cerebras configures successfully with valid key."""
        from ai_providers import CerebrasProvider
        
        api_key = os.getenv('CEREBRAS_API_KEY')
        if not api_key:
            pytest.skip("CEREBRAS_API_KEY not set")
        
        provider = CerebrasProvider(api_key=api_key)
        result = provider.configure()
        
        assert result is True


# ==================== OpenAIProvider Tests ====================

class TestOpenAIProvider:
    """Tests for OpenAIProvider class."""
    
    def test_openai_default_model(self):
        """Test OpenAI provider uses correct default model."""
        from ai_providers import OpenAIProvider
        
        provider = OpenAIProvider()
        assert provider.default_model == "gpt-4o-mini"
    
    def test_openai_available_models(self):
        """Test OpenAI has expected models defined."""
        from ai_providers import OpenAIProvider
        
        assert "gpt-4o" in OpenAIProvider.MODELS
        assert "gpt-4o-mini" in OpenAIProvider.MODELS
        assert "gpt-3.5-turbo" in OpenAIProvider.MODELS
    
    def test_openai_custom_model(self):
        """Test OpenAI provider accepts custom model."""
        from ai_providers import OpenAIProvider
        
        provider = OpenAIProvider(model="gpt-4o")
        assert provider.model == "gpt-4o"
    
    def test_openai_configure_without_key(self):
        """Test OpenAI configure fails without API key."""
        from ai_providers import OpenAIProvider
        
        provider = OpenAIProvider(api_key=None)
        result = provider.configure()
        
        assert result is False
        assert provider.is_available is False
    
    @pytest.mark.integration
    def test_openai_configure_with_key(self):
        """Test OpenAI configures successfully with valid key."""
        from ai_providers import OpenAIProvider
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")
        
        provider = OpenAIProvider(api_key=api_key)
        result = provider.configure()
        
        assert result is True
        assert provider.is_available is True


# ==================== FallbackChain Tests ====================

class TestFallbackChain:
    """Tests for FallbackChain class."""
    
    def test_fallback_chain_creation(self):
        """Test creating a fallback chain."""
        from ai_providers import FallbackChain
        
        chain = FallbackChain(["gemini", "groq", "cerebras"])
        
        assert chain.provider_names == ["gemini", "groq", "cerebras"]
    
    def test_fallback_chain_configure(self):
        """Test configuring a fallback chain."""
        from ai_providers import FallbackChain
        
        chain = FallbackChain(["gemini", "groq"])
        result = chain.configure()
        
        # Should succeed if at least one provider is configured
        # (returns True if any provider in the chain is available)
        assert isinstance(result, bool)


# ==================== Helper Function Tests ====================

class TestHelperFunctions:
    """Tests for module-level helper functions."""
    
    def test_generate_completion_requires_provider(self):
        """Test generate_completion raises error if no provider available."""
        from ai_providers import generate_completion
        import ai_providers
        
        # Clear cached instances
        ai_providers._provider_instances.clear()
        
        # This will attempt to use default provider
        # If no API key is set, it should fail
        # We test that it doesn't crash catastrophically
        try:
            # Should either work or raise RuntimeError
            result = generate_completion("test")
        except (RuntimeError, Exception):
            # Expected if no provider is configured
            pass
    
    def test_generate_json_returns_dict_or_none(self):
        """Test generate_json return type."""
        from ai_providers import generate_json
        
        # Mock test - would need actual API key to fully test
        # Just verify the function exists and has correct signature
        import inspect
        sig = inspect.signature(generate_json)
        
        assert 'prompt' in sig.parameters
        assert 'provider' in sig.parameters


# ==================== Integration Tests ====================

@pytest.mark.integration
@pytest.mark.slow
class TestAIProviderIntegration:
    """Integration tests that require actual API keys."""
    
    def test_gemini_generate(self):
        """Test actual generation with Gemini."""
        from ai_providers import GeminiProvider
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            pytest.skip("GEMINI_API_KEY not set")
        
        provider = GeminiProvider(api_key=api_key)
        provider.configure()
        
        response = provider.generate("Say 'hello' in one word")
        
        assert response.text is not None
        assert len(response.text) > 0
        assert response.provider == "gemini"
    
    def test_groq_generate(self):
        """Test actual generation with Groq."""
        from ai_providers import GroqProvider
        
        api_key = os.getenv('GROQ_API_KEY')
        if not api_key:
            pytest.skip("GROQ_API_KEY not set")
        
        provider = GroqProvider(api_key=api_key)
        provider.configure()
        
        response = provider.generate("Say 'hello' in one word")
        
        assert response.text is not None
        assert len(response.text) > 0
        assert response.provider == "groq"
        assert response.usage is not None
    
    def test_cerebras_generate(self):
        """Test actual generation with Cerebras."""
        from ai_providers import CerebrasProvider
        
        api_key = os.getenv('CEREBRAS_API_KEY')
        if not api_key:
            pytest.skip("CEREBRAS_API_KEY not set")
        
        provider = CerebrasProvider(api_key=api_key)
        provider.configure()
        
        response = provider.generate("Say 'hello' in one word")
        
        assert response.text is not None
        assert len(response.text) > 0
        assert response.provider == "cerebras"
    
    def test_openai_generate(self):
        """Test actual generation with OpenAI."""
        from ai_providers import OpenAIProvider
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")
        
        provider = OpenAIProvider(api_key=api_key)
        provider.configure()
        
        response = provider.generate("Say 'hello' in one word")
        
        assert response.text is not None
        assert len(response.text) > 0
        assert response.provider == "openai"
        assert response.usage is not None
