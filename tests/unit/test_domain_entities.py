"""
Unit tests for domain entities.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import unittest
from datetime import datetime

from src.domain.entities import PatternEntity, MathematicalExpression
from src.domain.entities.pattern import PatternContext, PatternType
from src.domain.value_objects import (
    LaTeXExpression,
    PatternPriority,
    MathematicalDomain,
    AudienceLevel
)
from src.domain.exceptions import ValidationError, PatternError


class TestPatternEntity(unittest.TestCase):
    """Test cases for PatternEntity."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.valid_pattern_data = {
            "id": "test_pattern",
            "name": "Test Pattern",
            "pattern": r"\\test",
            "output_template": "test",
            "priority": PatternPriority.medium(),
            "domain": MathematicalDomain("general"),
            "contexts": [PatternContext.ANY]
        }
    
    def test_pattern_creation_success(self):
        """Test successful pattern creation."""
        pattern = PatternEntity(**self.valid_pattern_data)
        
        self.assertEqual(pattern.id, "test_pattern")
        self.assertEqual(pattern.name, "Test Pattern")
        self.assertEqual(pattern.pattern, r"\\test")
        self.assertEqual(pattern.output_template, "test")
        self.assertEqual(pattern.priority.value, 500)
        self.assertEqual(pattern.domain.value, "general")
        self.assertEqual(pattern.contexts, [PatternContext.ANY])
    
    def test_pattern_validation_empty_pattern(self):
        """Test pattern validation with empty pattern."""
        invalid_data = self.valid_pattern_data.copy()
        invalid_data["pattern"] = ""
        
        with self.assertRaises(ValidationError) as ctx:
            PatternEntity(**invalid_data)
        
        self.assertIn("Pattern cannot be empty", str(ctx.exception))
    
    def test_pattern_validation_empty_output(self):
        """Test pattern validation with empty output template."""
        invalid_data = self.valid_pattern_data.copy()
        invalid_data["output_template"] = ""
        
        with self.assertRaises(ValidationError) as ctx:
            PatternEntity(**invalid_data)
        
        self.assertIn("Output template cannot be empty", str(ctx.exception))
    
    def test_pattern_regex_compilation(self):
        """Test regex pattern compilation."""
        pattern = PatternEntity(**self.valid_pattern_data)
        
        self.assertIsNotNone(pattern._compiled_pattern)
        self.assertTrue(pattern.matches(r"\test"))
        self.assertFalse(pattern.matches("test"))
    
    def test_pattern_apply_success(self):
        """Test successful pattern application."""
        pattern_data = self.valid_pattern_data.copy()
        pattern_data["pattern"] = r"\\frac\{(\d+)\}\{(\d+)\}"
        pattern_data["output_template"] = r"\1 over \2"
        
        pattern = PatternEntity(**pattern_data)
        result, applied = pattern.apply(r"\frac{1}{2}")
        
        self.assertTrue(applied)
        self.assertEqual(result, "1 over 2")
        self.assertEqual(pattern._match_count, 1)
    
    def test_pattern_apply_no_match(self):
        """Test pattern application with no match."""
        pattern = PatternEntity(**self.valid_pattern_data)
        result, applied = pattern.apply("no match here")
        
        self.assertFalse(applied)
        self.assertEqual(result, "no match here")
        self.assertEqual(pattern._match_count, 0)
    
    def test_pattern_literal_type(self):
        """Test literal pattern type."""
        pattern_data = self.valid_pattern_data.copy()
        pattern_data["pattern_type"] = PatternType.LITERAL
        pattern_data["pattern"] = "pi"
        pattern_data["output_template"] = "π"
        
        pattern = PatternEntity(**pattern_data)
        result, applied = pattern.apply("The value of pi is important")
        
        self.assertTrue(applied)
        self.assertEqual(result, "The value of π is important")
    
    def test_pattern_priority_comparison(self):
        """Test pattern priority comparison."""
        high_priority = PatternEntity(
            **{**self.valid_pattern_data, "priority": PatternPriority.high()}
        )
        low_priority = PatternEntity(
            **{**self.valid_pattern_data, "priority": PatternPriority.low()}
        )
        
        patterns = [low_priority, high_priority]
        sorted_patterns = sorted(patterns, key=lambda p: p.priority.value, reverse=True)
        
        self.assertEqual(sorted_patterns[0], high_priority)
        self.assertEqual(sorted_patterns[1], low_priority)


class TestMathematicalExpression(unittest.TestCase):
    """Test cases for MathematicalExpression entity."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.simple_expr = LaTeXExpression(r"\frac{1}{2}")
        self.complex_expr = LaTeXExpression(r"\int_{0}^{\infty} e^{-x^2} dx")
    
    def test_expression_creation(self):
        """Test mathematical expression creation."""
        expr = MathematicalExpression(
            latex_expression=self.simple_expr,
            audience_level=AudienceLevel("undergraduate")
        )
        
        self.assertEqual(expr.latex_expression, self.simple_expr)
        self.assertEqual(expr.audience_level.value, "undergraduate")
        self.assertIsNotNone(expr.id)
        self.assertIsNotNone(expr.created_at)
        self.assertIsNotNone(expr.metadata)
    
    def test_expression_type_detection(self):
        """Test expression type detection."""
        # Fraction
        frac_expr = MathematicalExpression(
            latex_expression=LaTeXExpression(r"\frac{a}{b}")
        )
        self.assertEqual(frac_expr.expression_type.value, "algebraic")
        
        # Integral
        int_expr = MathematicalExpression(
            latex_expression=LaTeXExpression(r"\int f(x) dx")
        )
        self.assertEqual(int_expr.expression_type.value, "calculus")
        
        # Matrix
        matrix_expr = MathematicalExpression(
            latex_expression=LaTeXExpression(r"\begin{matrix} a & b \\ c & d \end{matrix}")
        )
        self.assertEqual(matrix_expr.expression_type.value, "matrix")
    
    def test_complexity_calculation(self):
        """Test complexity score calculation."""
        simple = MathematicalExpression(
            latex_expression=LaTeXExpression("x + 1")
        )
        complex_expr = MathematicalExpression(
            latex_expression=self.complex_expr
        )
        
        self.assertIsNotNone(simple.complexity_metrics)
        self.assertIsNotNone(complex_expr.complexity_metrics)
        self.assertLess(simple.complexity_metrics.overall_score, 
                       complex_expr.complexity_metrics.overall_score)
    
    def test_domain_detection(self):
        """Test mathematical domain detection."""
        # Calculus expression
        calc_expr = MathematicalExpression(
            latex_expression=LaTeXExpression(r"\lim_{x \to 0} \frac{\sin x}{x}")
        )
        self.assertEqual(calc_expr.detected_domain.value, "calculus")
        
        # Linear algebra expression
        linalg_expr = MathematicalExpression(
            latex_expression=LaTeXExpression(r"\det(A) = 0")
        )
        self.assertEqual(linalg_expr.detected_domain.value, "linear_algebra")
        
        # Statistics expression
        stats_expr = MathematicalExpression(
            latex_expression=LaTeXExpression(r"P(X > \mu + 2\sigma)")
        )
        self.assertEqual(stats_expr.detected_domain.value, "statistics")
    
    def test_processing_metadata(self):
        """Test processing metadata management."""
        expr = MathematicalExpression(latex_expression=self.simple_expr)
        
        # Add transformation
        expr.add_transformation("Applied pattern X")
        self.assertIn("Applied pattern X", expr.metadata.transformations)
        
        # Add warning
        expr.add_warning("Potential ambiguity detected")
        self.assertIn("Potential ambiguity detected", expr.metadata.warnings)
        
        # Set processing result
        from src.domain.value_objects import SpeechText
        speech = SpeechText(value="one half")
        expr.set_processing_result(
            speech_text=speech,
            patterns_applied=["frac_pattern"],
            processing_time_ms=10.5,
            cache_hit=False
        )
        
        self.assertEqual(expr.speech_text, speech)
        self.assertEqual(expr.metadata.processing_time_ms, 10.5)
        self.assertFalse(expr.metadata.cache_hit)
    
    def test_audience_suitability(self):
        """Test audience level suitability check."""
        # Simple expression
        simple_expr = MathematicalExpression(
            latex_expression=LaTeXExpression("2 + 2"),
            audience_level=AudienceLevel("elementary")
        )
        
        self.assertTrue(simple_expr.is_suitable_for_audience(AudienceLevel("elementary")))
        self.assertTrue(simple_expr.is_suitable_for_audience(AudienceLevel("graduate")))
        
        # Complex expression
        complex_expr = MathematicalExpression(
            latex_expression=LaTeXExpression(r"\nabla \times \mathbf{F} = 0"),
            audience_level=AudienceLevel("graduate")
        )
        
        self.assertFalse(complex_expr.is_suitable_for_audience(AudienceLevel("elementary")))
        self.assertTrue(complex_expr.is_suitable_for_audience(AudienceLevel("graduate")))
    
    def test_expression_equality(self):
        """Test expression equality comparison."""
        expr1 = MathematicalExpression(
            latex_expression=self.simple_expr,
            audience_level=AudienceLevel("undergraduate")
        )
        expr2 = MathematicalExpression(
            latex_expression=self.simple_expr,
            audience_level=AudienceLevel("undergraduate")
        )
        
        # Different instances with same content
        self.assertNotEqual(expr1, expr2)  # Different IDs
        self.assertEqual(expr1.latex_expression, expr2.latex_expression)
        
    def test_expression_serialization(self):
        """Test expression serialization to dict."""
        expr = MathematicalExpression(
            latex_expression=self.simple_expr,
            audience_level=AudienceLevel("undergraduate"),
            domain_hint=MathematicalDomain("general")
        )
        
        data = expr.to_dict()
        
        self.assertIn("id", data)
        self.assertIn("latex_expression", data)
        self.assertIn("expression_type", data)
        self.assertIn("detected_domain", data)
        self.assertIn("complexity_metrics", data)
        self.assertIn("metadata", data)
        self.assertEqual(data["audience_level"], "undergraduate")


if __name__ == "__main__":
    unittest.main()