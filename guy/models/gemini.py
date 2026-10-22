from typing import Dict

from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from ..ui import app_ui
from .base import ModelFactory, ModelTier


class GeminiProvider(ModelFactory):
    """
    Gemini model provider implementation.
    """

    MODELS: Dict[str, ModelTier] = {
        "flash-lite": ModelTier(api_name="gemini-3.5-flash-lite", rank=1),
        "flash": ModelTier(api_name="gemini-3.8-flash", rank=2),
        "pro": ModelTier(api_name="gemini-2.5-pro", rank=3),
    }

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _create_model(self) -> GoogleModel:
        tier_info = self.MODELS.get(self.model_name)

        # choose the actual API name based on the model tier or fallback to the provided model name
        actual_api_name = tier_info.api_name if tier_info else self.model_name

        if not tier_info:
            app_ui.display_warning(
                f"Model '{self.model_name}' is not in the predefined list. Using fallback API name: {actual_api_name}."
            )

        provider = GoogleProvider(api_key=self._api_key)
        return GoogleModel(actual_api_name, provider=provider)
