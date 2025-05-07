import asyncio
import unittest
import tempfile
import json
import shutil
from pathlib import Path
from core.project_analyzer import analyze_project

class TestAnalysisSystem(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create sample project
        (self.temp_dir / "index.html").write_text("<html><body>Test</body></html>")
        (self.temp_dir / "style.css").write_text("body { color: red; }")
        (self.temp_dir / "package.json").write_text(json.dumps({
            "dependencies": {"react": "^18.0.0"}
        }))

    async def asyncTearDown(self):
        shutil.rmtree(self.temp_dir)

    async def test_full_analysis_cycle(self):
        # First run
        result1 = await analyze_project(str(self.temp_dir))
        self.assertIn("react", result1["current"]["frameworks"])
        
        # Second run with modification
        (self.temp_dir / "new.html").write_text("<html><body>New</body></html>")
        result2 = await analyze_project(str(self.temp_dir), result1["current"])
        
        # Verify diff
        self.assertIn("new.html", str(result2["diff"]["added"]))
        self.assertEqual(len(result2["current"]["static"]["files"]), 4)

    async def test_error_handling(self):
        # Invalid path
        with self.assertRaises(FileNotFoundError):
            await analyze_project("/invalid/path")
        
        # Corrupted ZIP
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b"invalid content")
            tmp.flush()
            with self.assertRaises(zipfile.BadZipFile):
                await safe_extract_zip(tmp.name, self.temp_dir)

if __name__ == "__main__":
    unittest.main() 