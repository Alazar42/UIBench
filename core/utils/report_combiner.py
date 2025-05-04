from typing import Dict, Any, List
import json
import os
from datetime import datetime
from pathlib import Path

class ReportCombiner:
    """Utility class to combine multiple analyzer JSON files into a single comprehensive report."""
    
    def __init__(self, output_dir: str = "combined_reports"):
        """
        Initialize the ReportCombiner.
        
        Args:
            output_dir: Directory to store combined reports
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def combine_reports(self, json_files: List[str], url: str) -> str:
        """
        Combine multiple analyzer JSON files into a single report.
        
        Args:
            json_files: List of paths to JSON files to combine
            url: URL of the analyzed page
            
        Returns:
            Path to the combined report JSON file
        """
        combined_data = {
            "metadata": {
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "analyzers": []
            },
            "overall_scores": {},
            "detailed_results": {},
            "issues": {},
            "recommendations": []
        }
        
        # Process each JSON file
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                # Extract analyzer type from filename
                analyzer_type = Path(json_file).stem.split('_')[0]
                
                # Add to metadata
                combined_data["metadata"]["analyzers"].append({
                    "type": analyzer_type,
                    "source_file": json_file
                })
                
                # Add scores
                if "results" in data and isinstance(data["results"], dict):
                    results = data["results"]
                    if "overall_score" in results:
                        combined_data["overall_scores"][analyzer_type] = results["overall_score"]
                    
                    # Add detailed results
                    combined_data["detailed_results"][analyzer_type] = results
                    
                    # Collect issues
                    if "issues" in results:
                        combined_data["issues"][analyzer_type] = results["issues"]
                    
                    # Collect recommendations
                    if "recommendations" in results:
                        for rec in results["recommendations"]:
                            if isinstance(rec, dict):
                                rec["analyzer"] = analyzer_type
                                combined_data["recommendations"].append(rec)
            
            except Exception as e:
                print(f"Error processing {json_file}: {str(e)}")
                continue
        
        # Calculate overall score across all analyzers
        if combined_data["overall_scores"]:
            combined_data["overall_score"] = sum(combined_data["overall_scores"].values()) / len(combined_data["overall_scores"])
        else:
            combined_data["overall_score"] = 0
        
        # Generate summary
        combined_data["summary"] = self._generate_summary(combined_data)
        
        # Save combined report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_url = "".join(c if c.isalnum() else "_" for c in url)
        filename = f"{safe_url}_combined_report_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def _generate_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the combined report."""
        summary = {
            "total_analyzers": len(data["metadata"]["analyzers"]),
            "overall_score": data["overall_score"],
            "analyzer_scores": data["overall_scores"],
            "total_issues": sum(len(issues) for issues in data["issues"].values()),
            "total_recommendations": len(data["recommendations"]),
            "critical_issues": []
        }
        
        # Identify critical issues (those with scores below 50)
        for analyzer, results in data["detailed_results"].items():
            if isinstance(results, dict):
                score = results.get("overall_score", 0)
                if score < 50:
                    summary["critical_issues"].append({
                        "analyzer": analyzer,
                        "score": score,
                        "issues": data["issues"].get(analyzer, [])
                    })
        
        return summary 