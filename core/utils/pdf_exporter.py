import time
import textwrap
import os
import logging
from pathlib import Path
from typing import Dict, Optional
from reportlab.platypus import PageBreak, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, mm
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logger = logging.getLogger(__name__)

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
        try:
            if not REPORTLAB_AVAILABLE:
                raise ImportError("reportlab is required for PDF export. Install with: pip install reportlab")
        
            # Generate filename if not provided
            if not filename:
                timestamp = time.strftime('%Y%m%d_%H%M%S')
                filename = f"ui_evaluation_{timestamp}.pdf"
        
            # Create PDF document
            doc = SimpleDocTemplate(filename, pagesize=A4)
            styles = getSampleStyleSheet()
            
            # Create story list at the beginning
            story = []

            # Register Nyala font
            try:
                current_dir = Path(__file__).parent
                nyala_path = current_dir / "Nyala.ttf"
                
                if nyala_path.exists():
                    pdfmetrics.registerFont(TTFont('Nyala', str(nyala_path)))
                    font_name = 'Nyala'
                else:
                    print(f"⚠️ Nyala font not found at: {nyala_path}")
                    print("⚠️ Using Helvetica as fallback")
                    font_name = 'Helvetica'
            except Exception as e:
                print(f"⚠️ Font loading error: {str(e)}")
                print("⚠️ Using Helvetica as fallback")
                font_name = 'Helvetica'
        
            # Add introduction page
            PDFExporter._add_intro_page(story, styles, font_name)
            story.append(PageBreak())  # Start report on new page
        
            # Add report content
            PDFExporter._add_title(story, styles, font_name)
            PDFExporter._add_metadata(story, results, styles, font_name)
            PDFExporter._add_summary(story, results, styles, font_name)
            PDFExporter._add_analyzers(story, results, styles, font_name)
            PDFExporter._add_figma_data(story, results, styles, font_name)
        
            # Build PDF
            doc.build(story)
            return os.path.abspath(filename)
            
        except Exception as e:
            logger.exception("PDF export failed")
            raise RuntimeError(f"PDF generation error: {str(e)}") from e
    
    @staticmethod
    def _add_intro_page(story, styles, font_name):
        """Add professional introduction page with image banner"""
        # Custom styles with adjusted font sizes
        intro_title_style = ParagraphStyle(
            'IntroTitle',
            fontName=font_name,
            fontSize=14,  # Max size 14 as requested
            spaceAfter=10,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            fontName=font_name,
            fontSize=12,
            spaceAfter=8,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        section_style = ParagraphStyle(
            'Section',
            fontName=font_name,
            fontSize=11,  # Normal text size 11 as requested
            spaceAfter=6,
            spaceBefore=10,
            textColor=colors.darkblue
        )
        
        body_style = ParagraphStyle(
            'Body',
            fontName=font_name,
            fontSize=11,  # Normal text size 11
            spaceAfter=4,
            leading=13
        )
        
        # Add UIBench image banner
        try:
            current_dir = Path(__file__).parent
            banner_path = current_dir / "uibench_banner.png"
            
            if banner_path.exists():
                img = Image(str(banner_path), width=150*mm, height=50*mm)
                img.hAlign = 'CENTER'
                story.append(img)
                story.append(Spacer(1, 10))
            else:
                print(f"⚠️ Banner image not found at: {banner_path}")
        except Exception as e:
            print(f"⚠️ Banner loading error: {str(e)}")
        
        # Add title
        story.append(Paragraph("UIBench Core Engine", intro_title_style))
        story.append(Spacer(1, 8))
        
        # Description
        description = textwrap.dedent("""
        UIBench is a Python-based core engine designed to automate the evaluation of 
        web design aesthetics and accessibility. The engine provides comprehensive 
        analysis of web pages through various analyzers and evaluators.
        """)
        story.append(Paragraph(description, body_style))
        story.append(Spacer(1, 11))
        
        # Core Components section
        story.append(Paragraph("Core Components", subtitle_style))
        story.append(Spacer(1, 5))
        
        # Analyzers section
        story.append(Paragraph("Analyzers", section_style))
        analyzers = [
            "• <b>Accessibility Analyzer</b>: Evaluates WCAG compliance and accessibility features",
            "• <b>Code Analyzer</b>: Analyzes HTML, CSS, and JavaScript code quality",
            "• <b>Compliance Analyzer</b>: Checks for legal and regulatory compliance",
            "• <b>Design System Analyzer</b>: Evaluates design consistency and component usage",
            "• <b>Infrastructure Analyzer</b>: Analyzes server configuration and performance",
            "• <b>NLP Analyzer</b>: Performs natural language processing on content",
            "• <b>Operational Metrics Analyzer</b>: Tracks performance and operational metrics",
            "• <b>Performance Analyzer</b>: Measures page load and runtime performance",
            "• <b>Security Analyzer</b>: Checks for security vulnerabilities",
            "• <b>SEO Analyzer</b>: Evaluates search engine optimization",
            "• <b>UX Analyzer</b>: Analyzes user experience and interaction patterns"
        ]
        for item in analyzers:
            story.append(Paragraph(item, body_style))
        
        story.append(Spacer(1, 7))
        
        # Evaluators section
        story.append(Paragraph("Evaluators", section_style))
        evaluators = [
            "• <b>PageEvaluator</b>: Evaluates individual web pages",
            "• <b>WebsiteEvaluator</b>: Evaluates entire websites",
            "• <b>ProjectEvaluator</b>: Evaluates local project files"
        ]
        for item in evaluators:
            story.append(Paragraph(item, body_style))
        
        story.append(Spacer(1, 12))
        
        # Analysis Types section
        story.append(Paragraph("Analysis Options", subtitle_style))
        story.append(Spacer(1, 5))
        
        analysis_types = [
            "1. <b>Website Evaluation</b> (live website analysis)",
            "2. <b>Offline Project Evaluation</b> (local files)",
            "3. <b>Figma Design Evaluation</b> (design system analysis)"
        ]
        
        for item in analysis_types:
            story.append(Paragraph(item, body_style))
            
        story.append(Spacer(1, 11))
        
        # Salutation
        salutation = textwrap.dedent("""
        <i>Thank you for using UIBench! We're committed to helping you create better,
        more accessible, and more efficient user interfaces.</i>
        
        - The UIBench Team
        """)
        story.append(Paragraph(salutation, ParagraphStyle(
            'Salutation',
            parent=body_style,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )))
    
    @staticmethod
    def _add_title(story, styles, font_name):
        """Add title to PDF with custom font and size"""
        title_style = ParagraphStyle(
            'CustomTitle',
            fontName=font_name,
            fontSize=16,
            spaceAfter=15,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        story.append(Paragraph("UI Evaluation Report", title_style))
        story.append(Spacer(1, 10))
    
    @staticmethod
    def _add_metadata(story, results, styles, font_name):
        """Add metadata section to PDF with enhanced formatting"""
        if "metadata" not in results:
            return
        
        metadata = results["metadata"]
    
        # Create custom styles with font
        header_style = ParagraphStyle(
            'MetadataHeader',
            fontName=font_name,
            fontSize=14,
            spaceAfter=10,
            textColor=colors.darkblue
        )
    
        body_style = ParagraphStyle(
            'MetadataBody',
            fontName=font_name,
            fontSize=11,
            leading=13
        )
    
        # Add section header with icon
        story.append(Paragraph("📋 Evaluation Details", header_style))
        story.append(Spacer(1, 8))
    
        # Create metadata table
        metadata_data = [
            ["🕒 Timestamp", metadata.get('timestamp', 'N/A')],
            ["🎛️ Mode", metadata.get('evaluation_mode', 'N/A').capitalize()],
            ["🎯 Target", str(metadata.get('target', 'N/A'))],
            ["🧩 Analyzers", ', '.join(metadata.get('analyzers_used', []))]
        ]
    
        metadata_table = Table(metadata_data, colWidths=[1.5*inch, 4.5*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.darkgrey),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8)
        ]))
        story.append(metadata_table)
        story.append(Spacer(1, 15))

    @staticmethod
    def _add_summary(story, results, styles, font_name):
        """Add summary section to PDF with enhanced formatting and emojis"""
        if "summary" not in results:
            return
        
        summary = results["summary"]
    
        # Create custom styles with font
        header_style = ParagraphStyle(
            'SummaryHeader',
            fontName=font_name,
            fontSize=14,
            spaceAfter=10,
            textColor=colors.darkblue
        )
    
        body_style = ParagraphStyle(
            'SummaryBody',
            fontName=font_name,
            fontSize=11,
            leading=13
        )   
    
        # Determine status icon and color
        score = summary.get('overall_score', 0)
        if score >= 80:
            status_icon = "🟢"
            status_color = colors.green
        elif score >= 60:
            status_icon = "🟡"
            status_color = colors.orange
        else:
            status_icon = "🔴"
            status_color = colors.red
    
        # Add section header with icon
        story.append(Paragraph("📊 Overall Assessment", header_style))
        story.append(Spacer(1, 8))
    
        # Create summary table
        summary_data = [
            [f"{status_icon} Score", f"<b>{score}/100</b>"],
            ["📊 Page Class", summary.get('page_class', 'N/A')],
            ["⚠️ Issues Found", str(summary.get('total_issues', 0))],
            ["💡 Recommendations", str(summary.get('total_recommendations', 0))]
        ]
    
        summary_table = Table(summary_data, colWidths=[1.5*inch, 4.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.darkgrey),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TEXTCOLOR', (1, 0), (1, 0), status_color),
            ('FONTWEIGHT', (1, 0), (1, 0), 'Bold')
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 15))
    
    @staticmethod
    def _add_analyzers(story, results, styles, font_name):
        """Add analyzer results to PDF with custom font and full details"""
        if "analyzers" not in results:
            return
            
        section_style = ParagraphStyle(
            'Section',
            fontName=font_name,
            fontSize=12,
            spaceAfter=6,
            spaceBefore=10,
            textColor=colors.darkblue
        )
        
        body_style = ParagraphStyle(
            'Body',
            fontName=font_name,
            fontSize=11,
            spaceAfter=5,
            leading=13
        )
        
        story.append(Paragraph("Detailed Analysis", section_style))
        story.append(Spacer(1, 8))
        
        for analyzer_key, analyzer_data in results["analyzers"].items():
            analyzer_name = analyzer_data.get("name", analyzer_key.title())
            score = analyzer_data.get("score", 0)
            status = analyzer_data.get("status", "Unknown")
            
            # Determine status color
            if score >= 80:
                status_color = colors.green
                status_icon = "🟢"
            elif score >= 60:
                status_color = colors.orange
                status_icon = "🟡"
            else:
                status_color = colors.red
                status_icon = "🔴"
            
            # Analyzer header
            story.append(Paragraph(
                f"{status_icon} <b>{analyzer_name}</b>", 
                ParagraphStyle(
                    'AnalyzerHeader', 
                    fontName=font_name, 
                    fontSize=12, 
                    textColor=status_color
                )
            ))
            story.append(Spacer(1, 5))
            
            # Score and status
            story.append(Paragraph(
                f"<b>Score:</b> {score}/100 | <b>Status:</b> {status}", 
                body_style
            ))
            story.append(Spacer(1, 8))
            
            # Issues - show ALL issues
            issues = analyzer_data.get("issues", [])
            if issues:
                story.append(Paragraph("⚠️ <b>Issues Found:</b>", body_style))
                for issue in issues:
                    story.append(Paragraph(f"• {issue}", body_style))
                story.append(Spacer(1, 8))
            
            # Recommendations - show ALL recommendations
            recommendations = analyzer_data.get("recommendations", [])
            if recommendations:
                story.append(Paragraph("💡 <b>Recommendations:</b>", body_style))
                for rec in recommendations:
                    story.append(Paragraph(f"• {rec}", body_style))
                story.append(Spacer(1, 8))
            
            # Key Metrics
            metrics = analyzer_data.get("metrics", {})
            if metrics:
                story.append(Paragraph("📏 <b>Key Metrics:</b>", body_style))
                for metric_name, metric_value in metrics.items():
                    story.append(Paragraph(f"• {metric_name}: {metric_value}", body_style))
                story.append(Spacer(1, 10))
    
    @staticmethod
    def _add_figma_data(story, results, styles, font_name):
        """Add Figma data to PDF if available with custom font and full details"""
        # Check if figma data exists
        figma_data = results.get("figma_data")
        if not figma_data:
            return
            
        # Create custom styles
        header_style = ParagraphStyle(
            'FigmaHeader',
            fontName=font_name,
            fontSize=12,
            spaceAfter=10,
            textColor=colors.darkblue
        )
        
        body_style = ParagraphStyle(
            'FigmaBody',
            fontName=font_name,
            fontSize=11,
            leading=13
        )
        
        story.append(Paragraph("Figma Integration Data", header_style))
        story.append(Spacer(1, 8))
        
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
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.darkgrey)
            ]))
            story.append(figma_table)
            story.append(Spacer(1, 8))
        
        if "components" in figma_data:
            components = figma_data["components"]
            story.append(Paragraph(f"Components Found: {len(components)}", header_style))
            story.append(Spacer(1, 5))
            
            for comp in components:
                story.append(Paragraph(f"• {comp.get('name', 'N/A')}", body_style))
            story.append(Spacer(1, 10))