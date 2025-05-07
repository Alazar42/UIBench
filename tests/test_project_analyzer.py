import pytest
import json
import zipfile
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from core.utils.zip_utils import safe_extract_zip
from core.utils.diff_utils import compute_diffs
from core.project_analyzer import analyze_project, ProjectAnalyzer
from core.project_analyzer_frameworks import FRAMEWORK_CONFIG
from core.analyzers import (
    AccessibilityAnalyzer,
    PerformanceAnalyzer,
    SEOAnalyzer,
    SecurityAnalyzer,
    UXAnalyzer,
    CodeAnalyzer,
    DesignSystemAnalyzer,
    NLPContentAnalyzer,
    InfrastructureAnalyzer,
    OperationalMetricsAnalyzer,
    ComplianceAnalyzer,
    MutationAnalyzer,
    ContractAnalyzer,
    FuzzAnalyzer
)
from bs4 import BeautifulSoup
import asyncio
import os

def save_test_results(test_name: str, results: dict):
    """Save test results to the analysis_results folder"""
    # Create analysis_results directory if it doesn't exist
    results_dir = Path("analysis_results")
    results_dir.mkdir(exist_ok=True)
    
    # Create timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{test_name}_{timestamp}.json"
    
    # Save results with metadata
    output = {
        "metadata": {
            "test_name": test_name,
            "timestamp": timestamp,
            "version": "1.0.0"
        },
        "results": results
    }
    
    with open(results_dir / filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    return results_dir / filename

@pytest.fixture
def workspace(tmp_path, request):
    """Create a fresh workspace directory for each test."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    return ws

@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project structure for testing"""
    project = tmp_path / "test_project"
    project.mkdir()
    
    # Create package.json
    package_json = {
        "dependencies": {
            "react": "^18.0.0",
            "react-dom": "^18.0.0",
            "@types/react": "^18.0.0"
        },
        "devDependencies": {
            "react-scripts": "^5.0.0"
        }
    }
    
    (project / "package.json").write_text(json.dumps(package_json))
    
    # Create React files
    (project / "src").mkdir()
    (project / "src" / "App.jsx").write_text("import React from 'react';")
    (project / "src" / "index.js").write_text("import React from 'react';")
    
    # Create HTML file for testing
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Test Page</title>
    </head>
    <body>
        <h1>Test Page</h1>
        <nav>
            <a href="#home">Home</a>
        </nav>
        <main>
            <p>Test content</p>
        </main>
    </body>
    </html>
    """
    (project / "public").mkdir()
    (project / "public" / "index.html").write_text(html_content)
    
    return project

def test_safe_extract_zip_traversal(workspace):
    """Test zip extraction security"""
    # Create an evil ZIP with a path traversal entry
    evil_zip = workspace / "evil.zip"
    with zipfile.ZipFile(evil_zip, 'w') as zf:
        zf.writestr("../evil.txt", "malicious")
    with pytest.raises(ValueError):
        safe_extract_zip(str(evil_zip), str(workspace / "out"))

def test_compute_diffs_basic():
    """Test basic diff computation"""
    old = {"a": 1, "b": {"x": 2}}
    new = {"a": 1, "b": {"x": 3}, "c": 4}
    diff = compute_diffs(old, new)
    assert "b.x" in diff["changed"]
    assert "c" in diff["added"]
    assert "b" not in diff["removed"]

@pytest.mark.asyncio
async def test_analyzer_integration(temp_project):
    """Test integration with all analyzers"""
    analyzer = ProjectAnalyzer(temp_project)
    results = {}
    
    # Test all analyzers
    analyzers = {
        'accessibility': AccessibilityAnalyzer(),
        'performance': PerformanceAnalyzer(),
        'seo': SEOAnalyzer(),
        'security': SecurityAnalyzer(),
        'code': CodeAnalyzer(),
        'design_system': DesignSystemAnalyzer(),
        'nlp_content': NLPContentAnalyzer(),
        'infrastructure': InfrastructureAnalyzer(),
        'operational_metrics': OperationalMetricsAnalyzer(),
        'compliance': ComplianceAnalyzer(),
        'mutation': MutationAnalyzer(),
        'contract': ContractAnalyzer(),
        'fuzz': FuzzAnalyzer()
    }
    
    # Run each analyzer
    for name, analyzer_instance in analyzers.items():
        try:
            analyzer_results = await analyzer_instance.analyze(str(temp_project))
            results[name] = analyzer_results
            
            # Verify basic structure
            assert isinstance(analyzer_results, dict)
            assert 'score' in analyzer_results
            assert 'details' in analyzer_results
            assert 'issues' in analyzer_results
            assert 'recommendations' in analyzer_results
            
            # Verify score range
            assert 0 <= analyzer_results['score'] <= 100
            
        except Exception as e:
            results[name] = {
                'error': str(e),
                'score': 0,
                'details': {},
                'issues': [f"Analyzer failed: {str(e)}"],
                'recommendations': ["Fix analyzer setup"]
            }
    
    # Save all analyzer results
    save_test_results("analyzer_integration", results)
    
    return results

@pytest.mark.asyncio
async def test_advanced_testing_integration(temp_project):
    """Test integration of advanced testing analyzers"""
    results = {}
    
    # Test mutation testing
    mutation_analyzer = MutationAnalyzer()
    mutation_results = await mutation_analyzer.analyze(str(temp_project))
    results['mutation'] = mutation_results
    
    # Test contract testing
    contract_analyzer = ContractAnalyzer()
    contract_results = await contract_analyzer.analyze(str(temp_project))
    results['contract'] = contract_results
    
    # Test fuzz testing
    fuzz_analyzer = FuzzAnalyzer()
    fuzz_results = await fuzz_analyzer.analyze(str(temp_project))
    results['fuzz'] = fuzz_results
    
    # Save advanced testing results
    save_test_results("advanced_testing", results)
    
    # Verify mutation testing results
    assert 'score' in mutation_results
    assert 'details' in mutation_results
    assert 'mutations' in mutation_results['details']
    assert 'killed' in mutation_results['details']
    assert 'survived' in mutation_results['details']
    
    # Verify contract testing results
    assert 'score' in contract_results
    assert 'details' in contract_results
    assert 'interactions' in contract_results['details']
    assert 'passed' in contract_results['details']
    assert 'failed' in contract_results['details']
    
    # Verify fuzz testing results
    assert 'score' in fuzz_results
    assert 'details' in fuzz_results
    assert 'executions' in fuzz_results['details']
    assert 'crashes' in fuzz_results['details']
    assert 'coverage' in fuzz_results['details']
    
    return results

@pytest.mark.asyncio
async def test_project_analysis(temp_project):
    """Test complete project analysis"""
    analyzer = ProjectAnalyzer(temp_project)
    results = await analyzer.analyze_project()
    
    # Save complete analysis results
    save_test_results("project_analysis", results)
    
    # Verify framework detection
    assert 'frameworks' in results['current']
    assert isinstance(results['current']['frameworks'], list)
    
    # Verify analyzer results
    assert 'accessibility' in results['current']['dynamic']
    assert 'performance' in results['current']['dynamic']
    assert 'seo' in results['current']['dynamic']
    assert 'security' in results['current']['dynamic']
    assert 'code_quality' in results['current']['dynamic']
    
    # Verify advanced testing results
    assert 'advanced_testing' in results['current']
    advanced = results['current']['advanced_testing']
    assert 'mutation' in advanced
    assert 'contract' in advanced
    assert 'fuzz' in advanced
    
    # Verify metrics
    assert 'overall_metrics' in results['current']
    metrics = results['current']['overall_metrics']
    assert 'code_quality' in metrics
    assert 'security' in metrics
    assert 'accessibility' in metrics
    assert 'performance' in metrics
    assert 'seo' in metrics
    
    return results

@pytest.mark.asyncio
async def test_analyzer_performance(temp_project):
    """Test analyzer performance metrics"""
    analyzer = ProjectAnalyzer(temp_project)
    results = await analyzer.analyze_project()
    
    # Save performance metrics
    save_test_results("analyzer_performance", results)
    
    # Verify performance metrics
    assert 'performance_metrics' in results['current']
    metrics = results['current']['performance_metrics']
    assert 'evaluation' in metrics
    assert 'analyzers' in metrics
    
    # Verify individual analyzer metrics
    analyzer_metrics = metrics['analyzers']
    assert 'accessibility' in analyzer_metrics
    assert 'performance' in analyzer_metrics
    assert 'seo' in analyzer_metrics
    assert 'security' in analyzer_metrics
    assert 'code' in analyzer_metrics
    assert 'mutation_testing' in analyzer_metrics
    assert 'contract_testing' in analyzer_metrics
    assert 'fuzz_testing' in analyzer_metrics
    
    return results