"""
Multi-provider AI abstraction for CompraAgil.
Supports Gemini, Groq, Cerebras, and easily extensible for others.

Usage:
    from ai_providers import get_ai_provider, generate_completion
    
    # Use default provider from config
    response = generate_completion("Analiza esta licitación...")
    
    # Use specific provider
    provider = get_ai_provider("groq")
    response = provider.generate("Tu prompt aquí")
"""
import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger('compra_agil.ai_providers')


# ==================== DATA CLASSES ====================

@dataclass
class AIResponse:
    """Standardized response from any AI provider."""
    text: str
    provider: str
    model: str
    usage: Optional[Dict[str, int]] = None  # tokens used
    raw_response: Optional[Any] = None
    
    def to_json(self) -> Optional[dict]:
        """Try to parse response as JSON."""
        text = self.text.strip()
        
        # Clean markdown code blocks
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return None


# ==================== BASE PROVIDER ====================

class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    name: str = "base"
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self._configured = False
    
    @abstractmethod
    def configure(self) -> bool:
        """Configure the provider. Returns True if successful."""
        pass
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> AIResponse:
        """Generate a completion from a prompt."""
        pass
    
    @property
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        return self._configured and self.api_key is not None
    
    def generate_json(self, prompt: str, **kwargs) -> Optional[dict]:
        """Generate and parse as JSON."""
        response = self.generate(prompt, **kwargs)
        return response.to_json()


# ==================== GEMINI PROVIDER ====================

class GeminiProvider(AIProvider):
    """Google Gemini AI provider."""
    
    name = "gemini"
    default_model = "gemini-2.0-flash-exp"
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(
            api_key=api_key or os.getenv('GEMINI_API_KEY'),
            model=model or os.getenv('GEMINI_MODEL', self.default_model)
        )
        self._genai = None
    
    def configure(self) -> bool:
        if not self.api_key:
            logger.warning("Gemini: API key not configured")
            return False
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._genai = genai
            self._configured = True
            logger.info(f"Gemini configured with model: {self.model}")
            return True
        except ImportError:
            logger.error("Gemini: google-generativeai package not installed")
            return False
        except Exception as e:
            logger.error(f"Gemini configuration error: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> AIResponse:
        if not self._configured:
            self.configure()
        
        if not self._configured:
            raise RuntimeError("Gemini provider not configured")
        
        try:
            model = self._genai.GenerativeModel(self.model)
            response = model.generate_content(prompt)
            
            return AIResponse(
                text=response.text,
                provider=self.name,
                model=self.model,
                raw_response=response
            )
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise


# ==================== GROQ PROVIDER ====================

class GroqProvider(AIProvider):
    """Groq AI provider (fast inference)."""
    
    name = "groq"
    default_model = "llama-3.3-70b-versatile"  # Fast and capable
    
    # Available models on Groq
    MODELS = {
        "llama-3.3-70b-versatile": "Meta Llama 3.3 70B - Best for complex tasks",
        "llama-3.1-8b-instant": "Meta Llama 3.1 8B - Fast responses",
        "mixtral-8x7b-32768": "Mixtral 8x7B - Good balance",
        "gemma2-9b-it": "Google Gemma 2 9B - Efficient",
    }
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(
            api_key=api_key or os.getenv('GROQ_API_KEY'),
            model=model or os.getenv('GROQ_MODEL', self.default_model)
        )
        self._client = None
    
    def configure(self) -> bool:
        if not self.api_key:
            logger.warning("Groq: API key not configured")
            return False
        
        try:
            from groq import Groq
            self._client = Groq(api_key=self.api_key)
            self._configured = True
            logger.info(f"Groq configured with model: {self.model}")
            return True
        except ImportError:
            logger.error("Groq: groq package not installed. Run: pip install groq")
            return False
        except Exception as e:
            logger.error(f"Groq configuration error: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> AIResponse:
        if not self._configured:
            self.configure()
        
        if not self._configured:
            raise RuntimeError("Groq provider not configured")
        
        try:
            # Groq uses OpenAI-compatible API
            chat_completion = self._client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 4096),
            )
            
            response_text = chat_completion.choices[0].message.content
            
            usage = None
            if chat_completion.usage:
                usage = {
                    "prompt_tokens": chat_completion.usage.prompt_tokens,
                    "completion_tokens": chat_completion.usage.completion_tokens,
                    "total_tokens": chat_completion.usage.total_tokens
                }
            
            return AIResponse(
                text=response_text,
                provider=self.name,
                model=self.model,
                usage=usage,
                raw_response=chat_completion
            )
        except Exception as e:
            logger.error(f"Groq generation error: {e}")
            raise


# ==================== CEREBRAS PROVIDER ====================

class CerebrasProvider(AIProvider):
    """Cerebras AI provider (ultra-fast inference)."""
    
    name = "cerebras"
    default_model = "llama3.1-8b"  # Available on Cerebras
    
    # Available models on Cerebras
    MODELS = {
        "llama3.1-8b": "Llama 3.1 8B - Fast and efficient",
        "llama3.1-70b": "Llama 3.1 70B - More capable",
    }
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(
            api_key=api_key or os.getenv('CEREBRAS_API_KEY'),
            model=model or os.getenv('CEREBRAS_MODEL', self.default_model)
        )
        self._client = None
    
    def configure(self) -> bool:
        if not self.api_key:
            logger.warning("Cerebras: API key not configured")
            return False
        
        try:
            from cerebras.cloud.sdk import Cerebras
            self._client = Cerebras(api_key=self.api_key)
            self._configured = True
            logger.info(f"Cerebras configured with model: {self.model}")
            return True
        except ImportError:
            logger.error("Cerebras: cerebras-cloud-sdk not installed. Run: pip install cerebras-cloud-sdk")
            return False
        except Exception as e:
            logger.error(f"Cerebras configuration error: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> AIResponse:
        if not self._configured:
            self.configure()
        
        if not self._configured:
            raise RuntimeError("Cerebras provider not configured")
        
        try:
            # Cerebras uses OpenAI-compatible API
            chat_completion = self._client.chat.completions.create(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=kwargs.get('temperature', 0.7),
                max_tokens=kwargs.get('max_tokens', 4096),
            )
            
            response_text = chat_completion.choices[0].message.content
            
            usage = None
            if hasattr(chat_completion, 'usage') and chat_completion.usage:
                usage = {
                    "prompt_tokens": chat_completion.usage.prompt_tokens,
                    "completion_tokens": chat_completion.usage.completion_tokens,
                    "total_tokens": chat_completion.usage.total_tokens
                }
            
            return AIResponse(
                text=response_text,
                provider=self.name,
                model=self.model,
                usage=usage,
                raw_response=chat_completion
            )
        except Exception as e:
            logger.error(f"Cerebras generation error: {e}")
            raise


# ==================== OPENAI PROVIDER ====================

class OpenAIProvider(AIProvider):
    """OpenAI ChatGPT provider."""
    
    name = "openai"
    default_model = "gpt-4o-mini"  # Cost-effective default
    
    # Available models on OpenAI
    MODELS = {
        "gpt-4o": "GPT-4o - Most capable, multimodal",
        "gpt-4o-mini": "GPT-4o Mini - Fast and cost-effective",
        "gpt-4-turbo": "GPT-4 Turbo - Previous gen, 128k context",
        "gpt-3.5-turbo": "GPT-3.5 Turbo - Fast and cheap",
        "o1-preview": "o1 Preview - Advanced reasoning",
        "o1-mini": "o1 Mini - Fast reasoning",
    }
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        super().__init__(
            api_key=api_key or os.getenv('OPENAI_API_KEY'),
            model=model or os.getenv('OPENAI_MODEL', self.default_model)
        )
        self._client = None
    
    def configure(self) -> bool:
        if not self.api_key:
            logger.warning("OpenAI: API key not configured")
            return False
        
        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
            self._configured = True
            logger.info(f"OpenAI configured with model: {self.model}")
            return True
        except ImportError:
            logger.error("OpenAI: openai package not installed. Run: pip install openai")
            return False
        except Exception as e:
            logger.error(f"OpenAI configuration error: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> AIResponse:
        if not self._configured:
            self.configure()
        
        if not self._configured:
            raise RuntimeError("OpenAI provider not configured")
        
        try:
            # Check if using o1 models (they don't support temperature)
            is_o1_model = self.model.startswith('o1')
            
            create_params = {
                "messages": [{"role": "user", "content": prompt}],
                "model": self.model,
                "max_tokens": kwargs.get('max_tokens', 4096),
            }
            
            # o1 models don't support temperature parameter
            if not is_o1_model:
                create_params["temperature"] = kwargs.get('temperature', 0.7)
            
            chat_completion = self._client.chat.completions.create(**create_params)
            
            response_text = chat_completion.choices[0].message.content
            
            usage = None
            if chat_completion.usage:
                usage = {
                    "prompt_tokens": chat_completion.usage.prompt_tokens,
                    "completion_tokens": chat_completion.usage.completion_tokens,
                    "total_tokens": chat_completion.usage.total_tokens
                }
            
            return AIResponse(
                text=response_text,
                provider=self.name,
                model=self.model,
                usage=usage,
                raw_response=chat_completion
            )
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise


# ==================== PROVIDER REGISTRY ====================

PROVIDERS: Dict[str, type] = {
    "gemini": GeminiProvider,
    "groq": GroqProvider,
    "cerebras": CerebrasProvider,
    "openai": OpenAIProvider,
}

# Cached provider instances
_provider_instances: Dict[str, AIProvider] = {}


def get_ai_provider(name: Optional[str] = None) -> AIProvider:
    """
    Get an AI provider instance by name.
    
    Args:
        name: Provider name ('gemini', 'groq', 'cerebras'). 
              If None, uses AI_PROVIDER env var or defaults to 'gemini'.
    
    Returns:
        Configured AIProvider instance.
    """
    if name is None:
        name = os.getenv('AI_PROVIDER', 'gemini').lower()
    
    name = name.lower()
    
    if name not in PROVIDERS:
        available = ", ".join(PROVIDERS.keys())
        raise ValueError(f"Unknown provider: {name}. Available: {available}")
    
    # Return cached instance if available
    if name in _provider_instances:
        return _provider_instances[name]
    
    # Create and configure new instance
    provider_class = PROVIDERS[name]
    provider = provider_class()
    provider.configure()
    
    _provider_instances[name] = provider
    return provider


def get_available_providers() -> List[str]:
    """Get list of providers that are configured and available."""
    available = []
    for name, provider_class in PROVIDERS.items():
        try:
            provider = provider_class()
            if provider.configure():
                available.append(name)
        except Exception:
            pass
    return available


def generate_completion(
    prompt: str,
    provider: Optional[str] = None,
    **kwargs
) -> AIResponse:
    """
    Generate a completion using the specified or default provider.
    
    Args:
        prompt: The prompt to send to the AI.
        provider: Provider name (optional, uses default if not specified).
        **kwargs: Additional arguments passed to the provider.
    
    Returns:
        AIResponse with the generated text.
    """
    ai_provider = get_ai_provider(provider)
    return ai_provider.generate(prompt, **kwargs)


def generate_json(
    prompt: str,
    provider: Optional[str] = None,
    **kwargs
) -> Optional[dict]:
    """
    Generate a completion and parse it as JSON.
    
    Args:
        prompt: The prompt to send to the AI.
        provider: Provider name (optional).
        **kwargs: Additional arguments passed to the provider.
    
    Returns:
        Parsed JSON dict, or None if parsing fails.
    """
    response = generate_completion(prompt, provider, **kwargs)
    return response.to_json()


# ==================== FALLBACK CHAIN ====================

class FallbackChain:
    """
    Try multiple providers in order until one succeeds.
    Useful for resilience when one provider is down.
    """
    
    def __init__(self, providers: List[str]):
        """
        Args:
            providers: List of provider names in priority order.
        """
        self.provider_names = providers
        self._providers: List[AIProvider] = []
    
    def configure(self) -> bool:
        """Configure all providers in the chain."""
        for name in self.provider_names:
            try:
                provider = get_ai_provider(name)
                if provider.is_available:
                    self._providers.append(provider)
            except Exception as e:
                logger.warning(f"Failed to configure {name}: {e}")
        
        return len(self._providers) > 0
    
    def generate(self, prompt: str, **kwargs) -> AIResponse:
        """Try each provider until one succeeds."""
        last_error = None
        
        for provider in self._providers:
            try:
                return provider.generate(prompt, **kwargs)
            except Exception as e:
                logger.warning(f"{provider.name} failed: {e}, trying next...")
                last_error = e
        
        raise RuntimeError(f"All providers failed. Last error: {last_error}")


# ==================== MAIN ====================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
    
    logger.info("=" * 60)
    logger.info("AI PROVIDERS - Status Check")
    logger.info("=" * 60)
    
    for name, provider_class in PROVIDERS.items():
        provider = provider_class()
        configured = provider.configure()
        status = "OK" if configured else "NOT CONFIGURED"
        logger.info(f"  {name}: {status}")
        if configured:
            logger.info(f"    Model: {provider.model}")
    
    logger.info("=" * 60)
    
    # Test default provider
    default = os.getenv('AI_PROVIDER', 'gemini')
    logger.info(f"Default provider (AI_PROVIDER): {default}")
    
    available = get_available_providers()
    logger.info(f"Available providers: {', '.join(available) if available else 'None'}")
