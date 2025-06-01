#!/usr/bin/env python3
"""
Test script to evaluate natural speech quality of MathTTSVer3
Focuses on professor-like explanations of mathematical expressions
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.application.use_cases.process_expression import ProcessExpressionUseCase
from src.application.dtos import ProcessExpressionRequest
from src.adapters.tts.edge_tts_adapter import EdgeTTSAdapter
from src.infrastructure.pattern_loader import YAMLPatternLoader
from src.infrastructure.cache import LRUCache
from src.domain.services.pattern_matching import PatternMatchingService
from src.domain.entities.pattern import PatternCollection


class NaturalSpeechTester:
    """Tests mathematical expressions for natural, professor-like speech"""
    
    def __init__(self):
        self.test_cases = self._create_test_cases()
        self.results = []
        
    def _create_test_cases(self) -> List[Tuple[str, str, str]]:
        """Create test cases covering various mathematical domains
        Returns: List of (expression, expected_key_phrases, description)
        """
        return [
            # Basic algebra
            ("x^2 + 2x + 1", "squared plus", "Quadratic expression"),
            ("\\frac{a+b}{c-d}", "fraction", "Simple fraction"),
            ("\\sqrt{x^2 + y^2}", "square root", "Pythagorean form"),
            
            # Calculus
            ("\\lim_{x \\to 0} \\frac{\\sin x}{x}", "limit as x approaches", "Famous limit"),
            ("\\frac{d}{dx} e^{x^2}", "derivative with respect to x", "Chain rule example"),
            ("\\int_0^\\pi \\sin x \\, dx", "integral from 0 to pi", "Definite integral"),
            
            # Linear algebra
            ("\\begin{pmatrix} a & b \\\\ c & d \\end{pmatrix}", "matrix", "2x2 matrix"),
            ("\\det(A) = ad - bc", "determinant", "Determinant formula"),
            ("\\vec{v} \\cdot \\vec{w}", "dot product", "Vector dot product"),
            
            # Advanced calculus
            ("\\nabla f = \\frac{\\partial f}{\\partial x}\\vec{i} + \\frac{\\partial f}{\\partial y}\\vec{j}", 
             "gradient", "Gradient in 2D"),
            
            # Statistics
            ("P(A|B) = \\frac{P(B|A)P(A)}{P(B)}", "probability", "Bayes' theorem"),
            ("\\sigma = \\sqrt{\\frac{1}{N}\\sum_{i=1}^N (x_i - \\mu)^2}", 
             "standard deviation", "Population std dev"),
            
            # Complex expressions
            ("e^{i\\pi} + 1 = 0", "Euler", "Euler's identity"),
            ("\\sum_{n=1}^\\infty \\frac{1}{n^2} = \\frac{\\pi^2}{6}", 
             "sum from n equals 1 to infinity", "Basel problem"),
            
            # Quantum mechanics notation
            ("|\\psi\\rangle = \\alpha|0\\rangle + \\beta|1\\rangle", 
             "quantum state", "Qubit superposition"),
        ]
    
    async def test_expression(self, expression: str, key_phrases: str, 
                            description: str) -> dict:
        """Test a single expression and evaluate its speech output"""
        print(f"\nTesting: {description}")
        print(f"LaTeX: {expression}")
        
        try:
            # Set up components
            pattern_loader = YAMLPatternLoader("patterns")
            patterns = pattern_loader.load_all_patterns()
            pattern_collection = PatternCollection(patterns)
            
            pattern_service = PatternMatchingService(pattern_collection)
            tts_adapter = EdgeTTSAdapter()
            cache = LRUCache()
            
            use_case = ProcessExpressionUseCase(
                pattern_matching_service=pattern_service,
                tts_adapter=tts_adapter,
                cache=cache
            )
            
            # Process expression
            request = ProcessExpressionRequest(
                latex=expression,
                voice_id="en-US-AriaNeural",
                speed=0.9  # Slightly slower for clarity
            )
            
            result = await use_case.execute(request)
            
            # Analyze result
            speech_text = result.speech_text
            print(f"Speech: {speech_text}")
            
            # Check for natural phrasing
            analysis = {
                "expression": expression,
                "description": description,
                "speech_text": speech_text,
                "contains_key_phrases": key_phrases.lower() in speech_text.lower(),
                "word_count": len(speech_text.split()),
                "has_pauses": "," in speech_text or ";" in speech_text,
                "audio_generated": result.audio_data is not None
            }
            
            # Natural speech indicators
            natural_indicators = {
                "uses_words_not_symbols": not any(sym in speech_text for sym in ["^", "_", "\\", "{"]),
                "has_natural_flow": len(speech_text.split()) > len(expression) // 3,
                "explains_operations": any(word in speech_text.lower() for word in 
                    ["plus", "minus", "times", "divided", "equals", "over", "squared", "cubed"]),
                "clear_structure": analysis["has_pauses"] or " of " in speech_text or " the " in speech_text
            }
            
            analysis["natural_score"] = sum(natural_indicators.values()) / len(natural_indicators)
            analysis["natural_indicators"] = natural_indicators
            
            print(f"Natural Score: {analysis['natural_score']:.2%}")
            
            return analysis
            
        except Exception as e:
            print(f"Error testing expression: {e}")
            return {
                "expression": expression,
                "description": description,
                "error": str(e),
                "natural_score": 0
            }
    
    async def run_all_tests(self):
        """Run all test cases and generate report"""
        print("="*60)
        print("MathTTSVer3 Natural Speech Quality Test")
        print("="*60)
        
        for expression, key_phrases, description in self.test_cases:
            result = await self.test_expression(expression, key_phrases, description)
            self.results.append(result)
            await asyncio.sleep(0.5)  # Small delay between tests
        
        self._generate_report()
    
    def _generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        
        successful_tests = [r for r in self.results if "error" not in r]
        failed_tests = [r for r in self.results if "error" in r]
        
        print(f"\nTotal Tests: {len(self.results)}")
        print(f"Successful: {len(successful_tests)}")
        print(f"Failed: {len(failed_tests)}")
        
        if successful_tests:
            avg_natural_score = sum(r["natural_score"] for r in successful_tests) / len(successful_tests)
            print(f"\nAverage Natural Speech Score: {avg_natural_score:.2%}")
            
            print("\nTop Natural Sounding Expressions:")
            sorted_results = sorted(successful_tests, key=lambda x: x["natural_score"], reverse=True)
            for result in sorted_results[:5]:
                print(f"- {result['description']}: {result['natural_score']:.2%}")
                print(f"  Speech: {result['speech_text'][:80]}...")
            
            print("\nExpressions Needing Improvement:")
            for result in sorted_results[-3:]:
                if result["natural_score"] < 0.6:
                    print(f"- {result['description']}: {result['natural_score']:.2%}")
                    print(f"  Issue: Missing natural indicators")
        
        if failed_tests:
            print("\nFailed Tests:")
            for result in failed_tests:
                print(f"- {result['description']}: {result['error']}")
        
        print("\n" + "="*60)
        print("RECOMMENDATIONS FOR NATURAL SPEECH")
        print("="*60)
        print("1. Add more contextual phrases ('the', 'of', 'with respect to')")
        print("2. Include natural pauses with commas for complex expressions")
        print("3. Use descriptive words instead of symbols")
        print("4. Group related terms naturally")
        print("5. Add emphasis on important operations")


async def main():
    """Main test execution"""
    tester = NaturalSpeechTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())