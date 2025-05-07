from deepdiff import DeepDiff
from typing import Any, Dict, List

def compute_diffs(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, List[str]]:
    """Enhanced diff computation with path normalization"""
    diff = DeepDiff(
        old, 
        new,
        ignore_order=True,
        exclude_paths=["root['timestamp']"],
        view='tree'
    )
    
    def format_path(path) -> str:
        return '.'.join([str(p) for p in path if isinstance(p, str)])
    
    return {
        "added": [format_path(item.path) for item in diff.get('iterable_item_added', [])],
        "removed": [format_path(item.path) for item in diff.get('iterable_item_removed', [])],
        "changed": [format_path(item.path) for item in diff.get('values_changed', [])]
    } 