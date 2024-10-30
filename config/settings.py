from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import yaml
import os
import glob


@dataclass
class AssistantConfig:
    name: str
    description: str
    system_prompt: str
    model: str
    username: Optional[str]
    provider_type: str  # "openai" or "anthropic"
    voice_settings: Optional[Dict[str, Any]]  # For elevenlabs settings
    settings: Dict[str, Any]  # For any other provider-specific settings

    @classmethod
    def from_yaml(cls, config: Dict[str, Any]) -> "AssistantConfig":
        # Determine provider type
        provider_type = "openai" if "openai" in config else "anthropic"
        provider_config = config.get(provider_type, {})

        return cls(
            name=config.get("va_name", "Unnamed Assistant"),
            description=f"Assistant with personality: {config.get('va_name')}",
            system_prompt=provider_config.get("system_prompt", ""),
            model=provider_config.get("model", ""),
            username=config.get("user", {}).get("username"),
            provider_type=provider_type,
            voice_settings=config.get("elevenlabs"),
            settings=provider_config.get("settings", {}),
        )


@dataclass
class ModuleConfig:
    provider_type: str
    config: Dict[str, Any]


@dataclass
class LLMProviderConfig:
    default_model: str
    models: List[str]


@dataclass
class LLMConfig:
    providers: Dict[str, LLMProviderConfig]
    default_system_prompt: str = "You are a conversational AI, speak in short sentences and use natural language."

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LLMConfig":
        providers = {
            name: LLMProviderConfig(**provider_data)
            for name, provider_data in data.get("providers", {}).items()
        }
        return cls(
            providers=providers,
            default_system_prompt=data.get(
                "default_system_prompt",
                "You are a conversational AI, speak in short sentences and use natural language.",
            ),
        )

    def save(self) -> Dict[str, Any]:
        return {
            "default_system_prompt": self.default_system_prompt,
            "providers": {
                name: {
                    "default_model": provider.default_model,
                    "models": provider.models,
                }
                for name, provider in self.providers.items()
            },
        }


@dataclass
class SpeechConfig:
    stt: ModuleConfig  # Speech-to-Text config
    tts: ModuleConfig  # Text-to-Speech config


@dataclass
class AppConfig:
    audio: ModuleConfig
    speech: SpeechConfig  # Changed from ModuleConfig to SpeechConfig
    assistant: ModuleConfig
    clipboard: ModuleConfig
    ui: Dict[str, Any]
    assistants: List[AssistantConfig]
    llm: LLMConfig

    @classmethod
    def load(cls, config_path: str) -> "AppConfig":
        """Load configuration from a YAML file, creating it if it doesn't exist"""
        config = None
        assistants = cls._load_assistant_configs()

        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config_dict = yaml.safe_load(f)
                    print(f"Loading config from: {os.path.abspath(config_path)}")
                    print(f"Raw config contents: {config_dict}")

                    # Get the speech provider settings
                    speech_dict = config_dict.get("speech", {})
                    speech_provider_type = speech_dict.get("provider_type")
                    print(f"Found speech provider: {speech_provider_type}")

                    # Get the speech config
                    speech_config = speech_dict.get("config", {})
                    if speech_provider_type:
                        speech_config = speech_dict.get("config", {}).get(
                            speech_provider_type, {}
                        )
                    print(f"Speech config: {speech_config}")

                    # Get audio settings
                    audio_dict = config_dict.get("audio", {})
                    audio_config = audio_dict.get("config", {})

                    # Get app settings
                    app_settings = config_dict.get("app", {})
                    if app_settings:
                        # Add device settings to audio config
                        audio_config["input_device"] = app_settings.get("input_device")
                        audio_config["output_device"] = app_settings.get(
                            "output_device"
                        )
                    print(f"Audio config with devices: {audio_config}")

                    # Convert LLM section to proper config object
                    llm_data = config_dict.get("llm", {})
                    llm_config = LLMConfig.from_dict(llm_data)

                    config = cls(
                        audio=ModuleConfig(
                            provider_type=audio_dict.get("provider", "pyaudio"),
                            config=audio_config,
                        ),
                        speech=SpeechConfig(
                            stt=ModuleConfig(
                                provider_type=speech_dict.get("stt", {}).get(
                                    "provider_type", "whisper"
                                ),
                                config=speech_dict.get("stt", {}).get("config", {}),
                            ),
                            tts=ModuleConfig(
                                provider_type=speech_dict.get("tts", {}).get(
                                    "provider_type", "elevenlabs"
                                ),
                                config=speech_dict.get("tts", {}).get("config", {}),
                            ),
                        ),
                        assistant=ModuleConfig(
                            provider_type=config_dict.get("assistant", {}).get(
                                "provider", "anthropic"
                            ),
                            config=config_dict.get("assistant", {}).get("config", {}),
                        ),
                        clipboard=ModuleConfig(
                            provider_type=config_dict.get("clipboard", {}).get(
                                "provider", "qt"
                            ),
                            config=config_dict.get("clipboard", {}).get("config", {}),
                        ),
                        ui=config_dict.get("ui", {}),
                        assistants=assistants,
                        llm=llm_config,
                    )

                    print(
                        f"Created config object with speech provider: {config.speech.stt.provider_type}"
                    )
                    print(f"Speech config: {config.speech.stt.config}")

            except Exception as e:
                print(f"Error loading config from {config_path}: {e}")
                import traceback

                traceback.print_exc()
                config = None

        if config is None:
            print(f"Using default config (failed to load {config_path})")
            config = cls.get_default_config()
            config.assistants = assistants
            config.save(config_path)
            print(f"Created default configuration at {config_path}")

        return config

    @staticmethod
    def _load_assistant_configs() -> List[AssistantConfig]:
        """Load all va-*.yaml files from root directory"""
        assistants = []

        # Get available providers and models from llm config
        with open("app-settings.yaml") as f:
            app_config = yaml.safe_load(f)
            available_providers = app_config.get("llm", {}).get("providers", {})

        for config_file in glob.glob("va-*.yaml"):
            try:
                print(f"\n=== Loading assistant config from {config_file} ===")
                with open(config_file, "r") as f:
                    config = yaml.safe_load(f)
                    print(f">>> Raw config: {config}")

                    # Determine provider and validate
                    provider_type = "openai" if "openai" in config else "anthropic"
                    if provider_type not in available_providers:
                        print(
                            f"!!! Provider {provider_type} not supported, trying fallback..."
                        )
                        # Try alternate provider
                        provider_type = next(iter(available_providers.keys()))
                        print(f">>> Using fallback provider: {provider_type}")

                    provider_config = available_providers[provider_type]

                    # Get model and validate with fallbacks
                    model = config.get(provider_type, {}).get("model")
                    if not model or model not in provider_config["models"]:
                        print(
                            f"!!! Model {model} not available, using provider default"
                        )
                        model = provider_config["default_model"]
                        print(f">>> Using default model: {model}")

                    # Create assistant config
                    assistant = AssistantConfig(
                        name=config.get("va_name", "Unnamed Assistant"),
                        description=f"Assistant loaded from {config_file}",
                        system_prompt=config.get(provider_type, {}).get(
                            "system_prompt", ""
                        ),
                        model=model,
                        username=config.get("user", {}).get("username"),
                        provider_type=provider_type,
                        voice_settings=config.get("elevenlabs"),
                        settings=config.get("settings", {}),
                    )

                    print(f">>> Loaded assistant: {assistant.name}")
                    print(f">>> Using provider: {provider_type}")
                    print(f">>> Using model: {model}")
                    print(f">>> System prompt: {assistant.system_prompt[:100]}...")

                    assistants.append(assistant)

            except Exception as e:
                print(f"!!! Error loading assistant config {config_file}: {e}")
                import traceback

                traceback.print_exc()

        print(f"\n>>> Loaded {len(assistants)} total assistants")
        return assistants

    @staticmethod
    def get_default_config() -> "AppConfig":
        """Get default configuration"""
        return AppConfig(
            audio=ModuleConfig(
                provider_type="pyaudio",
                config={
                    "sample_rate": 16000,
                    "channels": 1,
                    "chunk_size": 1024,
                    "input_device": None,  # Will be set to system default
                    "output_device": None,  # Will be set to system default
                },
            ),
            speech=SpeechConfig(
                stt=ModuleConfig(
                    provider_type="whisper",
                    config={
                        "whisper": {
                            "model": "base",
                        },
                        "deepgram": {
                            "model": "nova-2",
                            "language": "en",
                            "smart_format": True,
                            "encoding": "linear16",
                        },
                    },
                ),
                tts=ModuleConfig(
                    provider_type="elevenlabs",
                    config={
                        "elevenlabs": {
                            "model_id": "eleven_turbo_v2_5",
                            "voice_id": "Crm8VULvkVs5ZBDa1Ixm",
                            "voice_settings": {
                                "stability": 0.49,
                                "similarity_boost": 0.49,
                                "style": 0.49,
                                "speaker_boost": True,
                            },
                        },
                        "f5tts": {
                            "model": "F5-TTS",
                            "reference_audio_dir": "reference_audio",
                        },
                    },
                ),
            ),
            assistant=ModuleConfig(provider_type="anthropic", config={}),
            clipboard=ModuleConfig(provider_type="qt", config={}),
            ui={"theme": "dark", "window_size": [800, 600]},
            assistants=[],  # Will be populated from va-*.yaml files
            llm=LLMConfig(providers={}),
        )

    def save(self, config_path: str) -> None:
        """Save configuration to a YAML file"""
        config_dict = {
            "audio": {
                "provider": self.audio.provider_type,
                "config": self.audio.config,
            },
            "speech": {
                "provider": self.speech.stt.provider_type,
                "config": self.speech.stt.config,
            },
            "assistant": {
                "provider": self.assistant.provider_type,
                "config": self.assistant.config,
            },
            "clipboard": {
                "provider": self.clipboard.provider_type,
                "config": self.clipboard.config,
            },
            "ui": self.ui,
            "llm": self.llm.save(),  # Use the new save method
        }

        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False)
