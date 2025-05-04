from .security_analyzer import SecurityAnalyzer
from .compliance_analyzer import ComplianceAnalyzer
from .infrastructure_analyzer import InfrastructureAnalyzer
from .operational_metrics_analyzer import OperationalMetricsAnalyzer
from .design_system_analyzer import DesignSystemAnalyzer
from .nlp_content_analyzer import NLPContentAnalyzer
from .report_generator import ReportGenerator
import json

class PageEvaluator:
    def __init__(self, url, page, design_data):
        self.url = url
        self.page = page
        self.design_data = design_data

    async def evaluate(self) -> dict:
        results = {}
        security_analyzer = SecurityAnalyzer()
        compliance_analyzer = ComplianceAnalyzer()
        infrastructure_analyzer = InfrastructureAnalyzer()
        operational_metrics_analyzer = OperationalMetricsAnalyzer()
        design_system_analyzer = DesignSystemAnalyzer()
        nlp_content_analyzer = NLPContentAnalyzer()
        
        results["security"] = await security_analyzer.analyze(self.url, self.page)
        results["compliance"] = await compliance_analyzer.analyze(self.page)
        results["infrastructure"] = await infrastructure_analyzer.analyze(self.url, self.page)
        results["operational_metrics"] = await operational_metrics_analyzer.analyze(self.page)
        html = await self.page.content()
        results["design_system"] = await design_system_analyzer.analyze(self.url, html, self.design_data)
        
        # NLP/content analysis
        body_text = await self.page.inner_text("body")
        results["nlp_content"] = await nlp_content_analyzer.analyze(body_text)
        
        # Executive summary and reporting
        summary = ReportGenerator.create_executive_summary(results)
        return {"url": self.url, "results": results, "summary": summary, "design_data": self.design_data} 