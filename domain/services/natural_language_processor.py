"""
Natural Language Processor for Mathematical Speech Enhancement
Provides context-aware natural language processing for mathematical expressions
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class MathematicalContext(Enum):
    """Mathematical context types for enhanced processing"""
    VARIABLE = "variable"
    PARAMETER = "parameter"
    ANGLE = "angle"
    FUNCTION = "function"
    EQUATION = "equation"
    DERIVATIVE = "derivative"
    INTEGRAL = "integral"
    LIMIT = "limit"
    EDUCATIONAL = "educational"
    STEP_BY_STEP = "step_by_step"
    DEFINITION = "definition"
    PROOF = "proof"
    DEFAULT = "default"


class AudienceLevel(Enum):
    """Audience sophistication levels"""
    ELEMENTARY = "elementary"
    HIGH_SCHOOL = "high_school"
    UNDERGRADUATE = "undergraduate"
    GRADUATE = "graduate"
    RESEARCH = "research"


@dataclass
class NaturalLanguageContext:
    """Context information for natural language processing"""
    mathematical_context: MathematicalContext
    audience_level: AudienceLevel
    explanation_mode: bool = False
    step_by_step_mode: bool = False
    professor_style: bool = True
    include_reasoning: bool = False


class NaturalLanguageProcessor:
    """
    Enhances mathematical speech with natural language patterns
    Implements Stage 2 and Stage 3 advanced NLP capabilities
    
    Stage 3 Features:
    - Semantic mathematical understanding
    - Concept-aware explanations
    - Dynamic speech flow
    - Mathematical storytelling
    - Emotional intelligence for teaching
    """
    
    def __init__(self):
        self.contextual_articles = {
            # Mathematical operations always get 'the'
            "derivative": "the",
            "integral": "the", 
            "limit": "the",
            "sum": "the",
            "product": "the",
            "function": "the",
            "equation": "the",
            "inequality": "the",
            "matrix": "the",
            "vector": "the"
        }
        
        self.professor_transitions = {
            "calculation": ["we calculate", "let us compute", "we evaluate"],
            "observation": ["we observe that", "notice that", "we see that"],
            "conclusion": ["therefore", "thus we conclude", "hence"],
            "definition": ["we define", "let us define", "consider"],
            "step": ["in the next step", "proceeding further", "continuing"]
        }
        
        self.mathematical_connectors = {
            "with_respect_to": "with respect to",
            "from_to": "from {} to {}",
            "equals": "equals",
            "approaches": "approaches",
            "is_equal_to": "is equal to",
            "raised_to": "raised to the power of"
        }
        
        # Stage 3: Semantic understanding patterns
        self.concept_explanations = {
            "derivative": {
                "geometric": "represents the slope of the tangent line at any point",
                "physical": "measures the instantaneous rate of change",
                "computational": "follows the rules of differentiation"
            },
            "integral": {
                "geometric": "calculates the area under a curve",
                "physical": "accumulates quantities over time or space",
                "computational": "reverses the process of differentiation"
            },
            "limit": {
                "intuitive": "describes what value a function approaches",
                "formal": "makes precise the notion of 'getting arbitrarily close'",
                "practical": "allows us to handle infinity and undefined expressions"
            }
        }
        
        # Stage 3: Mathematical storytelling patterns
        self.story_patterns = {
            "introduction": [
                "Let's explore what happens when",
                "Consider the mathematical situation where",
                "Imagine we have a function that"
            ],
            "development": [
                "As we progress through this calculation",
                "Building on what we've established",
                "The next natural step is to"
            ],
            "revelation": [
                "This reveals an important property",
                "We discover that",
                "Remarkably, this shows us"
            ],
            "conclusion": [
                "Therefore, we can conclude",
                "This demonstrates that",
                "In summary, our analysis shows"
            ]
        }
        
        # Stage 3: Emotional teaching patterns
        self.teaching_emotions = {
            "encouragement": [
                "Don't worry if this seems complex at first",
                "This is a powerful technique once you understand it",
                "Let's work through this step by step"
            ],
            "excitement": [
                "Here's where mathematics becomes beautiful",
                "This is one of the most elegant results in calculus",
                "Notice the remarkable pattern that emerges"
            ],
            "clarity": [
                "To make this crystal clear",
                "Let me explain this in simpler terms",
                "The key insight is that"
            ]
        }

    def enhance_mathematical_speech(self, raw_output: str, context: NaturalLanguageContext) -> str:
        """
        Apply comprehensive natural language enhancements to mathematical speech
        
        Args:
            raw_output: The basic pattern-matched output
            context: Natural language context information
            
        Returns:
            Enhanced natural language mathematical speech
        """
        enhanced = raw_output
        
        # Apply contextual articles
        enhanced = self._add_contextual_articles(enhanced, context)
        
        # Improve mathematical phrasing
        enhanced = self._enhance_mathematical_phrasing(enhanced, context)
        
        # Add professor-style transitions if enabled
        if context.professor_style:
            enhanced = self._add_professor_transitions(enhanced, context)
        
        # Apply audience-appropriate language
        enhanced = self._adapt_for_audience(enhanced, context)
        
        # Add educational explanations if in explanation mode
        if context.explanation_mode:
            enhanced = self._add_educational_explanations(enhanced, context)
        
        # Stage 3: Add semantic understanding and concept explanations
        enhanced = self._add_semantic_understanding(enhanced, context)
        
        # Stage 3: Add mathematical storytelling flow
        enhanced = self._add_storytelling_flow(enhanced, context)
        
        # Stage 3: Add emotional intelligence for teaching
        enhanced = self._add_teaching_emotions(enhanced, context)
        
        return enhanced.strip()

    def _add_contextual_articles(self, text: str, context: NaturalLanguageContext) -> str:
        """Add appropriate articles ('the', 'a', 'an') based on mathematical context"""
        
        # Mathematical operations always get 'the'
        for operation in self.contextual_articles:
            pattern = rf'\b({operation})\b'
            replacement = f'{self.contextual_articles[operation]} \\1'
            text = re.sub(pattern, replacement, text)
        
        # Functions get 'the' when being defined or explained
        if context.mathematical_context in [MathematicalContext.DEFINITION, MathematicalContext.EDUCATIONAL]:
            text = re.sub(r'\b(function|equation|formula)\b', r'the \1', text)
        
        # Variables can get articles in educational context
        if context.mathematical_context == MathematicalContext.EDUCATIONAL:
            text = re.sub(r'\b(variable|parameter|coefficient)\b', r'the \1', text)
            
        return text

    def _enhance_mathematical_phrasing(self, text: str, context: NaturalLanguageContext) -> str:
        """Enhance mathematical phrasing for natural flow"""
        
        # Replace robotic patterns with natural language
        enhancements = {
            r'\bd\s+(\w+)\s+d\s+(\w+)\b': r'the derivative of \1 with respect to \2',
            r'\bpartial\s+(\w+)\s+partial\s+(\w+)\b': r'the partial derivative of \1 with respect to \2',
            r'\b(\w+)\s+over\s+(\w+)\b': r'the fraction \1 over \2',
            r'\b(\w+)\s+squared\b': r'\1 raised to the second power',
            r'\b(\w+)\s+cubed\b': r'\1 raised to the third power'
        }
        
        for pattern, replacement in enhancements.items():
            text = re.sub(pattern, replacement, text)
        
        # Add natural mathematical connectors
        text = text.replace(' d ', ' with respect to ')
        text = text.replace(' = ', ' equals ')
        text = text.replace(' -> ', ' approaches ')
        
        return text

    def _add_professor_transitions(self, text: str, context: NaturalLanguageContext) -> str:
        """Add professor-style transitions and explanatory phrases"""
        
        # Add introductory phrases for different contexts
        if context.mathematical_context == MathematicalContext.EQUATION:
            if not text.startswith(('we have', 'consider', 'let')):
                text = f"we have {text}"
        
        elif context.mathematical_context == MathematicalContext.DERIVATIVE:
            if 'chain rule' in text.lower():
                text = f"applying the chain rule, {text}"
            elif 'product rule' in text.lower():
                text = f"using the product rule, {text}"
        
        elif context.mathematical_context == MathematicalContext.INTEGRAL:
            if context.step_by_step_mode:
                text = f"we evaluate {text}"
        
        elif context.mathematical_context == MathematicalContext.DEFINITION:
            if not text.startswith(('let', 'we define', 'consider')):
                text = f"let us define {text}"
        
        return text

    def _adapt_for_audience(self, text: str, context: NaturalLanguageContext) -> str:
        """Adapt language complexity for target audience"""
        
        if context.audience_level == AudienceLevel.ELEMENTARY:
            # Simpler language for elementary audience
            adaptations = {
                r'the derivative of': 'the rate of change of',
                r'with respect to': 'as we change',
                r'approaches': 'gets close to',
                r'integral': 'area under the curve'
            }
        
        elif context.audience_level == AudienceLevel.HIGH_SCHOOL:
            # Moderate complexity
            adaptations = {
                r'partial derivative': 'partial rate of change',
                r'integral from (.+) to (.+)': r'area from \1 to \2'
            }
        
        elif context.audience_level in [AudienceLevel.UNDERGRADUATE, AudienceLevel.GRADUATE]:
            # Standard mathematical language - no changes needed
            adaptations = {}
        
        elif context.audience_level == AudienceLevel.RESEARCH:
            # More formal, concise language
            adaptations = {
                r'we have the equation': 'the equation',
                r'we evaluate the integral': 'the integral',
                r'let us define': 'define'
            }
        
        else:
            adaptations = {}
        
        for pattern, replacement in adaptations.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text

    def _add_educational_explanations(self, text: str, context: NaturalLanguageContext) -> str:
        """Add educational explanations and reasoning"""
        
        if not context.explanation_mode:
            return text
        
        # Add explanatory context for common operations
        if 'derivative' in text:
            if 'chain rule' in text:
                text += " because we have a composition of functions"
            elif 'product rule' in text:
                text += " since we are differentiating a product of two functions"
        
        elif 'integral' in text:
            if 'definite' in text:
                text += " to find the area under the curve"
            elif 'indefinite' in text:
                text += " to find the antiderivative"
        
        elif 'limit' in text:
            text += " to determine the behavior as the variable approaches the given value"
        
        return text

    def determine_context_from_expression(self, expression: str) -> MathematicalContext:
        """
        Automatically determine mathematical context from the expression
        
        Args:
            expression: The mathematical expression to analyze
            
        Returns:
            The most appropriate mathematical context
        """
        expression_lower = expression.lower()
        
        # Derivative patterns
        if any(pattern in expression for pattern in ['\\frac{d', '\\partial', "'"]):
            return MathematicalContext.DERIVATIVE
        
        # Integral patterns
        if any(pattern in expression for pattern in ['\\int', '\\iint', '\\oint']):
            return MathematicalContext.INTEGRAL
        
        # Limit patterns
        if '\\lim' in expression:
            return MathematicalContext.LIMIT
        
        # Equation patterns
        if '=' in expression and not any(op in expression for op in ['\\int', '\\lim', '\\frac{d']):
            return MathematicalContext.EQUATION
        
        # Function patterns
        if '(' in expression and ')' in expression:
            return MathematicalContext.FUNCTION
        
        # Variable patterns (single letters or simple expressions)
        if re.match(r'^[a-zA-Z]$', expression.strip()):
            return MathematicalContext.VARIABLE
        
        return MathematicalContext.DEFAULT

    def get_natural_language_variants(self, base_text: str, context: MathematicalContext) -> List[str]:
        """
        Generate multiple natural language variants for the same mathematical expression
        
        Args:
            base_text: The base mathematical text
            context: The mathematical context
            
        Returns:
            List of natural language variants
        """
        variants = [base_text]
        
        if context == MathematicalContext.DERIVATIVE:
            variants.extend([
                base_text.replace('derivative', 'rate of change'),
                base_text.replace('the derivative of', 'how quickly'),
                f"the instantaneous rate of change of {base_text.split('of ')[1] if 'of ' in base_text else base_text}"
            ])
        
        elif context == MathematicalContext.INTEGRAL:
            variants.extend([
                base_text.replace('integral', 'area calculation'),
                base_text.replace('the integral of', 'the area under'),
                f"the accumulated value of {base_text.split('of ')[1] if 'of ' in base_text else base_text}"
            ])
        
        return variants

    def _add_semantic_understanding(self, text: str, context: NaturalLanguageContext) -> str:
        """
        Stage 3: Add semantic understanding and concept-aware explanations
        """
        # Detect mathematical concepts and add appropriate explanations
        for concept, explanations in self.concept_explanations.items():
            if concept in text.lower():
                # Choose explanation type based on context
                if context.audience_level in [AudienceLevel.ELEMENTARY, AudienceLevel.HIGH_SCHOOL]:
                    explanation_type = "intuitive"
                elif context.audience_level == AudienceLevel.UNDERGRADUATE:
                    explanation_type = "geometric" if "geometric" in explanations else "physical"
                else:
                    explanation_type = "computational"
                
                if explanation_type in explanations:
                    # Add the conceptual explanation naturally
                    concept_explanation = explanations[explanation_type]
                    if concept_explanation not in text:
                        text = f"{text}, which {concept_explanation}"
        
        return text
    
    def _add_storytelling_flow(self, text: str, context: NaturalLanguageContext) -> str:
        """
        Stage 3: Add mathematical storytelling and narrative flow
        """
        if not context.step_by_step_mode:
            return text
        
        # Add narrative elements based on mathematical context
        if context.mathematical_context == MathematicalContext.DERIVATIVE:
            if "chain rule" in text.lower():
                text = f"Let's explore what happens when we have nested functions. {text}"
            elif "product rule" in text.lower():
                text = f"When we multiply two functions together, {text}"
        
        elif context.mathematical_context == MathematicalContext.INTEGRAL:
            if "definite" in text.lower():
                text = f"To find the exact area under our curve, {text}"
            elif "indefinite" in text.lower():
                text = f"To reverse the differentiation process, {text}"
        
        elif context.mathematical_context == MathematicalContext.LIMIT:
            text = f"Let's examine the behavior of our function as we approach a critical point. {text}"
        
        return text
    
    def _add_teaching_emotions(self, text: str, context: NaturalLanguageContext) -> str:
        """
        Stage 3: Add emotional intelligence for mathematics teaching
        """
        if context.audience_level not in [AudienceLevel.ELEMENTARY, AudienceLevel.HIGH_SCHOOL, AudienceLevel.UNDERGRADUATE]:
            return text  # Skip emotional elements for advanced audiences
        
        # Add encouraging elements for complex concepts
        complex_indicators = ["chain rule", "integration by parts", "partial derivative", "taylor series"]
        if any(indicator in text.lower() for indicator in complex_indicators):
            if not any(emotion in text.lower() for emotion in ["don't worry", "step by step", "let's work"]):
                encouragement = self.teaching_emotions["encouragement"][0]
                text = f"{encouragement}. {text}"
        
        # Add excitement for beautiful mathematical results
        beautiful_concepts = ["euler", "golden ratio", "infinity", "symmetry", "elegant"]
        if any(concept in text.lower() for concept in beautiful_concepts):
            if not any(emotion in text.lower() for emotion in ["beautiful", "elegant", "remarkable"]):
                excitement = self.teaching_emotions["excitement"][1]
                text = f"{excitement}. {text}"
        
        return text
    
    def interpret_mathematical_meaning(self, expression: str, context: NaturalLanguageContext) -> Dict[str, str]:
        """
        Stage 3: Interpret the deeper mathematical meaning of expressions
        """
        interpretation = {
            "literal": expression,
            "conceptual": "",
            "application": "",
            "significance": ""
        }
        
        # Analyze the expression for mathematical concepts
        if "\\frac{d" in expression:
            interpretation["conceptual"] = "This represents a rate of change or slope"
            interpretation["application"] = "Used to find velocity, optimization points, or tangent lines"
            interpretation["significance"] = "Fundamental to understanding motion and change in mathematics"
        
        elif "\\int" in expression:
            interpretation["conceptual"] = "This represents accumulation or area calculation"
            interpretation["application"] = "Used to find areas, volumes, or total accumulated quantities"
            interpretation["significance"] = "Connects discrete counting with continuous measurement"
        
        elif "\\lim" in expression:
            interpretation["conceptual"] = "This examines behavior at boundary conditions"
            interpretation["application"] = "Used to handle infinity, discontinuities, and precise definitions"
            interpretation["significance"] = "Makes rigorous the intuitive notion of 'approaching' a value"
        
        return interpretation
    
    def generate_conceptual_bridge(self, from_concept: str, to_concept: str) -> str:
        """
        Stage 3: Generate natural transitions between mathematical concepts
        """
        bridges = {
            ("derivative", "integral"): "Just as the derivative measures rate of change, the integral accumulates those changes over time",
            ("limit", "derivative"): "The derivative is actually defined as a special type of limit - the limit of difference quotients",
            ("function", "derivative"): "When we have a function, we can ask how quickly it changes - that's where derivatives come in",
            ("integral", "area"): "The integral gives us a precise way to calculate areas, even for curved boundaries",
            ("equation", "solution"): "An equation poses a question, and finding its solution answers that mathematical question"
        }
        
        key = (from_concept.lower(), to_concept.lower())
        return bridges.get(key, f"There's a natural connection between {from_concept} and {to_concept}")

    def add_mathematical_rhythm(self, text: str) -> str:
        """Add natural pauses and emphasis for mathematical clarity"""
        
        # Add pauses before major operations
        text = re.sub(r'\b(equals|plus|minus|times|divided by)\b', r', \1', text)
        
        # Add pauses in complex fractions
        text = re.sub(r'\bover\b', r', over,', text)
        
        # Add emphasis on important terms
        text = re.sub(r'\b(therefore|thus|hence)\b', r'<emphasis>\1</emphasis>', text)
        
        # Add pauses before explanatory clauses
        text = re.sub(r'\b(because|since|where)\b', r', \1', text)
        
        return text