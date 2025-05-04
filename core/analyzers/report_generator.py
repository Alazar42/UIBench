from typing import Dict, Any, List
import logging
import json
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class ReportGenerator:
    @staticmethod
    def create_executive_summary(data: dict) -> dict:
        return {
            "grades": data.get("aggregated_scores", {}),
            "priority_issues": ReportGenerator.generate_priority_issues(data),
            "comparative_analysis": ReportGenerator.compare_industry_benchmarks(data)
        }

    @staticmethod
    def generate_priority_issues(data: dict) -> List[str]:
        defects = []
        for url, checks in data.get("defect_details", {}).items():
            for check, issues in checks.items():
                defects.extend(issues)
        return defects

    @staticmethod
    def compare_industry_benchmarks(data: dict) -> dict:
        # Dummy static benchmarks
        return {"performance": 90, "accessibility": 95, "security": 85, "seo": 90}

    @staticmethod
    def generate_pdf(data: dict) -> bytes:
        pdf_content = f"Executive Summary:\n{json.dumps(data, indent=2)}"
        return pdf_content.encode("utf-8")

    @staticmethod
    def store_historical_result(data: dict, db=None):
        # Stub: store in MongoDB or other DB
        if db:
            db.results.insert_one({**data, "timestamp": datetime.utcnow()})
        # else: just print or log
        logger.info("Historical result stored.")

    @staticmethod
    def get_trend_analysis(db=None) -> dict:
        # Stub: fetch and analyze historical results
        if db:
            results = list(db.results.find().sort("timestamp", -1).limit(10))
            # Compute trends (dummy)
            return {"trend": "improving" if results else "no data"}
        return {"trend": "no data"} 