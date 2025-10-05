#!/usr/bin/env python3
"""
Minify CSS and JavaScript files for production.
This script reduces file sizes by removing whitespace, comments, and optimizing code.
"""
import re
from pathlib import Path


def minify_css(content: str) -> str:
    """Minify CSS by removing comments, whitespace, and optimizing."""
    # Remove comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Remove newlines and extra spaces
    content = re.sub(r'\s+', ' ', content)
    # Remove spaces around special characters
    content = re.sub(r'\s*([{}:;,>+~])\s*', r'\1', content)
    # Remove trailing semicolons
    content = re.sub(r';}', '}', content)
    return content.strip()


def minify_js(content: str) -> str:
    """Minify JavaScript by removing comments and unnecessary whitespace."""
    # Remove single-line comments (but preserve URLs)
    content = re.sub(r'(?<!:)//[^\n]*', '', content)
    # Remove multi-line comments
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # Remove extra whitespace but preserve necessary spacing
    content = re.sub(r'\s+', ' ', content)
    # Remove spaces around operators and punctuation
    content = re.sub(r'\s*([{}()\[\];,<>:=+\-*/%!&|?])\s*', r'\1', content)
    # Add back necessary spaces for keywords
    content = re.sub(r'(\b(?:return|var|let|const|if|else|for|while|function|class)\b)', r' \1 ', content)
    return content.strip()


def process_files(source_dir: Path, output_dir: Path, extensions: dict):
    """Process files with specified extensions using their minify functions."""
    for ext, minify_func in extensions.items():
        for file_path in source_dir.rglob(f'*.{ext}'):
            # Skip already minified files
            if '.min.' in file_path.name:
                continue
                
            content = file_path.read_text(encoding='utf-8')
            minified = minify_func(content)
            
            # Create output path
            relative = file_path.relative_to(source_dir)
            output_file = output_dir / relative.parent / f"{relative.stem}.min.{ext}"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write minified content
            output_file.write_text(minified, encoding='utf-8')
            
            # Calculate size reduction
            original_size = len(content)
            minified_size = len(minified)
            reduction = ((original_size - minified_size) / original_size) * 100
            
            print(f"✓ {relative}: {original_size:,} → {minified_size:,} bytes ({reduction:.1f}% reduction)")


if __name__ == '__main__':
    project_root = Path(__file__).parent.parent
    static_dir = project_root / 'src' / 'app' / 'web' / 'static'
    
    print("🚀 Minifying assets...")
    print()
    
    print("📦 CSS Files:")
    css_dir = static_dir / 'css'
    process_files(css_dir, css_dir, {'css': minify_css})
    
    print()
    print("📦 JavaScript Files:")
    js_dir = static_dir / 'js'
    process_files(js_dir, js_dir, {'js': minify_js})
    
    print()
    print("✨ Minification complete!")
