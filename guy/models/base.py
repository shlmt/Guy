from abc import ABC, abstractmethod
from dataclasses import dataclass

from pydantic_ai.models import Model

from ..config import config


@dataclass
class ModelTier:
    api_name: str
    rank: int


class ModelFactory(ABC):
    """
    Abstract Base Class for all model providers.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._api_key = config.get_api_key(self.provider_name)

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Unique string identifier for the provider (e.g., 'openai', 'anthropic').
        """
        pass

    def build_model(self) -> Model | str:
        """
        public function to build the model. Performs global sanity checks and then calls the specific implementation.
        """
        if not self._api_key:
            raise ValueError(
                f"API key for provider '{self.provider_name}' is missing. "
                # f"Please set it using: /model {self.provider_name} set-api-key <YOUR_KEY>"
            )

        return self._create_model()

    @abstractmethod
    def _create_model(self) -> Model | str:
        """
        This method should be implemented by subclasses to create and return the actual model instance.
        """
        pass
