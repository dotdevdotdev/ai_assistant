from typing import Dict, Type, Any, TypeVar, Optional
from core.interfaces import audio, speech, assistant, clipboard

T = TypeVar("T")


class ProviderRegistry:
    _instance = None

    def __init__(self):
        self._providers: Dict[Type, Any] = {}
        self._configs: Dict[Type, Dict[str, Any]] = {}

    @classmethod
    def get_instance(cls) -> "ProviderRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_provider(
        self, interface: Type[T], provider: T, config: Dict[str, Any] = None
    ) -> None:
        """Register a provider implementation with optional configuration"""
        self._providers[interface] = provider
        if config is not None:
            self._configs[interface] = config
            print(f">>> Registered config for {interface.__name__}: {config}")

    def get_provider(self, interface: Type[T]) -> T:
        """Get the registered provider implementation"""
        if interface not in self._providers:
            raise KeyError(f"No provider registered for {interface.__name__}")
        return self._providers[interface]

    def get_provider_config(self, interface: Type[T]) -> Dict[str, Any]:
        """Get the configuration for a provider"""
        return self._configs.get(interface, {})

    def clear(self) -> None:
        """Clear all registered providers"""
        self._providers.clear()
        self._configs.clear()
