from typing import Dict, Any
import json
from datetime import datetime
import os
from pathlib import Path
import json

class BaseAnalyzer:
    """Base class for all analyzers with JSON output support."""
    
    def __init__(self, output_dir: str = "analysis_results"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def _generate_json_filename(self, url: str, analyzer_name: str) -> str:
        """Generate a unique filename for the JSON output."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_url = url.replace("://", "_").replace("/", "_").replace(".", "_")
        return f"{self.output_dir}/{analyzer_name}_{safe_url}_{timestamp}.json"
    
    def save_to_json(self, data: Dict[str, Any], url: str, analyzer_name: str) -> str:
        """
        Save analysis results to a JSON file.
        
        Args:
            data: Analysis results
            url: Target URL
            analyzer_name: Name of the analyzer
            
        Returns:
            Path to the saved JSON file
        """
        filename = self._generate_json_filename(url, analyzer_name)
        
        # Add metadata
        data_with_metadata = {
            "metadata": {
                "analyzer": analyzer_name,
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            },
            "results": data
        }
        
        # Save to file
        with open(filename, 'w') as f:
            json.dump(data_with_metadata, f, indent=2)
        
        return filename
    
    def _standardize_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardize the results structure for JSON output.
        
        Args:
            results: Raw analysis results
            
        Returns:
            Standardized results structure
        """
        standardized = {
            "score": results.get("overall_score", 0),
            "issues": results.get("issues", []),
            "passes": results.get("passes", []),
            "details": results.get("details", {}),
            "recommendations": results.get("recommendations", []),
            "metrics": results.get("metrics", {})
        }
        
        # Remove None values
        return {k: v for k, v in standardized.items() if v is not None}