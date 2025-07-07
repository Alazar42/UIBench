# UIBench Core Engine

UIBench is a Python-based core engine designed to automate the evaluation of web design aesthetics and accessibility. The engine provides comprehensive analysis of web pages through various analyzers and evaluators.

## Core Components

### Analyzers
- **Accessibility Analyzer**: Evaluates WCAG compliance and accessibility features
- **Code Analyzer**: Analyzes HTML, CSS, and JavaScript code quality
- **Compliance Analyzer**: Checks for legal and regulatory compliance
- **Design System Analyzer**: Evaluates design consistency and component usage
- **Infrastructure Analyzer**: Analyzes server configuration and performance
- **NLP Analyzer**: Performs natural language processing on content
- **Operational Metrics Analyzer**: Tracks performance and operational metrics
- **Performance Analyzer**: Measures page load and runtime performance
- **Security Analyzer**: Checks for security vulnerabilities
- **SEO Analyzer**: Evaluates search engine optimization
- **UX Analyzer**: Analyzes user experience and interaction patterns

### Evaluators
- **PageEvaluator**: Evaluates individual web pages
- **WebsiteEvaluator**: Evaluates entire websites
- **ProjectEvaluator**: Evaluates local project files

## Core Architecture and Concepts

### System Overview

UIBench's core engine is built on a modular architecture that separates concerns and allows for flexible analysis of web interfaces. The system is designed to be:

1. **Extensible**: New analyzers can be added without modifying existing code
2. **Configurable**: Each component can be customized through settings
3. **Asynchronous**: Built for high-performance concurrent analysis
4. **Cached**: Results are cached to improve performance
5. **Error-Resilient**: Graceful handling of failures and timeouts

### Key Concepts

#### 1. Analysis Pipeline

The analysis pipeline follows these steps:

1. **Page Loading**: 
   - Initial page load and rendering
   - JavaScript execution
   - Resource loading (images, styles, scripts)

2. **Content Extraction**:
   - HTML structure analysis
   - CSS style computation
   - JavaScript execution context
   - Network request analysis

3. **Analysis Execution**:
   - Parallel analyzer execution
   - Result aggregation
   - Score calculation
   - Issue detection

4. **Result Processing**:
   - Data normalization
   - Cache storage
   - Report generation

#### 2. Analyzer Types

Analyzers are categorized by their focus:

1. **Technical Analyzers**:
   - Code quality
   - Performance metrics
   - Security vulnerabilities
   - Infrastructure assessment

2. **User Experience Analyzers**:
   - Accessibility compliance
   - Design system consistency
   - Interaction patterns
   - Content readability

3. **Business Analyzers**:
   - SEO optimization
   - Compliance requirements
   - Operational metrics
   - Content analysis

#### 3. Evaluation Modes

The engine supports multiple evaluation modes:

1. **Live Evaluation**:
   - Real-time analysis of live websites
   - WebSocket-based progress updates
   - Interactive result exploration

2. **Offline Evaluation**:
   - Analysis of local project files
   - Batch processing capabilities
   - Detailed reporting

3. **Continuous Evaluation**:
   - Automated periodic checks
   - Change detection
   - Trend analysis

#### 4. Scoring System

The scoring system is designed to be:

1. **Comprehensive**:
   - Multiple evaluation criteria
   - Weighted importance factors
   - Normalized scores (0-100)

2. **Transparent**:
   - Detailed scoring breakdown
   - Issue categorization
   - Actionable recommendations

3. **Customizable**:
   - Adjustable weights
   - Custom criteria
   - Industry-specific standards

### Best Practices

#### 1. Performance Optimization

1. **Resource Management**:
   - Browser instance pooling
   - Memory usage monitoring
   - Concurrent analysis limits

2. **Caching Strategy**:
   - Result caching
   - Resource caching
   - Cache invalidation rules

3. **Network Optimization**:
   - Request batching
   - Resource prioritization
   - Connection pooling

#### 2. Analysis Configuration

1. **Analyzer Selection**:
   - Choose relevant analyzers
   - Configure analysis depth
   - Set performance thresholds

2. **Custom Rules**:
   - Define custom criteria
   - Set industry standards
   - Configure severity levels

3. **Output Format**:
   - Select report format
   - Configure detail level
   - Set export options

#### 3. Integration Guidelines

1. **API Integration**:
   - RESTful endpoints
   - WebSocket connections
   - Authentication methods

2. **Data Flow**:
   - Input validation
   - Result processing
   - Error handling

3. **Security**:
   - Access control
   - Data protection
   - Rate limiting

### Advanced Features

#### 1. Custom Analyzers

The system supports custom analyzers through:

1. **Plugin System**:
   - Standardized interfaces
   - Configuration options
   - Result formatting

2. **Integration Points**:
   - Analysis hooks
   - Event listeners
   - Custom metrics

3. **Extension Methods**:
   - Custom rules
   - Specialized checks
   - Industry-specific analysis

#### 2. Analysis Extensions

Extend analysis capabilities with:

1. **Custom Metrics**:
   - Business-specific KPIs
   - Industry standards
   - Performance indicators

2. **Specialized Checks**:
   - Compliance requirements
   - Brand guidelines
   - Accessibility standards

3. **Integration Points**:
   - Third-party tools
   - External services
   - Custom validators

#### 3. Reporting System

Generate comprehensive reports with:

1. **Multiple Formats**:
   - JSON
   - HTML
   - PDF
   - CSV

2. **Custom Templates**:
   - Branded reports
   - Custom sections
   - Specific metrics

3. **Export Options**:
   - Scheduled exports
   - Automated delivery
   - Integration with tools

## Usage Examples

### Basic Page Evaluation
```python
from core.evaluators import PageEvaluator
from playwright.async_api import async_playwright

async def evaluate_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://example.com")
        
        evaluator = PageEvaluator(page)
        results = await evaluator.evaluate()
        
        print(f"Overall Score: {results['overall_score']}")
        print(f"Accessibility Score: {results['accessibility']['overall_score']}")
        print(f"Performance Score: {results['performance']['overall_score']}")
        
        await browser.close()

# Run the evaluation
import asyncio
asyncio.run(evaluate_page())
```

### Backend Implementation
```python
from fastapi import FastAPI, WebSocket
from core.evaluators import PageEvaluator
from core.services.websocket_service import WebSocketManager
from core.services.live_evaluation_service import LiveEvaluationService

app = FastAPI()
ws_manager = WebSocketManager()
evaluation_service = LiveEvaluationService(ws_manager)

@app.websocket("/ws/evaluate")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == "start_evaluation":
                await evaluation_service.start_evaluation(
                    url=data["url"],
                    client_id=websocket.client.id
                )
    except Exception as e:
        await ws_manager.disconnect(websocket)
```

### Offline Evaluation
```python
from core.evaluators import ProjectEvaluator
from pathlib import Path

def evaluate_project():
    project_path = Path("./my-project")
    evaluator = ProjectEvaluator(project_path)
    
    # Run specific analyzers
    results = evaluator.evaluate(
        analyzers=["accessibility", "performance", "security"]
    )
    
    # Save results
    evaluator.save_results(results, "analysis_results.json")
    
    # Get detailed report
    report = evaluator.generate_report(results)
    print(report)

# Run offline evaluation
evaluate_project()
```

## Analysis Results Structure

Each analyzer returns results in a consistent format:

```python
{
    "analyzer_name": {
        "overall_score": float,  # 0-100 score
        "details": {
            # Analyzer-specific details
        },
        "issues": [
            {
                "type": str,
                "message": str,
                "severity": str,
                "location": str
            }
        ],
        "recommendations": [
            {
                "title": str,
                "description": str,
                "priority": str
            }
        ],
        "metrics": {
            # Analyzer-specific metrics
        }
    }
}
```

## Configuration

The core engine can be configured through environment variables or a config file:

```python
from core.config import Settings

settings = Settings(
    CACHE_DIR="~/.uibench/cache",
    CACHE_TTL=3600,
    MAX_CONCURRENT_EVALUATIONS=5,
    ENABLED_ANALYZERS=["accessibility", "performance", "security"]
)
```

## Error Handling

The core engine includes comprehensive error handling:

```python
from core.exceptions import (
    EvaluationError,
    AnalyzerError,
    BrowserError,
    CacheError
)

try:
    results = await evaluator.evaluate()
except EvaluationError as e:
    print(f"Evaluation failed: {e}")
except AnalyzerError as e:
    print(f"Analyzer failed: {e}")
except BrowserError as e:
    print(f"Browser error: {e}")
except CacheError as e:
    print(f"Cache error: {e}")
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Browser Automation Issues

**Problem**: Playwright browser fails to launch or crashes
```python
# Error: Browser closed unexpectedly
# Error: Target page, context or browser has been closed
```

**Solutions**:
- Ensure Playwright browsers are installed:
  ```bash
  playwright install
  ```
- Check system resources (memory, CPU)
- Increase browser launch timeout:
  ```python
  browser = await p.chromium.launch(timeout=60000)  # 60 seconds
  ```
- Use headless mode for better stability:
  ```python
  browser = await p.chromium.launch(headless=True)
  ```

#### 2. Cache Issues

**Problem**: Cache operations fail or return stale data
```python
# Error: Cache directory not found
# Error: Cache file corrupted
```

**Solutions**:
- Clear cache directory:
  ```python
  from core.utils.cache import AnalysisCache
  cache = AnalysisCache()
  cache.clear()
  ```
- Verify cache permissions:
  ```bash
  chmod -R 755 ~/.uibench/cache
  ```
- Disable cache temporarily:
  ```python
  settings = Settings(CACHE_ENABLED=False)
  ```

#### 3. Analyzer Failures

**Problem**: Specific analyzers fail to complete
```python
# Error: Analyzer timeout
# Error: Missing required data
```

**Solutions**:
- Increase analyzer timeout:
  ```python
  settings = Settings(ANALYZER_TIMEOUT=300)  # 5 minutes
  ```
- Check analyzer dependencies:
  ```python
  # Verify required packages
  pip install -r requirements.txt
  ```
- Enable debug logging:
  ```python
  import logging
  logging.basicConfig(level=logging.DEBUG)
  ```

#### 4. Memory Issues

**Problem**: High memory usage or out of memory errors
```python
# Error: MemoryError
# Error: Process killed due to memory limit
```

**Solutions**:
- Reduce concurrent evaluations:
  ```python
  settings = Settings(MAX_CONCURRENT_EVALUATIONS=2)
  ```
- Enable garbage collection:
  ```python
  import gc
  gc.enable()
  ```
- Monitor memory usage:
  ```python
  from core.utils.monitoring import MemoryMonitor
  monitor = MemoryMonitor()
  monitor.start()
  ```

#### 5. Network Issues

**Problem**: Failed to fetch or analyze web pages
```python
# Error: Connection timeout
# Error: SSL certificate error
```

**Solutions**:
- Increase network timeout:
  ```python
  settings = Settings(NETWORK_TIMEOUT=30000)  # 30 seconds
  ```
- Configure proxy if needed:
  ```python
  browser = await p.chromium.launch(proxy={
      "server": "http://proxy.example.com:8080"
  })
  ```
- Disable SSL verification (not recommended for production):
  ```python
  browser = await p.chromium.launch(ignore_https_errors=True)
  ```

### Debugging Tools

#### 1. Enable Debug Logging
```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

#### 2. Use Debug Mode
```python
settings = Settings(DEBUG=True)
```

#### 3. Save Debug Information
```python
from core.utils.debug import DebugCollector

debug = DebugCollector()
try:
    results = await evaluator.evaluate()
except Exception as e:
    debug.save_error(e)
    debug.save_state(evaluator.get_state())
```

### Performance Optimization

#### 1. Resource Management
```python
# Limit concurrent operations
settings = Settings(
    MAX_CONCURRENT_EVALUATIONS=3,
    MAX_BROWSER_INSTANCES=2
)

# Configure memory limits
settings = Settings(
    MAX_MEMORY_USAGE="2GB",
    MEMORY_CLEANUP_THRESHOLD="1.5GB"
)
```

#### 2. Caching Strategy
```python
# Configure cache settings
settings = Settings(
    CACHE_TTL=3600,  # 1 hour
    CACHE_MAX_SIZE=1000,
    CACHE_CLEANUP_INTERVAL=3600
)
```

#### 3. Browser Pool Management
```python
# Configure browser pool
settings = Settings(
    BROWSER_POOL_SIZE=3,
    BROWSER_IDLE_TIMEOUT=300,  # 5 minutes
    BROWSER_RECYCLE_INTERVAL=3600  # 1 hour
)
```

### Getting Help

If you encounter issues not covered here:

1. if you have any questions ([![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/Alazar42/UIBench))
2. Open a new issue with:
   - Error message and stack trace
   - Steps to reproduce
   - System information
   - UIBench version

