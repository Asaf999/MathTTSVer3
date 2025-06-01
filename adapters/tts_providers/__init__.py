"""
TTS provider adapters.
"""

from .edge_tts_adapter import EdgeTTSAdapter
from .gtts_adapter import GTTSAdapter
from .pyttsx3_adapter import Pyttsx3Adapter
from .mock_tts_adapter import MockTTSAdapter

__all__ = [
    "EdgeTTSAdapter",
    "GTTSAdapter", 
    "Pyttsx3Adapter",
    "MockTTSAdapter"
]