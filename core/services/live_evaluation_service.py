import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .filesystem_analyzer import FileSystemAnalyzer
from ..engine import PageEvaluator, WebsiteEvaluator

class LiveEvaluationHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
        
    def on_modified(self, event):
        if not event.is_directory:
            self.callback(event.src_path)

class LiveEvaluationService:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.analyzer = FileSystemAnalyzer(project_root)
        self.observer = Observer()
        self.evaluation_results = {}
        self.watchers = {}
        
    async def start(self):
        """Start the live evaluation service."""
        # Initial project scan
        project_structure = self.analyzer.scan_project()
        
        # Set up file watchers
        handler = LiveEvaluationHandler(self._handle_file_change)
        self.observer.schedule(handler, str(self.project_root), recursive=True)
        self.observer.start()
        
        # Initial evaluation
        await self._evaluate_project()
        
    def stop(self):
        """Stop the live evaluation service."""
        self.observer.stop()
        self.observer.join()
        
    async def _handle_file_change(self, file_path: str):
        """Handle file changes and trigger re-evaluation."""
        file_path = Path(file_path)
        if file_path.suffix in ['.html', '.css', '.js']:
            await self._evaluate_file(file_path)
            
    async def _evaluate_file(self, file_path: Path):
        """Evaluate a single file."""
        if file_path.suffix == '.html':
            analysis = self.analyzer.analyze_html_file(str(file_path))
            evaluator = PageEvaluator(
                url=None,  # Not needed for local files
                html=analysis,
                page=None,  # Not needed for local files
                body_text=analysis.get('body', ''),
                custom_criteria={}
            )
            result = await evaluator.evaluate()
            self.evaluation_results[str(file_path)] = result
            
        elif file_path.suffix == '.css':
            analysis = self.analyzer.analyze_css_file(str(file_path))
            # Add CSS-specific evaluation logic here
            
        elif file_path.suffix == '.js':
            analysis = self.analyzer.analyze_js_file(str(file_path))
            # Add JavaScript-specific evaluation logic here
            
    async def _evaluate_project(self):
        """Evaluate the entire project."""
        project_structure = self.analyzer.generate_project_structure()
        
        # Evaluate all HTML files
        for html_file in self.analyzer.html_files:
            await self._evaluate_file(Path(html_file))
            
        # Evaluate all CSS files
        for css_file in self.analyzer.css_files:
            await self._evaluate_file(Path(css_file))
            
        # Evaluate all JavaScript files
        for js_file in self.analyzer.js_files:
            await self._evaluate_file(Path(js_file))
            
    def get_evaluation_results(self) -> Dict:
        """Get the current evaluation results."""
        return self.evaluation_results
        
    def get_project_structure(self) -> Dict:
        """Get the current project structure."""
        return self.analyzer.generate_project_structure()
        
    def get_file_analysis(self, file_path: str) -> Optional[Dict]:
        """Get analysis for a specific file."""
        file_path = Path(file_path)
        if file_path.suffix == '.html':
            return self.analyzer.analyze_html_file(str(file_path))
        elif file_path.suffix == '.css':
            return self.analyzer.analyze_css_file(str(file_path))
        elif file_path.suffix == '.js':
            return self.analyzer.analyze_js_file(str(file_path))
        return None 