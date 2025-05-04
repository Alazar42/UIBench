from typing import Dict, Any, List
from playwright.async_api import Page
import logging
import json

logger = logging.getLogger(__name__)

class ScreenReaderSimulator:
    @staticmethod
    async def simulate_screen_reader(page: Page) -> Dict[str, Any]:
        """
        Simulate a screen reader by extracting the accessibility tree and checking for accessible names/roles.
        """
        try:
            tree = await page.accessibility.snapshot(root=None, interesting_only=True)
            issues = []
            def traverse(node, path=None):
                if path is None:
                    path = []
                if node is None:
                    return
                role = node.get('role')
                name = node.get('name')
                if node.get('focused'):
                    path.append(f"[FOCUSED:{role}:{name}]")
                if role in ['button', 'link', 'textbox', 'checkbox', 'radio', 'combobox', 'menuitem', 'option', 'switch']:
                    if not name:
                        issues.append(f"Element with role '{role}' missing accessible name at path: {' > '.join(path)}")
                for child in node.get('children', []):
                    traverse(child, path + [f"{role}:{name}"])
            traverse(tree)
            return {
                "screen_reader_issues": issues,
                "tree": tree
            }
        except Exception as e:
            logger.error(f"Screen reader simulation failed: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    async def check_focus_order(page: Page) -> Dict[str, Any]:
        """
        Check the tab order and focus visibility by simulating Tab key presses.
        """
        try:
            focusable_selectors = [
                'a[href]', 'button', 'input', 'select', 'textarea', '[tabindex]:not([tabindex="-1"])'
            ]
            focusable = await page.query_selector_all(",".join(focusable_selectors))
            focus_order = []
            focus_issues = []
            prev_element = None
            for _ in range(len(focusable)):
                await page.keyboard.press("Tab")
                current_element = await page.evaluate_handle("document.activeElement")
                html = await current_element.evaluate('el => el.outerHTML')
                focus_order.append(html)
                # Check for visible focus
                outline = await current_element.evaluate('el => getComputedStyle(el).outline')
                if outline == "none":
                    focus_issues.append("Element missing visible focus outline: " + html)
                prev_element = current_element
            return {
                "focus_order": focus_order,
                "focus_issues": focus_issues
            }
        except Exception as e:
            logger.error(f"Focus order check failed: {str(e)}")
            return {"error": str(e)}
