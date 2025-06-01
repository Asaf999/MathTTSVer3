"""Devil test cases - the most challenging expressions."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest

from src.domain.value_objects import LaTeXExpression


class TestDevilCases:
    """Test cases for extremely complex mathematical expressions."""
    
    # Test case categories
    DEEP_NESTING = [
        # Deeply nested fractions
        r"\frac{\frac{\frac{a}{b}}{c}}{\frac{d}{\frac{e}{f}}}",
        r"\frac{1}{\frac{2}{\frac{3}{\frac{4}{5}}}}",
        
        # Nested functions
        r"\sin(\cos(\tan(\log(\exp(x)))))",
        r"\sqrt{\sqrt{\sqrt{\sqrt{x}}}}",
        
        # Mixed nesting
        r"\frac{\sin(\frac{x}{y})}{\cos(\frac{a}{b})}",
    ]
    
    COMPLEX_INTEGRALS = [
        # Integral limits containing integrals
        r"\int_{\int_0^1 f(x)dx}^{\int_0^2 g(x)dx} h(t) dt",
        
        # Multiple integrals with complex bounds
        r"\int_0^1 \int_0^x \int_0^y f(x,y,z) dz dy dx",
        
        # Integrals with complex integrands
        r"\int_0^\infty \frac{\sin(x^2)}{x^{1/2}} e^{-x} dx",
    ]
    
    MIXED_NOTATION = [
        # Mixing different mathematical domains
        r"\lim_{x \to \lim_{y \to 0} f(y)} g(x)",
        r"\sum_{i=1}^{\prod_{j=1}^n a_j} b_i",
        
        # Complex subscripts and superscripts
        r"x_{i_j}^{k^l}",
        r"a_{b_{c_{d_e}}}",
        
        # Conditional expressions
        r"\begin{cases} x^2 & \text{if } x > 0 \\ -x^2 & \text{if } x \leq 0 \end{cases}",
    ]
    
    SPECIAL_CHARACTERS = [
        # Mixed alphabets
        r"\alpha + \Beta - \gamma \times \Delta",
        
        # Special operators
        r"\nabla \times \vec{F} = \frac{\partial F_z}{\partial y} - \frac{\partial F_y}{\partial z}",
        
        # Matrix notation
        r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}^{-1}",
    ]
    
    LONG_EXPRESSIONS = [
        # Very long sum
        r"\sum_{i=1}^{100} \sum_{j=1}^{100} \sum_{k=1}^{100} a_{ijk} x^i y^j z^k",
        
        # Long continued fraction
        r"1 + \cfrac{1}{2 + \cfrac{1}{3 + \cfrac{1}{4 + \cfrac{1}{5 + \ddots}}}}",
    ]
    
    @pytest.mark.parametrize("expression", DEEP_NESTING)
    def test_deep_nesting(self, expression):
        """Test deeply nested expressions."""
        # Should not raise validation error
        expr = LaTeXExpression(expression)
        assert expr.value == expression
    
    @pytest.mark.parametrize("expression", COMPLEX_INTEGRALS)
    def test_complex_integrals(self, expression):
        """Test complex integral expressions."""
        expr = LaTeXExpression(expression)
        assert expr.value == expression
    
    @pytest.mark.parametrize("expression", MIXED_NOTATION)
    def test_mixed_notation(self, expression):
        """Test mixed mathematical notation."""
        expr = LaTeXExpression(expression)
        assert expr.value == expression
    
    @pytest.mark.parametrize("expression", SPECIAL_CHARACTERS)
    def test_special_characters(self, expression):
        """Test expressions with special characters."""
        expr = LaTeXExpression(expression)
        assert expr.value == expression
    
    @pytest.mark.parametrize("expression", LONG_EXPRESSIONS)
    def test_long_expressions(self, expression):
        """Test very long expressions."""
        expr = LaTeXExpression(expression)
        assert expr.value == expression
    
    def test_devil_case_command_extraction(self):
        """Test command extraction from complex expressions."""
        expr = LaTeXExpression(r"\int_{\sum_{i=1}^n x_i}^{\lim_{x \to \infty} f(x)} g(t) dt")
        commands = expr.extract_commands()
        
        expected = {"int", "sum", "lim", "to", "infty"}
        assert set(commands) >= expected  # May have more
    
    def test_pathological_spacing(self):
        """Test expressions with unusual spacing."""
        expressions = [
            r"\frac{ 1 }{ 2 }",  # Extra spaces
            r"\frac{1}{2}",      # No spaces
            r"\frac{\,1\,}{\,2\,}",  # Thin spaces
        ]
        
        for expr_str in expressions:
            expr = LaTeXExpression(expr_str)
            assert expr.value == expr_str
    
    def test_unicode_in_text(self):
        """Test expressions with unicode in text commands."""
        expr = LaTeXExpression(r"\text{Temperature: 25°C}")
        assert "text" in expr.extract_commands()
    
    def test_empty_arguments(self):
        """Test commands with empty arguments."""
        expressions = [
            r"\frac{}{2}",  # Empty numerator
            r"\sqrt{}",     # Empty square root
            r"\sum_{}^{n}", # Empty lower bound
        ]
        
        for expr_str in expressions:
            expr = LaTeXExpression(expr_str)
            assert expr.value == expr_str