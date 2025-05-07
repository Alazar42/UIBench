import asyncio
from pathlib import Path
from typing import Dict, Any
from core.analyzers.filesystem_analyzer import FileSystemAnalyzer

class ProjectEvaluator:
    def __init__(self, project_root: Path):
        self.root = project_root
        self.fs = FileSystemAnalyzer(project_root)
        self.ignore_dirs = {'.git', 'node_modules', 'venv', '__pycache__'}

    async def evaluate(self) -> Dict[str, Any]:
        """Async evaluation with parallel processing"""
        files = {}
        metrics = {
            "total_files": 0,
            "total_size": 0,
            "file_types": {},
            "errors": 0
        }
        
        tasks = []
        for path in self.root.rglob('*'):
            if path.is_file() and not any(p in self.ignore_dirs for p in path.parts):
                tasks.append(self.process_file(path))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                metrics["errors"] += 1
                continue
            
            if "error" in result:
                metrics["errors"] += 1
                continue
            
            files[result["path"]] = result
            metrics["total_files"] += 1
            metrics["total_size"] += result["size"]
            file_type = result.get("type", "unknown")
            metrics["file_types"][file_type] = metrics["file_types"].get(file_type, 0) + 1
        
        return {
            "structure": await self.generate_structure(),
            "files": files,
            "metrics": metrics
        }
    
    async def process_file(self, path: Path) -> Dict[str, Any]:
        return await self.fs.analyze_file(path)
    
    async def generate_structure(self) -> Dict:
        """Generate directory structure with async I/O"""
        structure = {}
        
        async def walk(path: Path) -> Dict:
            if path.name in self.ignore_dirs:
                return None
            
            if path.is_file():
                return None
            
            children = {}
            for child in path.iterdir():
                children[child.name] = await walk(child)
            return {"type": "directory", "children": children}
        
        return await walk(self.root) 