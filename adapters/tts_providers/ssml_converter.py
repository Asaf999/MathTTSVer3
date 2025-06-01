"""
SSML converter for mathematical expressions.

Converts mathematical speech text to SSML format with proper
pauses, emphasis, and pronunciation hints.
"""

from typing import Dict, List, Optional, Tuple
import re
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

from src.domain.value_objects import SpeechText
from src.infrastructure.logging import get_logger


logger = get_logger(__name__)


class SSMLConverter:
    """Converts SpeechText to SSML format for TTS providers."""
    
    # Mathematical terms that should have emphasis
    EMPHASIS_TERMS = {
        'derivative', 'integral', 'limit', 'sum', 'product',
        'infinity', 'equals', 'prime', 'squared', 'cubed',
        'numerator', 'denominator', 'coefficient'
    }
    
    # Terms that should have a pause before them
    PAUSE_BEFORE_TERMS = {
        'equals', 'plus', 'minus', 'times', 'over', 'from', 'to',
        'where', 'such that', 'given', 'for all', 'there exists'
    }
    
    # Terms that should have a pause after them
    PAUSE_AFTER_TERMS = {
        'therefore', 'because', 'Q.E.D.', 'where', 'given'
    }
    
    def __init__(self, provider: str = "edge-tts"):
        """
        Initialize SSML converter.
        
        Args:
            provider: TTS provider name for provider-specific formatting
        """
        self.provider = provider
        
    def convert(self, speech_text: SpeechText) -> str:
        """
        Convert SpeechText to SSML.
        
        Args:
            speech_text: Speech text object
            
        Returns:
            SSML string
        """
        try:
            # Create root speak element
            speak = ET.Element('speak')
            speak.set('version', '1.0')
            speak.set('xml:lang', 'en-US')
            
            if self.provider == "edge-tts":
                speak.set('xmlns', 'http://www.w3.org/2001/10/synthesis')
                speak.set('xmlns:mstts', 'http://www.w3.org/2001/mstts')
            
            # Process the text
            processed_text = self._process_text(speech_text)
            
            # Add content to speak element
            self._add_content_to_speak(speak, processed_text)
            
            # Convert to string
            ssml = ET.tostring(speak, encoding='unicode', method='xml')
            
            # Clean up formatting
            ssml = self._format_ssml(ssml)
            
            logger.debug("Generated SSML", ssml_length=len(ssml))
            return ssml
            
        except Exception as e:
            logger.error("Failed to convert to SSML", error=str(e))
            # Fallback to plain text wrapped in speak tags
            return f'<speak>{escape(speech_text.plain_text)}</speak>'
    
    def _process_text(self, speech_text: SpeechText) -> List[Dict[str, any]]:
        """
        Process text into segments with metadata.
        
        Returns list of segments with:
        - text: The text content
        - type: 'text', 'pause', 'emphasis', etc.
        - attributes: Additional attributes
        """
        segments = []
        text = speech_text.plain_text
        
        # Split into words while preserving spaces
        words = re.findall(r'\S+|\s+', text)
        
        i = 0
        while i < len(words):
            word = words[i].strip()
            
            if not word:
                # Whitespace
                if words[i]:
                    segments.append({'text': words[i], 'type': 'text'})
                i += 1
                continue
            
            # Check for mathematical structures
            if self._is_fraction_start(word, words, i):
                # Handle fraction
                segments.extend(self._process_fraction(words, i))
                i = self._skip_fraction(words, i)
                
            elif self._is_expression_boundary(word):
                # Add pause at expression boundaries
                segments.append({'type': 'pause', 'duration': '200ms'})
                segments.append({'text': word, 'type': 'text'})
                segments.append({'type': 'pause', 'duration': '200ms'})
                i += 1
                
            elif word.lower() in self.EMPHASIS_TERMS:
                # Add emphasis
                segments.append({
                    'text': word,
                    'type': 'emphasis',
                    'level': 'moderate'
                })
                i += 1
                
            elif word.lower() in self.PAUSE_BEFORE_TERMS:
                # Add pause before
                segments.append({'type': 'pause', 'duration': '100ms'})
                segments.append({'text': word, 'type': 'text'})
                i += 1
                
            elif word.lower() in self.PAUSE_AFTER_TERMS:
                # Add pause after
                segments.append({'text': word, 'type': 'text'})
                segments.append({'type': 'pause', 'duration': '100ms'})
                i += 1
                
            else:
                # Regular text
                segments.append({'text': word, 'type': 'text'})
                i += 1
            
            # Add space if not at end
            if i < len(words) and words[i].isspace():
                segments.append({'text': words[i], 'type': 'text'})
                i += 1
        
        return segments
    
    def _add_content_to_speak(self, speak: ET.Element, segments: List[Dict]) -> None:
        """Add processed segments to speak element."""
        current_text = []
        
        for segment in segments:
            if segment['type'] == 'text':
                current_text.append(segment['text'])
                
            elif segment['type'] == 'pause':
                # Flush current text
                if current_text:
                    text = ''.join(current_text)
                    if text.strip():
                        speak.text = (speak.text or '') + text
                    current_text = []
                
                # Add break element
                break_elem = ET.SubElement(speak, 'break')
                break_elem.set('time', segment['duration'])
                
            elif segment['type'] == 'emphasis':
                # Flush current text
                if current_text:
                    text = ''.join(current_text)
                    if text.strip():
                        speak.text = (speak.text or '') + text
                    current_text = []
                
                # Add emphasis element
                emphasis = ET.SubElement(speak, 'emphasis')
                emphasis.set('level', segment.get('level', 'moderate'))
                emphasis.text = segment['text']
                
            elif segment['type'] == 'say-as':
                # Flush current text
                if current_text:
                    text = ''.join(current_text)
                    if text.strip():
                        speak.text = (speak.text or '') + text
                    current_text = []
                
                # Add say-as element
                say_as = ET.SubElement(speak, 'say-as')
                say_as.set('interpret-as', segment['interpret-as'])
                say_as.text = segment['text']
        
        # Flush remaining text
        if current_text:
            text = ''.join(current_text)
            if text.strip():
                if speak.text:
                    speak.text += text
                else:
                    # Find last element and append text after it
                    if len(speak) > 0:
                        speak[-1].tail = (speak[-1].tail or '') + text
                    else:
                        speak.text = text
    
    def _is_fraction_start(self, word: str, words: List[str], index: int) -> bool:
        """Check if this starts a fraction pattern."""
        # Look for "X over Y" pattern
        if index + 2 < len(words):
            next_word = words[index + 2].strip()
            return next_word.lower() == 'over'
        return False
    
    def _process_fraction(self, words: List[str], start_index: int) -> List[Dict]:
        """Process a fraction with appropriate pauses."""
        segments = []
        
        # Numerator
        segments.append({'text': words[start_index], 'type': 'text'})
        
        # Space
        if start_index + 1 < len(words) and words[start_index + 1].isspace():
            segments.append({'text': words[start_index + 1], 'type': 'text'})
        
        # "over" with slight pauses
        segments.append({'type': 'pause', 'duration': '50ms'})
        segments.append({'text': words[start_index + 2], 'type': 'text'})
        segments.append({'type': 'pause', 'duration': '50ms'})
        
        return segments
    
    def _skip_fraction(self, words: List[str], start_index: int) -> int:
        """Skip past fraction in word list."""
        # Skip numerator, space, "over"
        return start_index + 3
    
    def _is_expression_boundary(self, word: str) -> bool:
        """Check if word marks an expression boundary."""
        # Parentheses, brackets, etc.
        return word in ['(', ')', '[', ']', '{', '}']
    
    def _format_ssml(self, ssml: str) -> str:
        """Format SSML for readability."""
        # Remove extra whitespace
        ssml = re.sub(r'>\s+<', '><', ssml)
        
        # Add XML declaration
        if not ssml.startswith('<?xml'):
            ssml = '<?xml version="1.0" encoding="UTF-8"?>\n' + ssml
        
        return ssml
    
    def add_pronunciation_hints(
        self,
        ssml: str,
        hints: Dict[str, str]
    ) -> str:
        """
        Add pronunciation hints to SSML.
        
        Args:
            ssml: Base SSML
            hints: Dictionary of term -> pronunciation
            
        Returns:
            SSML with pronunciation hints added
        """
        try:
            root = ET.fromstring(ssml)
            
            # Find all text nodes and replace terms with phoneme elements
            for elem in root.iter():
                if elem.text:
                    text = elem.text
                    for term, pronunciation in hints.items():
                        if term in text:
                            # Create phoneme element
                            # This is simplified - real implementation would
                            # need to handle partial matches properly
                            text = text.replace(
                                term,
                                f'<phoneme alphabet="ipa" ph="{pronunciation}">{term}</phoneme>'
                            )
                    elem.text = text
            
            return ET.tostring(root, encoding='unicode', method='xml')
            
        except Exception as e:
            logger.error("Failed to add pronunciation hints", error=str(e))
            return ssml