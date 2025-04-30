import sys
import os

module_path = r"C:\Users\alaza\Documents\PythonProjects\UIBench"
sys.path.append(module_path)
from core.evaluators.website_evaluator import WebsiteEvaluator

import asyncio

# Initialize with website URL
evaluator = WebsiteEvaluator(
    root_url="https://example.com",
    max_subpages=100,  # Optional limit
    max_depth=3,       # Optional depth limit
    concurrency=5,     # Optional concurrency limit
    custom_criteria={} # Optional custom criteria
)

async def main():
    # Run evaluation
    results = await evaluator.evaluate(crawl=True)
    print(results)

# Run the async function
asyncio.run(main())