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
    settings: Dict[str, Any]


@dataclass
class ModuleConfig:
    provider_type: str
    config: Dict[str, Any]


@dataclass
class AppConfig:
    audio: ModuleConfig
    speech: ModuleConfig
    assistant: ModuleConfig
    clipboard: ModuleConfig
    ui: Dict[str, Any]
    assistants: List[AssistantConfig]

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
                    speech_provider = speech_dict.get("provider")
                    print(f"Found speech provider: {speech_provider}")

                    # Get the speech config
                    speech_config = speech_dict.get("config", {})
                    if speech_provider:
                        speech_config = speech_dict.get("config", {}).get(
                            speech_provider, {}
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

                    config = cls(
                        audio=ModuleConfig(
                            provider_type=audio_dict.get("provider", "pyaudio"),
                            config=audio_config,
                        ),
                        speech=ModuleConfig(
                            provider_type=speech_provider or "whisper",
                            config=speech_config,
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
                    )
                    print(
                        f"Created config object with speech provider: {config.speech.provider_type}"
                    )
                    print(f"Speech config: {config.speech.config}")

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
        for config_file in glob.glob("va-*.yaml"):
            try:
                with open(config_file, "r") as f:
                    config = yaml.safe_load(f)
                    assistant = AssistantConfig(
                        name=config.get("name", "Unnamed Assistant"),
                        description=config.get("description", ""),
                        system_prompt=config.get("system_prompt", ""),
                        model=config.get("model", "claude-3-opus-20240229"),
                        settings=config.get("settings", {}),
                    )
                    assistants.append(assistant)
                    print(f"Loaded assistant config from {config_file}")
            except Exception as e:
                print(f"Error loading assistant config {config_file}: {e}")
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
            speech=ModuleConfig(
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
            assistant=ModuleConfig(provider_type="anthropic", config={}),
            clipboard=ModuleConfig(provider_type="qt", config={}),
            ui={"theme": "dark", "window_size": [800, 600]},
            assistants=[],  # Will be populated from va-*.yaml files
        )

    def save(self, config_path: str) -> None:
        """Save configuration to a YAML file"""
        config_dict = {
            "audio": {
                "provider": self.audio.provider_type,
                "config": self.audio.config,
            },
            "speech": {
                "provider": self.speech.provider_type,
                "config": self.speech.config,
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
        }

        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, "w") as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False)
