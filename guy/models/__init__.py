from .registry import ModelRegistry
from ..config import config
from .gemini import GeminiProvider

default_model = config.default_model if config.default_model is not None else 'gemini'

model_registry = ModelRegistry(default_model)

model_registry.register_provider("gemini", GeminiProvider)
