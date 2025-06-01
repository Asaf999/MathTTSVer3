"""
Mathematical Rhythm Processor for Stage 4
Adds natural pauses, emphasis, and rhythm to mathematical speech
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class PauseLength(Enum):
    """Different pause lengths for mathematical rhythm"""
    SHORT = "short"      # 200ms - for minor separations
    MEDIUM = "medium"    # 400ms - for major operations
    LONG = "long"        # 600ms - for concept transitions
    DRAMATIC = "dramatic" # 800ms - for important revelations


class EmphasisLevel(Enum):
    """Emphasis levels for important mathematical terms"""
    MILD = "mild"
    MODERATE = "moderate"
    STRONG = "strong"
    DRAMATIC = "dramatic"


@dataclass
class RhythmContext:
    """Context for rhythm processing decisions"""
    is_definition: bool = False
    is_theorem: bool = False
    is_proof: bool = False
    is_complex_expression: bool = False
    audience_level: str = "undergraduate"
    teaching_mode: bool = True


class MathematicalRhythmProcessor:
    """
    Stage 4: Add natural pauses and emphasis to mathematical speech
    Creates professor-like rhythm and flow in mathematical narration
    """
    
    def __init__(self):
        # Pause patterns for mathematical operations
        self.operation_pauses = {
            # Major operations get medium pauses
            "equals": PauseLength.MEDIUM,
            "plus": PauseLength.SHORT,
            "minus": PauseLength.SHORT,
            "times": PauseLength.SHORT,
            "divided by": PauseLength.MEDIUM,
            "over": PauseLength.MEDIUM,
            
            # Logical connectors get medium pauses
            "therefore": PauseLength.MEDIUM,
            "thus": PauseLength.MEDIUM,
            "hence": PauseLength.MEDIUM,
            "because": PauseLength.MEDIUM,
            "since": PauseLength.MEDIUM,
            
            # Conceptual transitions get long pauses
            "which means": PauseLength.LONG,
            "this shows": PauseLength.LONG,
            "revealing": PauseLength.LONG,
            "demonstrating": PauseLength.LONG
        }
        
        # Terms that deserve emphasis
        self.emphasis_terms = {
            # Strong emphasis for conclusions
            "therefore": EmphasisLevel.STRONG,
            "thus": EmphasisLevel.STRONG,
            "hence": EmphasisLevel.STRONG,
            "conclude": EmphasisLevel.STRONG,
            
            # Moderate emphasis for important concepts
            "fundamental": EmphasisLevel.MODERATE,
            "theorem": EmphasisLevel.MODERATE,
            "proof": EmphasisLevel.MODERATE,
            "lemma": EmphasisLevel.MODERATE,
            "definition": EmphasisLevel.MODERATE,
            
            # Dramatic emphasis for beauty and wonder
            "remarkable": EmphasisLevel.DRAMATIC,
            "beautiful": EmphasisLevel.DRAMATIC,
            "elegant": EmphasisLevel.DRAMATIC,
            "profound": EmphasisLevel.DRAMATIC,
            "extraordinary": EmphasisLevel.DRAMATIC
        }
        
        # Rhythm patterns for different mathematical contexts
        self.context_rhythms = {
            "definition": {
                "intro_pause": PauseLength.LONG,
                "internal_pauses": PauseLength.SHORT,
                "conclusion_pause": PauseLength.MEDIUM
            },
            "theorem": {
                "intro_pause": PauseLength.DRAMATIC,
                "internal_pauses": PauseLength.MEDIUM,
                "conclusion_pause": PauseLength.LONG
            },
            "proof": {
                "intro_pause": PauseLength.LONG,
                "internal_pauses": PauseLength.SHORT,
                "conclusion_pause": PauseLength.DRAMATIC
            }
        }

    def add_mathematical_rhythm(self, text: str, context: Optional[RhythmContext] = None) -> str:
        """
        Add natural pauses and emphasis to mathematical speech
        
        Args:
            text: The mathematical narration text
            context: Optional context for rhythm decisions
            
        Returns:
            Text with rhythm markup for TTS processing
        """
        if context is None:
            context = RhythmContext()
        
        # Apply different rhythm processing stages
        text = self._add_operation_pauses(text)
        text = self._add_emphasis_markup(text)
        text = self._add_conceptual_pauses(text, context)
        text = self._add_breathing_points(text)
        text = self._add_dramatic_pauses(text, context)
        text = self._optimize_rhythm_flow(text)
        
        return text.strip()

    def _add_operation_pauses(self, text: str) -> str:
        """Add pauses before and after mathematical operations"""
        for operation, pause_length in self.operation_pauses.items():
            # Add pause before operation
            pattern = rf'\b({operation})\b'
            
            if pause_length == PauseLength.SHORT:
                replacement = r'<pause:200ms> \1'
            elif pause_length == PauseLength.MEDIUM:
                replacement = r'<pause:400ms> \1'
            elif pause_length == PauseLength.LONG:
                replacement = r'<pause:600ms> \1'
            else:  # DRAMATIC
                replacement = r'<pause:800ms> \1'
            
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Also add pauses after commas for natural flow
        text = re.sub(r',\s*', r', <pause:300ms>', text)
        
        return text

    def _add_emphasis_markup(self, text: str) -> str:
        """Add emphasis to important mathematical terms"""
        for term, emphasis_level in self.emphasis_terms.items():
            pattern = rf'\b({term})\b'
            
            if emphasis_level == EmphasisLevel.MILD:
                replacement = r'<emphasis level="mild">\1</emphasis>'
            elif emphasis_level == EmphasisLevel.MODERATE:
                replacement = r'<emphasis level="moderate">\1</emphasis>'
            elif emphasis_level == EmphasisLevel.STRONG:
                replacement = r'<emphasis level="strong">\1</emphasis>'
            else:  # DRAMATIC
                replacement = r'<emphasis level="dramatic">\1</emphasis>'
            
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text

    def _add_conceptual_pauses(self, text: str, context: RhythmContext) -> str:
        """Add pauses for conceptual transitions and explanations"""
        # Pause before explanatory phrases
        explanatory_patterns = [
            (r'(, which\s+)', '<pause:400ms>\\1'),
            (r'(, meaning\s+)', '<pause:400ms>\\1'),
            (r'(, showing\s+)', '<pause:400ms>\\1'),
            (r'(, revealing\s+)', '<pause:600ms>\\1'),
            (r'(, demonstrating\s+)', '<pause:600ms>\\1')
        ]
        
        for pattern, replacement in explanatory_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        # Add pauses around parenthetical explanations
        text = re.sub(r'\s*\(', ' <pause:300ms>(', text)
        text = re.sub(r'\)\s*', ')<pause:300ms> ', text)
        
        return text

    def _add_breathing_points(self, text: str) -> str:
        """Add natural breathing points in long sentences"""
        # Add breathing pauses after long phrases (approximated by commas in long sentences)
        sentences = text.split('.')
        processed_sentences = []
        
        for sentence in sentences:
            if len(sentence) > 100:  # Long sentence
                # Add breathing pause after commas in long sentences
                sentence = re.sub(r',\s+', ', <pause:300ms>', sentence)
            processed_sentences.append(sentence)
        
        return '.'.join(processed_sentences)

    def _add_dramatic_pauses(self, text: str, context: RhythmContext) -> str:
        """Add dramatic pauses for important mathematical moments"""
        if context.is_theorem:
            # Dramatic pause before theorem statement
            text = re.sub(r'(theorem:?\s+)', '\\1<pause:800ms>', text, flags=re.IGNORECASE)
            
        if context.is_proof:
            # Dramatic pause before QED
            text = re.sub(r'(QED|∎|□)', '<pause:1000ms>\\1', text)
            
        # Dramatic pause before profound statements
        profound_patterns = [
            r'(this is one of the most)',
            r'(remarkably,)',
            r'(extraordinarily,)',
            r'(beautifully,)',
            r'(profoundly,)'
        ]
        
        for pattern in profound_patterns:
            text = re.sub(pattern, '<pause:600ms>\\1', text, flags=re.IGNORECASE)
        
        return text

    def _optimize_rhythm_flow(self, text: str) -> str:
        """Optimize the overall rhythm flow to avoid awkward pauses"""
        # Remove redundant consecutive pauses
        text = re.sub(r'(<pause:\d+ms>\s*)+', r'\1', text)
        
        # Ensure proper spacing around pause markers
        text = re.sub(r'\s*<pause:(\d+)ms>\s*', r' <pause:\1ms> ', text)
        
        # Remove pauses at the very beginning or end
        text = re.sub(r'^\s*<pause:\d+ms>\s*', '', text)
        text = re.sub(r'\s*<pause:\d+ms>\s*$', '', text)
        
        # Clean up emphasis tags
        text = re.sub(r'\s*<emphasis\s+level="(\w+)">\s*', r' <emphasis level="\1">', text)
        text = re.sub(r'\s*</emphasis>\s*', r'</emphasis> ', text)
        
        return text

    def get_reading_time_estimate(self, text: str) -> float:
        """
        Estimate reading time including pauses
        
        Args:
            text: The text with rhythm markup
            
        Returns:
            Estimated reading time in seconds
        """
        # Base reading speed: 150 words per minute
        words = len(re.findall(r'\b\w+\b', text))
        base_time = (words / 150) * 60  # Convert to seconds
        
        # Add pause times
        pause_time = 0
        pause_matches = re.findall(r'<pause:(\d+)ms>', text)
        for pause_ms in pause_matches:
            pause_time += int(pause_ms) / 1000  # Convert to seconds
        
        # Add extra time for emphasis (approximately 20% slower)
        emphasis_matches = re.findall(r'<emphasis.*?>(.*?)</emphasis>', text)
        for emphasized_text in emphasis_matches:
            emphasis_words = len(re.findall(r'\b\w+\b', emphasized_text))
            pause_time += (emphasis_words / 150) * 60 * 0.2
        
        return base_time + pause_time

    def create_ssml_output(self, text: str) -> str:
        """
        Convert rhythm markup to SSML for TTS engines
        
        Args:
            text: Text with rhythm markup
            
        Returns:
            SSML-formatted text
        """
        ssml = '<speak>\n'
        
        # Convert pause markup to SSML breaks
        text = re.sub(r'<pause:(\d+)ms>', r'<break time="\1ms"/>', text)
        
        # Convert emphasis markup to SSML emphasis
        text = re.sub(r'<emphasis level="mild">(.*?)</emphasis>', 
                     r'<emphasis level="weak">\1</emphasis>', text)
        text = re.sub(r'<emphasis level="dramatic">(.*?)</emphasis>', 
                     r'<emphasis level="strong">\1</emphasis>', text)
        
        # Add prosody for mathematical sections
        if '<emphasis level="strong">' in text:
            # Slow down dramatic sections slightly
            text = re.sub(r'(<emphasis level="strong">.*?</emphasis>)',
                         r'<prosody rate="90%">\1</prosody>', text)
        
        ssml += text + '\n</speak>'
        
        return ssml

    def analyze_rhythm_quality(self, text: str) -> Dict[str, any]:
        """
        Analyze the rhythm quality of processed text
        
        Returns:
            Dictionary with rhythm quality metrics
        """
        metrics = {
            'total_pauses': len(re.findall(r'<pause:\d+ms>', text)),
            'total_emphasis': len(re.findall(r'<emphasis.*?>', text)),
            'reading_time': self.get_reading_time_estimate(text),
            'pause_distribution': {},
            'emphasis_distribution': {}
        }
        
        # Analyze pause distribution
        for pause_match in re.finditer(r'<pause:(\d+)ms>', text):
            pause_length = int(pause_match.group(1))
            if pause_length <= 200:
                pause_type = 'short'
            elif pause_length <= 400:
                pause_type = 'medium'
            elif pause_length <= 600:
                pause_type = 'long'
            else:
                pause_type = 'dramatic'
            
            metrics['pause_distribution'][pause_type] = \
                metrics['pause_distribution'].get(pause_type, 0) + 1
        
        # Analyze emphasis distribution
        for emphasis_match in re.finditer(r'<emphasis level="(\w+)">', text):
            emphasis_level = emphasis_match.group(1)
            metrics['emphasis_distribution'][emphasis_level] = \
                metrics['emphasis_distribution'].get(emphasis_level, 0) + 1
        
        # Calculate rhythm score (0-100)
        rhythm_score = 0
        
        # Good rhythm has pauses
        if metrics['total_pauses'] > 0:
            rhythm_score += 30
        
        # Good rhythm has varied pauses
        if len(metrics['pause_distribution']) >= 1:
            rhythm_score += 20
        
        # Good rhythm has some emphasis
        if metrics['total_emphasis'] > 0:
            rhythm_score += 30
        
        # Good rhythm has appropriate pacing
        words = len(re.findall(r'\b\w+\b', text))
        if words > 0:
            pause_ratio = metrics['total_pauses'] / max(words / 10, 1)
            if pause_ratio > 0:
                rhythm_score += 20
        
        metrics['rhythm_score'] = rhythm_score
        
        return metrics