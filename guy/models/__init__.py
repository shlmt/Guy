from typing import Dict, Type, Optional
from pydantic_ai.models import Model
from .base import ModelFactory
from .gemini import GeminiProvider


class ModelRegistry:
    """
    Manages active models, provider registries, and fallback logic.
    """

    def __init__(self, default_model: str):
        self._providers: Dict[str, Type[ModelFactory]] = {}
        self.active_model_spec: str = default_model

        # Register default providers
        self.register_provider("gemini", GeminiProvider)


    def register_provider(self, provider_name: str, provider_class: Type[ModelFactory]):
        """
        Registers a new model provider.
        """
        self._providers[provider_name.lower()] = provider_class


    def set_active_model(self, model_spec: str) -> None:
        """
        Updates the active model specification (e.g., 'openai:gpt-4o-mini').
        """
        provider_name, _ = self._parse_model_spec(model_spec)
        if provider_name not in self._providers:
            raise ValueError(f"Provider '{provider_name}' is not registered.")
        self.active_model_spec = model_spec


    def get_current_model(self) -> Model | str:
        """
        Instantiates and returns the current PydanticAI Model instance.
        """
        provider_name, model_name = self._parse_model_spec(self.active_model_spec)
        provider_cls = self._providers[provider_name]
        
        provider_instance = provider_cls(model_name=model_name)
        return provider_instance.build_model()


    def _parse_model_spec(self, model_spec: str) -> tuple[str, Optional[str]]:
        """
        Parses a model spec string formatted as 'provider:model_name'.
        """
        if ":" in model_spec:
            provider_name, model_name = model_spec.split(":", 1)
        else:
            provider_name = model_spec
            model_name = None

        return provider_name, model_name