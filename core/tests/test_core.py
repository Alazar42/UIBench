
import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

from core.evaluators.website_evaluator import WebsiteEvaluator
from core.utils.error_handler import handle_evaluation_error

async def evaluate_website(url: str):
    """
    Evaluate a website using the core functionality.
    
    Args:
        url: The URL of the website to evaluate
    """
    try:
        print(f"\nEvaluating website: {url}")
        print("=" * 50)
        
        # Create evaluator instance
        evaluator = WebsiteEvaluator(
            root_url=url,
            max_subpages=5,  # Limit to 5 subpages for testing
            max_depth=2      # Limit depth to 2 for testing
        )
        
        # Run evaluation
        print("\nStarting evaluation...")
        results = await evaluator.evaluate(crawl=True)
        
        # Print results
        print("\nEvaluation Results:")
        print("-" * 30)
        
        # Print overall scores
        print("\nOverall Scores:")
        for category, score in results.get("aggregated_scores", {}).items():
            print(f"{category}: {score:.2f}")
        
        # Print critical issues
        print("\nCritical Issues:")
        for issue in results.get("defect_details", {}).get("critical", []):
            print(f"- {issue}")
        
        # Print recommendations
        print("\nRecommendations:")
        for rec in results.get("recommendations", []):
            print(f"- {rec}")
        
        return results
        
    except Exception as e:
        error_response = handle_evaluation_error(e)
        print("\nError during evaluation:")
        print(f"Message: {error_response['message']}")
        if error_response.get('details'):
            print("Details:", error_response['details'])
        return None

async def main():
    # Use Cursor website URL
    url = "https://www.cursor.com/"
    await evaluate_website(url)

if __name__ == "__main__":
    asyncio.run(main()) 