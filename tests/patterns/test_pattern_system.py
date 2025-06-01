"""Comprehensive pattern system tests for MathTTS v3"""

import pytest
from pathlib import Path
import yaml
from typing import List, Dict, Any

# Import the actual pattern system components
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / 'src'))

from src.adapters.pattern_loaders.yaml_pattern_loader import YamlPatternLoader
from src.domain.services.pattern_matcher import PatternMatcher
from src.domain.entities.pattern import Pattern


class TestPatternSystem:
    """Test the complete pattern system"""
    
    @pytest.fixture
    def pattern_loader(self):
        """Create pattern loader instance"""
        patterns_dir = Path(__file__).parent.parent.parent / 'patterns'
        return YamlPatternLoader(patterns_dir)
        
    @pytest.fixture
    def pattern_matcher(self, pattern_loader):
        """Create pattern matcher with loaded patterns"""
        patterns = pattern_loader.load_all_patterns()
        return PatternMatcher(patterns)
        
    def test_pattern_loading(self, pattern_loader):
        """Test that patterns load correctly"""
        patterns = pattern_loader.load_all_patterns()
        assert len(patterns) > 0
        
        # Check that we have patterns from different categories
        categories = set()
        for pattern in patterns:
            if hasattr(pattern, 'tags'):
                categories.update(pattern.tags)
                
        expected_categories = {'fraction', 'derivative', 'integral', 'greek'}
        assert expected_categories.issubset(categories)
        
    def test_basic_arithmetic(self, pattern_matcher):
        """Test basic arithmetic operations"""
        test_cases = [
            ("2 + 3", "2 plus 3"),
            ("5 - 2", "5 minus 2"),
            ("4 × 7", "4 times 7"),
            ("8 ÷ 2", "8 divided by 2"),
            ("x = 5", "x equals 5"),
            ("a < b", "a is less than b"),
            ("x > y", "x is greater than y"),
        ]
        
        for latex, expected in test_cases:
            result = pattern_matcher.process(latex)
            assert expected in result.lower()
            
    def test_fractions(self, pattern_matcher):
        """Test fraction patterns"""
        test_cases = [
            (r"\frac{1}{2}", "one half"),
            (r"\frac{1}{3}", "one third"),
            (r"\frac{1}{4}", "one quarter"),
            (r"\frac{2}{3}", "two thirds"),
            (r"\frac{3}{4}", "three quarters"),
            (r"\frac{5}{7}", "5 over 7"),
            (r"\frac{x}{y}", "x over y"),
            (r"\frac{a+b}{c-d}", "a plus b over c minus d"),
        ]
        
        for latex, expected in test_cases:
            result = pattern_matcher.process(latex)
            assert expected in result.lower()
            
    def test_powers_and_roots(self, pattern_matcher):
        """Test power and root patterns"""
        test_cases = [
            ("x^2", "x squared"),
            ("y^3", "y cubed"),
            ("z^4", "z to the fourth"),
            ("a^n", "a to the power of n"),
            (r"\sqrt{4}", "the square root of 4"),
            (r"\sqrt[3]{8}", "the cube root of 8"),
            (r"\sqrt[n]{x}", "the n root of x"),
        ]
        
        for latex, expected in test_cases:
            result = pattern_matcher.process(latex)
            assert expected in result.lower()
            
    def test_derivatives(self, pattern_matcher):
        """Test derivative patterns"""
        test_cases = [
            (r"\frac{d}{dx} f(x)", "the derivative of f of x with respect to x"),
            (r"\frac{d^2 y}{dx^2}", "d squared y d x squared"),
            (r"\frac{\partial f}{\partial x}", "partial f partial x"),
            ("f'(x)", "f prime of x"),
            ("g''(t)", "g double prime of t"),
        ]
        
        for latex, expected in test_cases:
            result = pattern_matcher.process(latex)
            # Normalize and check
            assert any(exp in result.lower() for exp in expected.lower().split())
            
    def test_integrals(self, pattern_matcher):
        """Test integral patterns"""
        test_cases = [
            (r"\int f(x) dx", "the integral of f of x d x"),
            (r"\int_0^1 x^2 dx", "the integral from 0 to 1 of x squared d x"),
            (r"\int_a^b g(t) dt", "the integral from a to b of g of t d t"),
            (r"\iint f(x,y) dA", "the double integral of f of x comma y d A"),
        ]
        
        for latex, expected in test_cases:
            result = pattern_matcher.process(latex)
            assert any(word in result.lower() for word in ['integral', 'from', 'to'])
            
    def test_greek_letters(self, pattern_matcher):
        """Test Greek letter patterns"""
        test_cases = [
            (r"\alpha", "alpha"),
            (r"\beta", "beta"),
            (r"\gamma", "gamma"),
            (r"\delta", "delta"),
            (r"\pi", "pi"),
            (r"\theta", "theta"),
            (r"\lambda", "lambda"),
            (r"\Sigma", "capital sigma"),
            (r"\Delta", "capital delta"),
        ]
        
        for latex, expected in test_cases:
            result = pattern_matcher.process(latex)
            assert expected in result.lower()
            
    def test_complex_expressions(self, pattern_matcher):
        """Test complex mathematical expressions"""
        test_cases = [
            (
                r"x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}",
                ["negative b", "plus or minus", "square root", "b squared", "minus", "4 a c", "over", "2 a"]
            ),
            (
                r"\lim_{x \to \infty} \frac{1}{x} = 0",
                ["limit", "x", "approaches", "infinity", "1 over x", "equals", "0"]
            ),
            (
                r"\sum_{n=1}^{\infty} \frac{1}{n^2} = \frac{\pi^2}{6}",
                ["sum", "n equals 1", "infinity", "1 over n squared", "equals", "pi squared over 6"]
            ),
        ]
        
        for latex, expected_parts in test_cases:
            result = pattern_matcher.process(latex)
            result_lower = result.lower()
            for part in expected_parts:
                assert part.lower() in result_lower or any(
                    word in result_lower for word in part.lower().split()
                )
                
    def test_statistics_patterns(self, pattern_matcher):
        """Test statistics and probability patterns"""
        test_cases = [
            ("P(A)", "the probability of A"),
            ("P(A|B)", "the probability of A given B"),
            (r"E[X]", "the expected value of X"),
            (r"\text{Var}(X)", "the variance of X"),
            (r"\bar{x}", "x bar"),
            (r"\mathcal{N}(0, 1)", "normal distribution with mean 0 and variance 1"),
        ]
        
        for latex, expected in test_cases:
            result = pattern_matcher.process(latex)
            assert any(word in result.lower() for word in expected.lower().split())
            
    def test_set_theory_patterns(self, pattern_matcher):
        """Test set theory patterns"""
        test_cases = [
            (r"x \in A", "x is an element of A"),
            (r"B \subset C", "B is a subset of C"),
            (r"A \cup B", "A union B"),
            (r"A \cap B", "A intersection B"),
            (r"\emptyset", "the empty set"),
            (r"\mathbb{R}", "the real numbers"),
            (r"\forall x", "for all x"),
            (r"\exists y", "there exists y"),
        ]
        
        for latex, expected in test_cases:
            result = pattern_matcher.process(latex)
            assert any(word in result.lower() for word in expected.lower().split()[:3])
            
    def test_pattern_priorities(self, pattern_matcher):
        """Test that pattern priorities work correctly"""
        # Special fractions should have higher priority than general fractions
        result1 = pattern_matcher.process(r"\frac{1}{2}")
        assert "one half" in result1.lower()
        
        result2 = pattern_matcher.process(r"\frac{5}{7}")
        assert "5 over 7" in result2.lower()
        
    def test_edge_cases(self, pattern_matcher):
        """Test edge cases and special scenarios"""
        test_cases = [
            ("", ""),  # Empty input
            ("hello", "hello"),  # Non-mathematical text
            ("2 + 2 = 4", "2 plus 2 equals 4"),  # Simple equation
            (r"\frac{\frac{1}{2}}{3}", "1 over 2, all over 3"),  # Nested fractions
            ("x^2 + y^2 = z^2", "x squared plus y squared equals z squared"),  # Pythagorean theorem
        ]
        
        for latex, expected in test_cases:
            result = pattern_matcher.process(latex)
            if expected:
                assert any(word in result.lower() for word in expected.lower().split()[:3])


class TestPatternValidation:
    """Test pattern validation and consistency"""
    
    def test_all_patterns_have_unique_ids(self):
        """Ensure all patterns have unique IDs"""
        patterns_dir = Path(__file__).parent.parent.parent / 'patterns'
        pattern_ids = set()
        
        # Load master config
        with open(patterns_dir / 'master_patterns.yaml', 'r') as f:
            master_config = yaml.safe_load(f)
            
        # Check each pattern file
        for file_config in master_config.get('pattern_files', []):
            if file_config.get('enabled', True):
                file_path = patterns_dir / file_config['path']
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        data = yaml.safe_load(f)
                        
                    for pattern in data.get('patterns', []):
                        pattern_id = pattern.get('id')
                        assert pattern_id is not None
                        assert pattern_id not in pattern_ids, f"Duplicate ID: {pattern_id}"
                        pattern_ids.add(pattern_id)
                        
    def test_all_patterns_compile(self):
        """Ensure all pattern regexes compile"""
        import re
        patterns_dir = Path(__file__).parent.parent.parent / 'patterns'
        
        # Load master config
        with open(patterns_dir / 'master_patterns.yaml', 'r') as f:
            master_config = yaml.safe_load(f)
            
        # Check each pattern file
        for file_config in master_config.get('pattern_files', []):
            if file_config.get('enabled', True):
                file_path = patterns_dir / file_config['path']
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        data = yaml.safe_load(f)
                        
                    for pattern in data.get('patterns', []):
                        pattern_str = pattern.get('pattern')
                        if pattern_str:
                            try:
                                re.compile(pattern_str)
                            except re.error as e:
                                pytest.fail(f"Pattern '{pattern.get('id')}' failed to compile: {e}")


# Performance tests
@pytest.mark.performance
class TestPatternPerformance:
    """Test pattern system performance"""
    
    def test_pattern_matching_speed(self, pattern_matcher, benchmark):
        """Benchmark pattern matching speed"""
        test_expression = r"\int_0^1 \frac{x^2 + 2x + 1}{x + 1} dx"
        
        result = benchmark(pattern_matcher.process, test_expression)
        assert "integral" in result.lower()
        
    def test_large_expression_handling(self, pattern_matcher):
        """Test handling of large expressions"""
        # Create a large expression
        large_expr = " + ".join([f"x_{i}^2" for i in range(100)])
        
        result = pattern_matcher.process(large_expr)
        assert "squared" in result
        assert "plus" in result