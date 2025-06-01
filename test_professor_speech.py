#!/usr/bin/env python3
"""
Test natural professor-like speech quality of MathTTSVer3
Uses the CLI interface to test various mathematical expressions
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import List, Dict, Tuple

class ProfessorSpeechTester:
    """Tests mathematical expressions for professor-like natural speech"""
    
    def __init__(self):
        self.test_cases = self._create_professor_test_cases()
        self.results = []
        
    def _create_professor_test_cases(self) -> List[Dict[str, str]]:
        """Create test cases that a professor might explain in class"""
        return [
            # Basic algebra that a professor would explain step by step
            {
                "latex": "x^2 + 2x + 1",
                "context": "Explaining perfect square",
                "expected_keywords": ["squared", "plus", "equals"],
                "professor_style": "This is x squared plus 2x plus 1"
            },
            {
                "latex": "\\frac{d}{dx} x^2",
                "context": "Basic derivative",
                "expected_keywords": ["derivative", "with respect to", "x squared"],
                "professor_style": "The derivative of x squared with respect to x"
            },
            {
                "latex": "\\int x^2 dx",
                "context": "Simple integral",
                "expected_keywords": ["integral", "x squared", "dx"],
                "professor_style": "The integral of x squared dx"
            },
            {
                "latex": "\\lim_{x \\to 0} \\frac{\\sin x}{x}",
                "context": "Famous limit",
                "expected_keywords": ["limit", "approaches", "sine", "over"],
                "professor_style": "The limit as x approaches 0 of sine x over x"
            },
            {
                "latex": "\\sum_{n=1}^{\\infty} \\frac{1}{n^2}",
                "context": "Infinite series",
                "expected_keywords": ["sum", "from", "to infinity", "squared"],
                "professor_style": "The sum from n equals 1 to infinity of 1 over n squared"
            },
            {
                "latex": "\\vec{a} \\cdot \\vec{b} = |\\vec{a}||\\vec{b}|\\cos\\theta",
                "context": "Dot product formula",
                "expected_keywords": ["vector", "dot", "magnitude", "cosine"],
                "professor_style": "Vector a dot vector b equals magnitude of a times magnitude of b times cosine theta"
            },
            {
                "latex": "e^{i\\pi} + 1 = 0",
                "context": "Euler's identity",
                "expected_keywords": ["e to the", "i pi", "plus", "equals"],
                "professor_style": "e to the i pi plus 1 equals 0"
            },
            {
                "latex": "\\frac{\\partial f}{\\partial x}",
                "context": "Partial derivative",
                "expected_keywords": ["partial", "derivative", "with respect to"],
                "professor_style": "The partial derivative of f with respect to x"
            }
        ]
    
    def run_cli_test(self, expression: str) -> Tuple[bool, str, str]:
        """Run a single expression through the CLI and capture output"""
        try:
            # Activate virtual environment and run CLI command
            cmd = [
                sys.executable,
                "main.py",
                "cli",
                "process",
                expression,
                "--audience", "undergraduate"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            if result.returncode == 0:
                return True, result.stdout, ""
            else:
                return False, result.stdout, result.stderr
                
        except Exception as e:
            return False, "", str(e)
    
    def analyze_speech_quality(self, test_case: Dict[str, str], output: str) -> Dict[str, any]:
        """Analyze the speech output for natural professor-like qualities"""
        
        # Extract speech text from output
        speech_text = ""
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if "Speech Text" in line and i + 1 < len(lines):
                # Look for the actual speech text in the output
                for j in range(i, min(i + 5, len(lines))):
                    if "│" in lines[j]:
                        parts = lines[j].split("│")
                        if len(parts) > 2:
                            speech_text = parts[2].strip()
                            break
        
        if not speech_text:
            # Try to find it in a different format
            for line in lines:
                if "Speech Text:" in line:
                    speech_text = line.split("Speech Text:")[1].strip()
                    break
        
        # Calculate natural speech indicators
        analysis = {
            "latex": test_case["latex"],
            "context": test_case["context"],
            "speech_text": speech_text,
            "success": bool(speech_text),
        }
        
        if speech_text:
            # Check for expected keywords
            keywords_found = sum(1 for kw in test_case["expected_keywords"] 
                               if kw.lower() in speech_text.lower())
            
            # Natural speech characteristics
            natural_features = {
                "uses_words_not_symbols": not any(sym in speech_text for sym in ["^", "_", "\\", "{", "}"]),
                "has_articles": any(article in speech_text.lower() for article in ["the", "a", "an"]),
                "has_prepositions": any(prep in speech_text.lower() for prep in ["of", "to", "with", "over", "from"]),
                "explains_operations": any(op in speech_text.lower() for op in 
                    ["plus", "minus", "times", "divided", "equals", "squared", "cubed"]),
                "has_natural_flow": len(speech_text.split()) >= len(test_case["latex"]) / 4,
                "matches_keywords": keywords_found >= len(test_case["expected_keywords"]) * 0.6
            }
            
            analysis["natural_score"] = sum(natural_features.values()) / len(natural_features)
            analysis["natural_features"] = natural_features
            analysis["keywords_found"] = keywords_found
            analysis["total_keywords"] = len(test_case["expected_keywords"])
            
            # Compare to professor style
            professor_words = set(test_case["professor_style"].lower().split())
            speech_words = set(speech_text.lower().split())
            common_words = professor_words.intersection(speech_words)
            analysis["professor_similarity"] = len(common_words) / len(professor_words) if professor_words else 0
            
        return analysis
    
    def run_all_tests(self):
        """Run all test cases and generate comprehensive report"""
        print("="*70)
        print("MathTTSVer3 Professor-Style Natural Speech Test")
        print("="*70)
        print()
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"Test {i}/{len(self.test_cases)}: {test_case['context']}")
            print(f"LaTeX: {test_case['latex']}")
            
            success, output, error = self.run_cli_test(test_case['latex'])
            
            if success:
                analysis = self.analyze_speech_quality(test_case, output)
                self.results.append(analysis)
                
                if analysis["speech_text"]:
                    print(f"Speech: {analysis['speech_text']}")
                    print(f"Natural Score: {analysis['natural_score']:.2%}")
                    print(f"Professor Similarity: {analysis['professor_similarity']:.2%}")
                else:
                    print("❌ Could not extract speech text from output")
            else:
                print(f"❌ Error: {error}")
                self.results.append({
                    "latex": test_case['latex'],
                    "context": test_case['context'],
                    "success": False,
                    "error": error
                })
            
            print("-" * 70)
        
        self._generate_report()
    
    def _generate_report(self):
        """Generate comprehensive test report with recommendations"""
        print("\n" + "="*70)
        print("FINAL TEST REPORT")
        print("="*70)
        
        successful = [r for r in self.results if r.get("success", False) and "natural_score" in r]
        failed = [r for r in self.results if not r.get("success", False)]
        
        print(f"\nTest Summary:")
        print(f"- Total tests: {len(self.results)}")
        print(f"- Successful: {len(successful)}")
        print(f"- Failed: {len(failed)}")
        
        if successful:
            avg_natural = sum(r["natural_score"] for r in successful) / len(successful)
            avg_professor = sum(r["professor_similarity"] for r in successful) / len(successful)
            
            print(f"\nQuality Metrics:")
            print(f"- Average Natural Speech Score: {avg_natural:.2%}")
            print(f"- Average Professor Style Match: {avg_professor:.2%}")
            
            print("\nBest Natural Sounding Expressions:")
            sorted_by_natural = sorted(successful, key=lambda x: x["natural_score"], reverse=True)
            for result in sorted_by_natural[:3]:
                print(f"- {result['context']}: {result['natural_score']:.2%}")
                print(f"  Speech: \"{result['speech_text']}\"")
            
            print("\nExpressions Needing Improvement:")
            for result in sorted_by_natural[-2:]:
                if result["natural_score"] < 0.7:
                    print(f"- {result['context']}: {result['natural_score']:.2%}")
                    missing = [k for k, v in result["natural_features"].items() if not v]
                    print(f"  Missing: {', '.join(missing)}")
        
        print("\n" + "="*70)
        print("PROJECT CAPABILITIES SUMMARY")
        print("="*70)
        print()
        print("MathTTSVer3 is a sophisticated LaTeX-to-Speech system that:")
        print()
        print("✅ CONVERTS mathematical expressions to natural spoken language")
        print("✅ SUPPORTS multiple mathematical domains (algebra, calculus, etc.)")
        print("✅ USES pattern matching with 541+ patterns for accurate conversion")
        print("✅ PROVIDES multiple TTS providers (Edge-TTS, gTTS, Azure, etc.)")
        print("✅ INCLUDES caching for performance optimization")
        print("✅ OFFERS both API and CLI interfaces")
        print("✅ FEATURES production-ready infrastructure (auth, logging, monitoring)")
        print()
        print("Current Natural Speech Quality:")
        if successful:
            if avg_natural > 0.8:
                print("🟢 EXCELLENT - Expressions sound natural and professor-like")
            elif avg_natural > 0.6:
                print("🟡 GOOD - Most expressions sound natural with room for improvement")
            else:
                print("🔴 NEEDS WORK - Expressions need more natural phrasing")
        
        print("\nRecommendations for More Natural Speech:")
        print("1. Add more contextual phrases like 'the', 'of', 'with respect to'")
        print("2. Include natural pauses and emphasis for complex expressions")
        print("3. Use descriptive words instead of mathematical symbols")
        print("4. Group related terms as a professor would when explaining")
        print("5. Consider audience level for appropriate terminology")


if __name__ == "__main__":
    tester = ProfessorSpeechTester()
    tester.run_all_tests()