import os
from pathlib import Path
from typing import List, Dict, Optional, Any
import mimetypes
import aiofiles
import esprima
from cssutils import parseString
from bs4 import BeautifulSoup

class FileSystemAnalyzer:
    def __init__(self, project_root: Path):
        self.root = project_root.resolve()
        mimetypes.init()
        self.html_files = []
        self.css_files = []
        self.js_files = []
        self.other_files = []
        
    def scan_project(self) -> Dict[str, List[str]]:
        """Scan the project directory and categorize files."""
        for root, _, files in os.walk(self.root):
            for file in files:
                file_path = Path(root) / file
                mime_type, _ = mimetypes.guess_type(str(file_path))
                
                if mime_type == 'text/html':
                    self.html_files.append(str(file_path))
                elif mime_type == 'text/css':
                    self.css_files.append(str(file_path))
                elif mime_type == 'application/javascript':
                    self.js_files.append(str(file_path))
                else:
                    self.other_files.append(str(file_path))
                    
        return {
            'html_files': self.html_files,
            'css_files': self.css_files,
            'js_files': self.js_files,
            'other_files': self.other_files
        }
    
    async def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Async file analysis with proper parsing"""
        try:
            async with aiofiles.open(file_path, 'r', errors='replace') as f:
                content = await f.read()
            
            result = {
                "path": str(file_path.relative_to(self.root)),
                "size": file_path.stat().st_size,
                "lines": len(content.splitlines()),
                "mime": mimetypes.guess_type(str(file_path))[0] or 'unknown'
            }
            
            if file_path.suffix == '.html':
                soup = BeautifulSoup(content, 'lxml')
                result.update({
                    "type": "html",
                    "title": soup.title.string if soup.title else None,
                    "elements": {
                        "links": [a.get('href') for a in soup.find_all('a')],
                        "images": [img.get('src') for img in soup.find_all('img')],
                        "scripts": [script.get('src') for script in soup.find_all('script')]
                    }
                })
            elif file_path.suffix == '.css':
                sheet = parseString(content)
                result.update({
                    "type": "css",
                    "rules": [rule.selectorText for rule in sheet.cssRules if rule.type == 1]
                })
            elif file_path.suffix in ('.js', '.jsx', '.ts'):
                try:
                    tree = esprima.parseModule(content, range=True)
                    result.update({
                        "type": "javascript",
                        "imports": [node.source.value for node in tree.body 
                                   if isinstance(node, esprima.nodes.ImportDeclaration)],
                        "exports": [node.declaration.name for node in tree.body
                                   if isinstance(node, esprima.nodes.ExportNamedDeclaration)]
                    })
                except Exception as e:
                    result["parse_error"] = str(e)
            
            return result
        except Exception as e:
            return {
                "path": str(file_path.relative_to(self.root)),
                "error": str(e)
            }
    
    def analyze_html_file(self, file_path: str) -> Dict:
        """Analyze a single HTML file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            
            return {
                'title': soup.title.string if soup.title else None,
                'meta_tags': [tag.attrs for tag in soup.find_all('meta')],
                'links': [link.get('href') for link in soup.find_all('a')],
                'images': [img.get('src') for img in soup.find_all('img')],
                'scripts': [script.get('src') for script in soup.find_all('script')],
                'stylesheets': [link.get('href') for link in soup.find_all('link', rel='stylesheet')]
            }
    
    def analyze_css_file(self, file_path: str) -> Dict:
        """Analyze a single CSS file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return {
                'file_size': len(content),
                'selectors': self._extract_selectors(content),
                'media_queries': self._extract_media_queries(content)
            }
    
    def _extract_selectors(self, css_content: str) -> List[str]:
        """Extract CSS selectors from content."""
        # Basic implementation - can be enhanced with proper CSS parsing
        import re
        return re.findall(r'([^{]+){', css_content)
    
    def _extract_media_queries(self, css_content: str) -> List[str]:
        """Extract media queries from content."""
        import re
        return re.findall(r'@media\s*([^{]+){', css_content)
    
    def analyze_js_file(self, file_path: str) -> Dict:
        """Analyze a single JavaScript file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return {
                'file_size': len(content),
                'functions': self._extract_functions(content),
                'imports': self._extract_imports(content)
            }
    
    def _extract_functions(self, js_content: str) -> List[str]:
        """Extract function names from JavaScript content."""
        import re
        return re.findall(r'function\s+(\w+)\s*\(', js_content)
    
    def _extract_imports(self, js_content: str) -> List[str]:
        """Extract import statements from JavaScript content."""
        import re
        return re.findall(r'import\s+.*?from\s+[\'"](.*?)[\'"]', js_content)
    
    def generate_project_structure(self) -> Dict:
        """Generate a tree structure of the project."""
        structure = {}
        
        def build_tree(path: Path, current_dict: Dict):
            if path.is_file():
                current_dict[path.name] = None
            else:
                current_dict[path.name] = {}
                for item in path.iterdir():
                    build_tree(item, current_dict[path.name])
        
        build_tree(self.root, structure)
        return structure 