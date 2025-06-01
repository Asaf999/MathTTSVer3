#!/usr/bin/env python3
"""
MathTTSVer3 - LaTeX to Natural Speech Converter
Simple script to convert LaTeX documents to natural mathematical speech
"""

import re
import yaml
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional

class MathTTSConverter:
    """Main converter class for LaTeX to speech"""
    
    def __init__(self, patterns_dir: str = "patterns"):
        self.patterns_dir = Path(patterns_dir)
        self.patterns = self.load_all_patterns()
        self.stats = {'total': 0, 'converted': 0, 'fallback': 0}
        
    def load_all_patterns(self) -> List[Dict]:
        """Load all pattern files from the patterns directory"""
        patterns = []
        
        if not self.patterns_dir.exists():
            print(f"Warning: Patterns directory '{self.patterns_dir}' not found")
            return patterns
        
        # Define loading priority (Stage 4 highest, Stage 1 lowest)
        priority_paths = [
            # Stage 4 - Perfect naturalness
            "advanced/mathematical_narratives.yaml",
            "core/natural_language_enhancers.yaml",
            # Stage 3 - Advanced NLP
            "advanced/theorem_narration.yaml",
            "advanced/concept_explanations.yaml", 
            "advanced/speech_flow.yaml",
            # Stage 2 - Context aware
            "educational/professor_style.yaml",
            "audience_adaptations/undergraduate.yaml",
            # Stage 1 - Basic patterns
            "calculus/derivatives.yaml",
            "calculus/integrals.yaml",
            "basic/fractions.yaml",
            "basic/arithmetic.yaml",
            "algebra/equations.yaml",
            "special/symbols_greek.yaml"
        ]
        
        # Load patterns in priority order
        for rel_path in priority_paths:
            full_path = self.patterns_dir / rel_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    if data and 'patterns' in data:
                        patterns.extend(data['patterns'])
                except Exception as e:
                    print(f"Warning: Error loading {rel_path}: {e}")
        
        # Also load any other pattern files not in priority list
        for pattern_file in self.patterns_dir.rglob("*.yaml"):
            rel_path = pattern_file.relative_to(self.patterns_dir)
            if str(rel_path) not in priority_paths:
                try:
                    with open(pattern_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    if data and 'patterns' in data:
                        patterns.extend(data['patterns'])
                except Exception:
                    pass
        
        print(f"Loaded {len(patterns)} conversion patterns")
        return patterns
    
    def convert_expression(self, latex: str, context: str = "") -> str:
        """Convert a single LaTeX expression to natural speech"""
        self.stats['total'] += 1
        
        # Clean the LaTeX
        latex = latex.strip()
        
        # Try special cases first
        special_conversions = {
            r'e\^{i\\pi} \+ 1 = 0': "Euler's remarkable identity shows us that e raised to the power of i pi plus 1 equals zero, beautifully connecting five fundamental mathematical constants",
            r'\\frac{-b \\pm \\sqrt{b\^2-4ac}}{2a}': "the solutions to our quadratic equation are given by x equals negative b plus or minus the square root of the discriminant b squared minus 4ac, all divided by 2a",
            r'\\sum_{n=0}\^{\\infty}': "the sum from n equals 0 to infinity",
            r'\\int_a\^b': "the integral from a to b",
            r'\\frac{d}{dx}': "the derivative with respect to x",
            r'\\lim_{x \\to a}': "the limit as x approaches a"
        }
        
        for pattern, replacement in special_conversions.items():
            if re.search(pattern, latex):
                self.stats['converted'] += 1
                return replacement + " of " + self._extract_expression_content(latex)
        
        # Try pattern matching
        best_match = None
        best_score = 0
        
        for pattern in self.patterns:
            if 'pattern' not in pattern or 'output_template' not in pattern:
                continue
                
            try:
                # Simple scoring based on pattern features
                score = 0
                template = pattern.get('output_template', '').lower()
                
                # Check for natural language indicators
                if any(phrase in template for phrase in ['which', 'tells us', 'we have', 'shows']):
                    score += 2
                if any(phrase in template for phrase in ['beautiful', 'remarkable', 'elegant']):
                    score += 1
                if pattern.get('naturalness_score', 0) >= 5:
                    score += 3
                    
                # Try to match (simplified)
                pattern_str = pattern['pattern']
                if self._pattern_matches(pattern_str, latex):
                    if score > best_score:
                        best_score = score
                        best_match = pattern
                        
            except Exception:
                continue
        
        if best_match:
            self.stats['converted'] += 1
            return self._apply_template(best_match['output_template'], latex)
        
        # Fallback conversions
        self.stats['fallback'] += 1
        return self._fallback_conversion(latex)
    
    def _pattern_matches(self, pattern: str, latex: str) -> bool:
        """Check if a pattern matches the LaTeX (simplified)"""
        # Very simplified pattern matching
        # In a real implementation, this would use proper regex
        
        # Check for key structures
        pattern_key = pattern.replace('\\\\', '\\').replace('\\s*', '').replace('\\{', '{').replace('\\}', '}')
        latex_key = latex.replace(' ', '')
        
        return pattern_key in latex_key or latex_key in pattern_key
    
    def _apply_template(self, template: str, latex: str) -> str:
        """Apply output template to LaTeX (simplified)"""
        # This is a simplified version
        # Real implementation would parse LaTeX and substitute properly
        return template
    
    def _extract_expression_content(self, latex: str) -> str:
        """Extract the main content from a LaTeX expression"""
        # Remove common LaTeX commands
        content = latex
        content = re.sub(r'\\[a-zA-Z]+', '', content)
        content = re.sub(r'[{}]', '', content)
        content = re.sub(r'\^', ' to the power ', content)
        content = re.sub(r'_', ' subscript ', content)
        return content.strip()
    
    def _fallback_conversion(self, latex: str) -> str:
        """Basic fallback conversion for unmatched patterns"""
        # Simple replacements
        conversions = {
            r'\\frac\{([^}]+)\}\{([^}]+)\}': r'the fraction \1 over \2',
            r'\\sqrt\{([^}]+)\}': r'the square root of \1',
            r'\\sin': 'sine',
            r'\\cos': 'cosine',
            r'\\tan': 'tangent',
            r'\\log': 'logarithm',
            r'\\ln': 'natural logarithm',
            r'\\alpha': 'alpha',
            r'\\beta': 'beta',
            r'\\gamma': 'gamma',
            r'\\delta': 'delta',
            r'\\pi': 'pi',
            r'\\infty': 'infinity',
            r'\\sum': 'the sum',
            r'\\prod': 'the product',
            r'\^2': ' squared',
            r'\^3': ' cubed',
            r'\^': ' to the power of ',
            r'_': ' subscript ',
            r'\\cdot': ' times ',
            r'\\times': ' times ',
            r'\\div': ' divided by ',
            r'\\pm': ' plus or minus ',
            r'\\leq': ' less than or equal to ',
            r'\\geq': ' greater than or equal to ',
            r'\\neq': ' not equal to ',
            r'=': ' equals ',
            r'\+': ' plus ',
            r'-': ' minus '
        }
        
        result = latex
        for pattern, replacement in conversions.items():
            result = re.sub(pattern, replacement, result)
        
        # Clean up
        result = re.sub(r'\\[a-zA-Z]+', '', result)
        result = re.sub(r'[{}]', '', result)
        result = re.sub(r'\s+', ' ', result)
        
        return f"the expression {result.strip()}"
    
    def process_document(self, content: str, doc_type: str = "tex") -> List[Dict]:
        """Process a document and extract LaTeX expressions"""
        results = []
        
        if doc_type == "tex":
            # LaTeX document patterns
            patterns = [
                (r'\\begin\{equation\}(.*?)\\end\{equation\}', 'display'),
                (r'\$\$(.*?)\$\$', 'display'),
                (r'\$(.*?)\$', 'inline'),
                (r'\\\[(.*?)\\\]', 'display'),
                (r'\\\((.*?)\\\)', 'inline')
            ]
        elif doc_type == "md":
            # Markdown patterns
            patterns = [
                (r'\$\$(.*?)\$\$', 'display'),
                (r'\$(.*?)\$', 'inline')
            ]
        else:
            # Plain text - same as markdown
            patterns = [
                (r'\$\$(.*?)\$\$', 'display'),
                (r'\$(.*?)\$', 'inline')
            ]
        
        # Extract and convert expressions
        for pattern, expr_type in patterns:
            for match in re.finditer(pattern, content, re.DOTALL):
                latex = match.group(1).strip()
                if latex:  # Skip empty expressions
                    speech = self.convert_expression(latex)
                    results.append({
                        'type': expr_type,
                        'latex': latex,
                        'speech': speech,
                        'position': match.start()
                    })
        
        # Sort by position to maintain document order
        results.sort(key=lambda x: x['position'])
        
        return results
    
    def process_file(self, filepath: str) -> List[Dict]:
        """Process a file containing LaTeX"""
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Determine file type
        suffix = filepath.suffix.lower()
        if suffix == '.tex':
            doc_type = 'tex'
        elif suffix == '.md':
            doc_type = 'md'
        elif suffix in ['.txt', '.text']:
            doc_type = 'txt'
        else:
            print(f"Warning: Unknown file type '{suffix}', treating as plain text")
            doc_type = 'txt'
        
        # Read and process file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.process_document(content, doc_type)
    
    def print_results(self, results: List[Dict], verbose: bool = False):
        """Print conversion results"""
        if not results:
            print("No mathematical expressions found in the document.")
            return
        
        print(f"\nFound {len(results)} mathematical expressions:\n")
        print("="*80)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Type: {result['type'].upper()}")
            print(f"   LaTeX: {result['latex'][:60]}{'...' if len(result['latex']) > 60 else ''}")
            print(f"   Speech: {result['speech'][:120]}{'...' if len(result['speech']) > 120 else ''}")
            
            if verbose:
                print(f"   Full LaTeX: {result['latex']}")
                print(f"   Full Speech: {result['speech']}")
        
        print("\n" + "="*80)
        print(f"Conversion Statistics:")
        print(f"  Total expressions: {self.stats['total']}")
        print(f"  Pattern matches: {self.stats['converted']}")
        print(f"  Fallback conversions: {self.stats['fallback']}")
        print(f"  Success rate: {(self.stats['converted']/max(self.stats['total'],1))*100:.1f}%")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Convert LaTeX mathematical expressions to natural speech",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python convert_latex.py document.tex
  python convert_latex.py paper.tex -o speech.txt
  python convert_latex.py notes.md -v
  
Supported file types:
  .tex  - LaTeX documents
  .md   - Markdown with LaTeX
  .txt  - Plain text with LaTeX expressions
        """
    )
    
    parser.add_argument('input_file', help='Input file containing LaTeX expressions')
    parser.add_argument('-o', '--output', help='Output file for speech text')
    parser.add_argument('-v', '--verbose', action='store_true', 
                       help='Show full expressions and conversions')
    parser.add_argument('-p', '--patterns-dir', default='patterns',
                       help='Directory containing pattern files (default: patterns)')
    
    args = parser.parse_args()
    
    # Create converter
    converter = MathTTSConverter(args.patterns_dir)
    
    try:
        # Process file
        results = converter.process_file(args.input_file)
        
        # Output results
        if args.output:
            # Write to file
            with open(args.output, 'w', encoding='utf-8') as f:
                for result in results:
                    f.write(f"[{result['type'].upper()}]\n")
                    f.write(f"LaTeX: {result['latex']}\n")
                    f.write(f"Speech: {result['speech']}\n")
                    f.write("\n")
            print(f"Results written to: {args.output}")
        else:
            # Print to console
            converter.print_results(results, args.verbose)
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()