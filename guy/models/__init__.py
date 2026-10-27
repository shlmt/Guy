from ..config import config
from .base import ModelFactory, ModelTier
from .gemini import GeminiProvider
from .registry import ModelRegistry

default_model = config.default_model if config.default_model is not None else "gemini"

model_registry = ModelRegistry(default_model)

model_registry.register_provider("gemini", GeminiProvider)
