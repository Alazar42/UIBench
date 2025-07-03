"""
PDF Export Utility for UI Evaluation Results
"""

import time
import os
from typing import Dict, Optional

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class PDFExporter:
    """Export evaluation results to PDF format"""
    
    @staticmethod
    def export_results(results: Dict, filename: Optional[str] = None) -> str:
        """
        Export evaluation results to PDF
        
        Args:
            results: Evaluation results dictionary
            filename: Optional custom filename
            
        Returns:
            Path to the generated PDF file
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is required for PDF export. Install with: pip install reportlab")
        
        # Generate filename if not provided
        if not filename:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"ui_evaluation_{timestamp}.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(filename, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Add content to story
        PDFExporter._add_title(story, styles)
        PDFExporter._add_metadata(story, results, styles)
        PDFExporter._add_summary(story, results, styles)
        PDFExporter._add_analyzers(story, results, styles)
        PDFExporter._add_figma_data(story, results, styles)
        
        # Build PDF
        doc.build(story)
        
        return os.path.abspath(filename)
    
    @staticmethod
    def _add_title(story, styles):
        """Add title to PDF"""
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        story.append(Paragraph("UI Evaluation Report", title_style))
        story.append(Spacer(1, 20))
    
    @staticmethod
    def _add_metadata(story, results, styles):
        """Add metadata section to PDF"""
        if "metadata" not in results:
            return
            
        metadata = results["metadata"]
        story.append(Paragraph("Evaluation Details", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        metadata_data = [
            ["Timestamp", metadata.get('timestamp', 'N/A')],
            ["Evaluation Mode", metadata.get('evaluation_mode', 'N/A')],
            ["Target", str(metadata.get('target', 'N/A'))],
            ["Analyzers Used", ', '.join(metadata.get('analyzers_used', []))]
        ]
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 20))
    
    @staticmethod
    def _add_summary(story, results, styles):
        """Add summary section to PDF"""
        if "summary" not in results:
            return
            
        summary = results["summary"]
        story.append(Paragraph("Overall Assessment", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        summary_data = [
            ["Overall Score", f"{summary.get('overall_score', 0)}/100"],
            ["Status", summary.get('status', 'unknown').replace('_', ' ').title()],
            ["Total Issues", str(summary.get('total_issues', 0))],
            ["Total Recommendations", str(summary.get('total_recommendations', 0))]
        ]
        
        summary_table = Table(summary_data, colWidths=[2*inch, 4*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 20))
    
    @staticmethod
    def _add_analyzers(story, results, styles):
        """Add analyzer results to PDF"""
        if "analyzers" not in results:
            return
            
        story.append(Paragraph("Detailed Analysis", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        for analyzer_key, analyzer_data in results["analyzers"].items():
            analyzer_name = analyzer_data.get("name", analyzer_key.title())
            score = analyzer_data.get("score", 0)
            status = analyzer_data.get("status", "Unknown")
            
            story.append(Paragraph(f"{analyzer_name}", styles['Heading3']))
            story.append(Spacer(1, 6))
            
            # Analyzer summary
            analyzer_summary = [
                ["Score", f"{score}/100"],
                ["Status", status]
            ]
            
            analyzer_table = Table(analyzer_summary, colWidths=[1*inch, 5*inch])
            analyzer_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(analyzer_table)
            story.append(Spacer(1, 12))
            
            # Issues
            issues = analyzer_data.get("issues", [])
            if issues:
                story.append(Paragraph("Issues Found:", styles['Heading4']))
                for issue in issues:
                    story.append(Paragraph(f"• {issue}", styles['Normal']))
                story.append(Spacer(1, 6))
            
            # Recommendations
            recommendations = analyzer_data.get("recommendations", [])
            if recommendations:
                story.append(Paragraph("Recommendations:", styles['Heading4']))
                for rec in recommendations:
                    story.append(Paragraph(f"• {rec}", styles['Normal']))
                story.append(Spacer(1, 12))
    
    @staticmethod
    def _add_figma_data(story, results, styles):
        """Add Figma data to PDF if available"""
        if "figma_data" not in results or not results["figma_data"]:
            return
            
        figma_data = results["figma_data"]
        story.append(Paragraph("Figma Integration Data", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        if "file_info" in figma_data:
            file_info = figma_data["file_info"]
            figma_info_data = [
                ["File Name", file_info.get('name', 'N/A')],
                ["Owner", file_info.get('owner', 'N/A')],
                ["Last Modified", file_info.get('last_modified', 'N/A')]
            ]
            
            figma_table = Table(figma_info_data, colWidths=[2*inch, 4*inch])
            figma_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(figma_table)
            story.append(Spacer(1, 12))
        
        if "components" in figma_data:
            components = figma_data["components"]
            story.append(Paragraph(f"Components Found: {len(components)}", styles['Heading3']))
            for comp in components[:5]:  # Show first 5 components
                story.append(Paragraph(f"• {comp.get('name', 'N/A')}", styles['Normal']))
            if len(components) > 5:
                story.append(Paragraph(f"... and {len(components) - 5} more", styles['Normal']))
            story.append(Spacer(1, 12)) 