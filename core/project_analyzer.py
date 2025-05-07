import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
import asyncio
from playwright.async_api import async_playwright, Browser, Page
import logging
import re
from collections import defaultdict
from core.analyzers.accessibility_analyzer import AccessibilityAnalyzer
from core.analyzers.performance_analyzer import PerformanceAnalyzer
from core.analyzers.seo_analyzer import SEOAnalyzer
from core.analyzers.security_analyzer import SecurityAnalyzer
from core.analyzers.code_analyzer import CodeAnalyzer
from core.utils.diff_utils import compute_diffs
from core.evaluators import ProjectEvaluator
import sys
import shutil
from datetime import datetime
from .analyzers import (
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
from .config import Settings

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ProjectAnalyzer')

class ProjectAnalyzer:
    """Core class for analyzing web projects"""
    
    def __init__(self, project_path: Path):
        self.root = project_path.resolve()
        self.evaluator = ProjectEvaluator(self.root)
        self.framework_config = self.load_framework_config()
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.analysis_results = {
            'frameworks': [],
            'pages': {},
            'overall_metrics': {},
            'framework_specific': {},
            'code_quality': {},
            'dependencies': {},
            'security': {},
            'performance': {},
            'accessibility': {},
            'seo': {},
            'mutation_testing': {},
            'contract_testing': {},
            'fuzz_testing': {}
        }
        
        # Initialize analyzers
        self.accessibility_analyzer = AccessibilityAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()
        self.seo_analyzer = SEOAnalyzer()
        self.security_analyzer = SecurityAnalyzer()
        self.code_quality_analyzer = CodeAnalyzer()
        self.mutation_analyzer = MutationAnalyzer()
        self.contract_analyzer = ContractAnalyzer()
        self.fuzz_analyzer = FuzzAnalyzer()
    
    def load_framework_config(self) -> Dict:
        """Load framework detection configuration with comprehensive framework support"""
        return {
            # Modern Component Frameworks
            'svelte': {
                'required_files': ['svelte.config.js', 'vite.config.ts'],
                'required_deps': ['svelte', '@sveltejs/kit'],
                'optional_deps': ['@sveltejs/adapter-', '@sveltejs/vite-plugin-svelte'],
                'file_patterns': ['**/*.svelte', 'src/routes/+*.svelte'],
                'threshold': 0.7
            },
            'react': {
                'required_files': ['package.json'],
                'required_deps': ['react', 'react-dom'],
                'optional_deps': ['@types/react', 'react-scripts', 'react-refresh'],
                'file_patterns': ['**/*.jsx', '**/*.tsx', 'src/index.js', 'src/index.tsx'],
                'threshold': 0.8
            },
            'preact': {
                'required_files': ['package.json'],
                'required_deps': ['preact'],
                'optional_deps': ['preact-cli', 'preact-router'],
                'file_patterns': ['**/*.jsx', '**/*.tsx'],
                'threshold': 0.7
            },
            'vue': {
                'required_files': ['package.json', 'vite.config.js'],
                'required_deps': ['vue'],
                'optional_deps': ['@vitejs/plugin-vue', 'vue-router', 'vuex'],
                'file_patterns': ['**/*.vue'],
                'threshold': 0.6
            },
            
            # Meta-Frameworks
            'nextjs': {
                'required_files': ['package.json', 'next.config.js'],
                'required_deps': ['next'],
                'optional_deps': ['@next/'],
                'file_patterns': ['pages/**/*.js', 'pages/**/*.tsx', 'app/**/*.js', 'app/**/*.tsx'],
                'threshold': 0.7
            },
            'nuxt': {
                'required_files': ['package.json', 'nuxt.config.js'],
                'required_deps': ['nuxt'],
                'optional_deps': ['@nuxtjs/'],
                'file_patterns': ['pages/**/*.vue', 'layouts/**/*.vue'],
                'threshold': 0.7
            },
            'gatsby': {
                'required_files': ['package.json', 'gatsby-config.js'],
                'required_deps': ['gatsby'],
                'optional_deps': ['gatsby-plugin-', 'gatsby-source-'],
                'file_patterns': ['src/pages/**/*.js', 'src/templates/**/*.js'],
                'threshold': 0.7
            },
            'remix': {
                'required_files': ['package.json', 'remix.config.js'],
                'required_deps': ['@remix-run/'],
                'optional_deps': ['@remix-run/react'],
                'file_patterns': ['app/routes/**/*.tsx', 'app/**/*.tsx'],
                'threshold': 0.7
            },
            'sapper': {
                'required_files': ['package.json', 'sapper.config.js'],
                'required_deps': ['@sapper/'],
                'optional_deps': [],
                'file_patterns': ['src/routes/**/*.svelte'],
                'threshold': 0.7
            },
            'astro': {
                'required_files': ['package.json', 'astro.config.mjs'],
                'required_deps': ['astro'],
                'optional_deps': ['@astrojs/'],
                'file_patterns': ['src/**/*.astro'],
                'threshold': 0.7
            },
            'solid': {
                'required_files': ['package.json'],
                'required_deps': ['solid-js'],
                'optional_deps': ['vite-plugin-solid'],
                'file_patterns': ['**/*.jsx', '**/*.tsx'],
                'threshold': 0.7
            },
            'qwik': {
                'required_files': ['package.json', 'vite.config.ts'],
                'required_deps': ['@builder.io/qwik'],
                'optional_deps': [],
                'file_patterns': ['**/*.tsx'],
                'threshold': 0.7
            },
            'millionjs': {
                'required_files': ['package.json'],
                'required_deps': ['million'],
                'optional_deps': [],
                'file_patterns': ['**/*.js', '**/*.jsx'],
                'threshold': 0.7
            },

            # Full-Stack / Meta-Frameworks
            'redwoodjs': {
                'required_files': ['package.json', 'redwood.toml'],
                'required_deps': ['@redwoodjs/'],
                'optional_deps': [],
                'file_patterns': ['api/**/*.ts', 'web/**/*.tsx'],
                'threshold': 0.7
            },
            'blitzjs': {
                'required_files': ['package.json', 'blitz.config.js'],
                'required_deps': ['blitz'],
                'optional_deps': [],
                'file_patterns': ['app/**/*.{js,ts,jsx,tsx}'],
                'threshold': 0.7
            },
            'hydrogen': {
                'required_files': ['package.json'],
                'required_deps': ['@shopify/hydrogen'],
                'optional_deps': [],
                'file_patterns': ['src/**/*.server.jsx', 'src/**/*.client.jsx'],
                'threshold': 0.7
            },

            # Classic & MVC-Style Frameworks
            'angular': {
                'required_files': ['package.json', 'angular.json'],
                'required_deps': ['@angular/core', '@angular/common'],
                'optional_deps': ['@angular/cli', 'rxjs'],
                'file_patterns': ['**/*.component.ts', '**/*.module.ts'],
                'threshold': 0.7
            },
            'ember': {
                'required_files': ['ember-cli-build.js', 'package.json'],
                'required_deps': ['ember-source', 'ember-cli'],
                'optional_deps': ['ember-data', 'ember-cli-babel'],
                'file_patterns': ['app/**/*.hbs', 'app/**/*.js'],
                'threshold': 0.7
            },
            'meteor': {
                'required_files': ['package.json', 'meteor.settings.json'],
                'required_deps': ['meteor-base', 'meteor'],
                'optional_deps': ['accounts-base', 'mongo'],
                'file_patterns': ['imports/**/*.js', 'client/**/*.js', 'server/**/*.js'],
                'threshold': 0.7
            },
            'dojo': {
                'required_files': ['package.json', 'dojoConfig.js'],
                'required_deps': ['dojo'],
                'optional_deps': ['dijit', 'dojox'],
                'file_patterns': ['**/*.view.html', '**/*.js'],
                'threshold': 0.7
            },
            'extjs': {
                'required_files': ['package.json'],
                'required_deps': ['@sencha/extjs', 'ext'],
                'optional_deps': [],
                'file_patterns': ['**/*.js'],
                'threshold': 0.7
            },
            'mootools': {
                'required_files': ['package.json'],
                'required_deps': ['mootools'],
                'optional_deps': [],
                'file_patterns': ['**/*.js'],
                'threshold': 0.7
            },
            'prototype': {
                'required_files': ['package.json'],
                'required_deps': ['prototype'],
                'optional_deps': ['script.aculo.us'],
                'file_patterns': ['**/*.js'],
                'threshold': 0.7
            },
            'sproutcore': {
                'required_files': ['package.json'],
                'required_deps': ['sproutcore'],
                'optional_deps': [],
                'file_patterns': ['Core/**/*.js'],
                'threshold': 0.7
            },

            # Web-Components & Lightweight Toolkits
            'lit': {
                'required_files': ['package.json'],
                'required_deps': ['lit'],
                'optional_deps': ['@lit/reactive-element'],
                'file_patterns': ['**/*.js', '**/*.ts'],
                'threshold': 0.7
            },
            'polymer': {
                'required_files': ['package.json'],
                'required_deps': ['@polymer/polymer'],
                'optional_deps': [],
                'file_patterns': ['**/*.html'],
                'threshold': 0.7
            },
            'stencil': {
                'required_files': ['package.json'],
                'required_deps': ['@stencil/core'],
                'optional_deps': [],
                'file_patterns': ['src/components/**/*.tsx'],
                'threshold': 0.7
            },
            'hybrids': {
                'required_files': ['package.json'],
                'required_deps': ['hybrids'],
                'optional_deps': [],
                'file_patterns': ['**/*.js'],
                'threshold': 0.7
            },
            'smarthtml': {
                'required_files': ['package.json'],
                'required_deps': ['smarthtml', 'maskjs'],
                'optional_deps': [],
                'file_patterns': ['**/*.html', '**/*.js'],
                'threshold': 0.7
            },

            # Niche & Specialized Solutions
            'mithril': {
                'required_files': ['package.json'],
                'required_deps': ['mithril'],
                'optional_deps': [],
                'file_patterns': ['**/*.js'],
                'threshold': 0.7
            },
            'riot': {
                'required_files': ['package.json'],
                'required_deps': ['riot'],
                'optional_deps': [],
                'file_patterns': ['**/*.tag.html', '**/*.tag.js'],
                'threshold': 0.7
            },
            'stimulus': {
                'required_files': ['package.json'],
                'required_deps': ['@hotwired/stimulus'],
                'optional_deps': [],
                'file_patterns': ['controllers/**/*.js'],
                'threshold': 0.7
            },
            'marko': {
                'required_files': ['package.json'],
                'required_deps': ['marko'],
                'optional_deps': [],
                'file_patterns': ['**/*.marko'],
                'threshold': 0.7
            },
            'enyo': {
                'required_files': ['package.json'],
                'required_deps': ['enyo'],
                'optional_deps': [],
                'file_patterns': ['**/*.js'],
                'threshold': 0.7
            },
            "react": {
                "deps": ["react", "react-dom"],
                "patterns": ["**/*.jsx", "src/App.js"],
                "threshold": 0.8
            },
            "vue": {
                "deps": ["vue"],
                "patterns": ["**/*.vue"],
                "threshold": 0.6
            }
            

        }
    
    async def start(self):
        """Start the Playwright browser"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch()
            self.page = await self.browser.new_page()
            logger.info("Playwright browser started successfully")
        except Exception as e:
            logger.error(f"Failed to start Playwright browser: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the Playwright browser"""
        if self.browser:
            await self.browser.close()
            logger.info("Playwright browser stopped")
    
    async def detect_frameworks(self) -> List[str]:
        """Improved framework detection with fuzzy matching and comprehensive checks"""
        pkg_path = self.root / "package.json"
        if not pkg_path.exists():
            return []
        
        try:
            pkg = json.loads(pkg_path.read_text())
            deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
        except json.JSONDecodeError:
            return []
        
        detected = []
        for name, config in self.framework_config.items():
            score = 0.0
            total_checks = 0
            
            # Check required files
            if 'required_files' in config:
                for file in config['required_files']:
                    total_checks += 1
                    if (self.root / file).exists():
                        score += 1
            
            # Check required dependencies
            if 'required_deps' in config:
                for dep in config['required_deps']:
                    total_checks += 1
                    if any(dep in d for d in deps):
                        score += 1
            
            # Check optional dependencies (weighted less)
            if 'optional_deps' in config:
                for dep in config['optional_deps']:
                    total_checks += 0.5  # Optional deps count half
                    if any(dep in d for d in deps):
                        score += 0.5
            
            # Check file patterns
            if 'file_patterns' in config:
                for pattern in config['file_patterns']:
                    total_checks += 1
                    if any(self.root.glob(pattern)):
                        score += 1
            
            # Calculate final score
            if total_checks > 0:
                final_score = score / total_checks
                if final_score >= config.get('threshold', 0.7):
                    detected.append(name)
                    logger.info(f"Detected framework: {name} (score: {final_score:.2f})")
        
        return list(set(detected))
    
    async def setup_environment(self):
        """Async environment setup with proper cleanup"""
        venv_path = self.root / ".venv"
        if venv_path.exists():
            shutil.rmtree(venv_path)
        
        # Create virtual environment
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "venv", str(venv_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        
        # Install requirements
        req_file = self.root / "requirements.txt"
        if req_file.exists():
            pip = venv_path / "bin" / "pip"
            proc = await asyncio.create_subprocess_exec(
                str(pip), "install", "-r", str(req_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await proc.wait()
    
    async def analyze_project(
        self,
        previous: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Main analysis workflow"""
        # File system analysis
        fs_data = await self.evaluator.evaluate()
        
        # Framework detection
        frameworks = await self.detect_frameworks()
        
        # Environment setup
        await self.setup_environment()
        
        # Dynamic analysis
        dynamic_data = await self.run_dynamic_analysis()
        
        # Advanced testing analysis
        mutation_data = await self.mutation_analyzer.analyze(str(self.root))
        contract_data = await self.contract_analyzer.analyze(str(self.root))
        fuzz_data = await self.fuzz_analyzer.analyze(str(self.root))
        
        # Compile results
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "frameworks": frameworks,
            "static": fs_data,
            "dynamic": dynamic_data,
            "advanced_testing": {
                "mutation": mutation_data,
                "contract": contract_data,
                "fuzz": fuzz_data
            }
        }
        
        # Compute diffs
        if previous:
            return {
                "current": results,
                "diff": compute_diffs(previous, results)
            }
        return {"current": results}
    
    async def run_dynamic_analysis(self) -> Dict[str, Any]:
        """Run dynamic analysis including advanced testing"""
        results = {}
        
        # Run standard analyzers
        results["accessibility"] = await self.accessibility_analyzer.analyze(self.page)
        results["performance"] = await self.performance_analyzer.analyze(self.page)
        results["seo"] = await self.seo_analyzer.analyze(self.page)
        results["security"] = await self.security_analyzer.analyze(self.page)
        results["code_quality"] = await self.code_quality_analyzer.analyze(self.page)
        
        # Run advanced testing analyzers
        results["mutation_testing"] = await self.mutation_analyzer.analyze(str(self.root))
        results["contract_testing"] = await self.contract_analyzer.analyze(str(self.root))
        results["fuzz_testing"] = await self.fuzz_analyzer.analyze(str(self.root))
        
        return results
    
    async def run_axe(self, page) -> Dict:
        """Accessibility audit with axe-core"""
        return await page.evaluate("""async () => {
            await import('https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.7.2/axe.min.js');
            return axe.run();
        }""")
    
    async def get_metrics(self, page) -> Dict:
        """Performance metrics collection"""
        return await page.evaluate("""() => ({
            timing: window.performance.timing.toJSON(),
            entries: window.performance.getEntries()
        })""")
    
    async def get_seo_data(self, page) -> Dict:
        """SEO data collection"""
        return await page.evaluate("""() => {
            const meta = {};
            document.querySelectorAll('meta').forEach(m => {
                const name = m.getAttribute('name') || m.getAttribute('property');
                if (name) meta[name] = m.getAttribute('content');
            });
            return {
                title: document.title,
                meta,
                headings: Array.from(document.querySelectorAll('h1, h2, h3')).map(h => ({
                    level: h.tagName[1],
                    text: h.textContent
                }))
            };
        }""")
    
    async def analyze_page(self, file_path: str) -> Dict[str, Any]:
        """Analyze a single page using Playwright and existing analyzers"""
        if not self.page:
            await self.start()
        
        url = f"file://{os.path.abspath(file_path)}"
        logger.info(f"Analyzing page: {url}")
        
        try:
            await self.page.goto(url)
            await self.page.wait_for_load_state('networkidle')
            
            # Get page content for analysis
            content = await self.page.content()
            
            # Run all analyzers
            accessibility_results = await self.accessibility_analyzer.analyze(self.page)
            performance_results = await self.performance_analyzer.analyze(self.page)
            seo_results = await self.seo_analyzer.analyze(self.page)
            security_results = await self.security_analyzer.analyze(self.page)
            
            return {
                'accessibility': accessibility_results,
                'performance': performance_results,
                'seo': seo_results,
                'security': security_results
            }
            
        except Exception as e:
            logger.error(f"Error analyzing page {file_path}: {str(e)}")
            return {}
    
    def analyze_code_quality(self, file_path: str) -> Dict[str, Any]:
        """Analyze code quality of a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic code quality metrics
            lines = content.split('\n')
            total_lines = len(lines)
            empty_lines = sum(1 for line in lines if not line.strip())
            comment_lines = sum(1 for line in lines if line.strip().startswith(('//', '/*', '*', '#')))
            
            # Complexity metrics
            function_count = len(re.findall(r'function\s+\w+\s*\(', content))
            class_count = len(re.findall(r'class\s+\w+', content))
            
            # Style issues
            long_lines = sum(1 for line in lines if len(line) > 80)
            trailing_whitespace = sum(1 for line in lines if line.rstrip() != line)
            
            return {
                'total_lines': total_lines,
                'empty_lines': empty_lines,
                'comment_lines': comment_lines,
                'function_count': function_count,
                'class_count': class_count,
                'style_issues': {
                    'long_lines': long_lines,
                    'trailing_whitespace': trailing_whitespace
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing code quality for {file_path}: {str(e)}")
            return {}
    
    def analyze_security(self, file_path: str) -> Dict[str, Any]:
        """Analyze security aspects of a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Common security issues to check
            security_issues = {
                'eval_usage': len(re.findall(r'eval\s*\(', content)),
                'inner_html': len(re.findall(r'innerHTML\s*=', content)),
                'dangerous_attributes': len(re.findall(r'dangerouslySetInnerHTML', content)),
                'unsafe_imports': len(re.findall(r'import\s+.*from\s+[\'"](http|https):', content)),
                'sensitive_data': len(re.findall(r'(password|secret|key|token)\s*=', content))
            }
            
            return security_issues
        except Exception as e:
            logger.error(f"Error analyzing security for {file_path}: {str(e)}")
            return {}
    
    def analyze_framework_specific(self, framework: str, file_path: str) -> Dict[str, Any]:
        """Analyze framework-specific aspects of a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {}
            
            if framework == 'react':
                # React-specific analysis
                hooks = re.findall(r'use[A-Z]\w+', content)
                components = re.findall(r'const\s+([A-Z]\w+)\s*=', content)
                analysis.update({
                    'hooks_used': list(set(hooks)),
                    'components_defined': components,
                    'jsx_usage': len(re.findall(r'<[A-Z]', content))
                })
            
            elif framework == 'svelte':
                # Svelte-specific analysis
                stores = re.findall(r'writable|readable|derived', content)
                actions = re.findall(r'use:(\w+)', content)
                analysis.update({
                    'stores_used': list(set(stores)),
                    'actions_used': list(set(actions)),
                    'reactive_declarations': len(re.findall(r'\$:', content))
                })
            
            # Add more framework-specific analysis here
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing framework-specific aspects for {file_path}: {str(e)}")
            return {}
    
    def _calculate_overall_metrics(self):
        """Calculate overall project metrics"""
        # Code quality metrics
        total_files = len(self.analysis_results['code_quality'])
        total_lines = sum(
            metrics.get('total_lines', 0) 
            for metrics in self.analysis_results['code_quality'].values()
            if isinstance(metrics, dict)
        )
        total_functions = sum(
            metrics.get('function_count', 0) 
            for metrics in self.analysis_results['code_quality'].values()
            if isinstance(metrics, dict)
        )
        
        # Security metrics
        total_security_issues = sum(
            len(issues.get('issues', []))
            for issues in self.analysis_results['security'].values()
            if isinstance(issues, dict)
        )
        
        # Accessibility metrics
        total_accessibility_issues = sum(
            len(issues.get('issues', []))
            for issues in self.analysis_results['accessibility'].values()
            if isinstance(issues, dict)
        )
        
        # Performance metrics
        performance_scores = [
            metrics.get('score', 0)
            for metrics in self.analysis_results['performance'].values()
            if isinstance(metrics, dict) and metrics
        ]
        avg_performance_score = sum(performance_scores) / len(performance_scores) if performance_scores else 0
        
        # SEO metrics
        seo_scores = [
            metrics.get('score', 0)
            for metrics in self.analysis_results['seo'].values()
            if isinstance(metrics, dict) and metrics
        ]
        avg_seo_score = sum(seo_scores) / len(seo_scores) if seo_scores else 0
        
        self.analysis_results['overall_metrics'] = {
            'code_quality': {
                'total_files': total_files,
                'total_lines': total_lines,
                'total_functions': total_functions,
                'average_lines_per_file': total_lines / total_files if total_files > 0 else 0
            },
            'security': {
                'total_issues': total_security_issues,
                'files_with_issues': sum(
                    1 for issues in self.analysis_results['security'].values()
                    if isinstance(issues, dict) and issues.get('issues')
                )
            },
            'accessibility': {
                'total_issues': total_accessibility_issues,
                'files_with_issues': sum(
                    1 for issues in self.analysis_results['accessibility'].values()
                    if isinstance(issues, dict) and issues.get('issues')
                )
            },
            'performance': {
                'average_score': avg_performance_score,
                'total_pages': len(performance_scores)
            },
            'seo': {
                'average_score': avg_seo_score,
                'total_pages': len(seo_scores)
            }
        }

async def analyze_project(
    project_path: str,
    previous: Optional[Dict] = None
) -> Dict[str, Any]:
    return await ProjectAnalyzer(Path(project_path)).analyze_project(previous) 