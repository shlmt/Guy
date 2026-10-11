import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Optional

from .paths import CONFIG_FILE


@dataclass
class AppConfig:
    default_model: str = "gemini"
    api_keys: Dict[str, str] = field(default_factory=dict)


class ConfigManager:
    """Loads and manages application configuration."""

    _PROVIDER_ALIASES = {"google": "gemini"}

    def __init__(self, config_file: Path = CONFIG_FILE) -> None:
        self._config_file = Path(config_file)
        self._config = AppConfig()
        self.load()

    @classmethod
    def _normalize_provider(cls, provider: str) -> str:
        if not isinstance(provider, str) or not provider.strip():
            raise ValueError("provider must be a non-empty string")

        # Accept a provider name ("gemini") or a model spec ("gemini:flash").
        name = provider.strip().lower().split(":", maxsplit=1)[0].strip()
        return cls._PROVIDER_ALIASES.get(name, name)

    def load(self) -> AppConfig:
        """Reload the file into this manager and return the current config."""
        if not self._config_file.exists():
            self._config = AppConfig()
            return self._config

        try:
            with self._config_file.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as exc:
            # Do not silently replace a broken config with empty defaults.
            raise ValueError(
                f"Invalid JSON in config file: {self._config_file} (line {exc.lineno})"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(f"Config file must contain a JSON object: {self._config_file}")

        raw_api_keys = data.get("api_keys", {})
        if not isinstance(raw_api_keys, dict):
            raise ValueError("The 'api_keys' value in the config file must be an object")

        api_keys: Dict[str, str] = {}
        for provider, api_key in raw_api_keys.items():
            normalized_provider = self._normalize_provider(provider)
            if not isinstance(api_key, str):
                raise ValueError(f"API key for '{normalized_provider}' must be a string")
            if api_key.strip():
                api_keys[normalized_provider] = api_key.strip()

        self._config = AppConfig(
            default_model=data.get("default_model", "gemini:flash"),
            api_keys=api_keys,
        )
        return self._config

    def save(self) -> None:
        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        with self._config_file.open("w", encoding="utf-8") as file:
            json.dump(asdict(self._config), file, indent=4, ensure_ascii=False)

    @property
    def default_model(self) -> str:
        return self._config.default_model

    @default_model.setter
    def default_model(self, model_spec: str) -> None:
        self._config.default_model = model_spec
        self.save()

    @property
    def api_keys(self) -> Dict[str, str]:
        """Return a copy; use set_api_key() to change and persist keys."""
        return dict(self._config.api_keys)

    def get_api_key(self, provider: str) -> Optional[str]:
        provider_name = self._normalize_provider(provider)

        # A non-empty value in the config file takes precedence.
        api_key = self._config.api_keys.get(provider_name)
        if api_key and api_key.strip():
            return api_key.strip()

        # Fall back to environment variables.
        if provider_name == "gemini":
            return os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip() or None

        return os.getenv(f"{provider_name.upper()}_API_KEY", "").strip() or None

    def set_api_key(self, provider: str, api_key: str) -> None:
        provider_name = self._normalize_provider(provider)
        if not isinstance(api_key, str):
            raise ValueError("api_key must be a string")

        self._config.api_keys[provider_name] = api_key.strip()
        self.save()


# Import this object through one consistent package path throughout the application.
config = ConfigManager()
