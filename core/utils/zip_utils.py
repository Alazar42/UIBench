import zipfile
import tempfile
import shutil
from pathlib import Path
from typing import Optional

async def safe_extract_zip(zip_path: str, dest_dir: str) -> Path:
    """Safely extract ZIP with multiple layers of protection"""
    dest = Path(dest_dir).resolve()
    temp_dir = Path(tempfile.mkdtemp())
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for member in zf.infolist():
                member_path = Path(member.filename)
                if member_path.is_absolute() or ".." in member_path.parts:
                    raise ValueError(f"Invalid path in ZIP: {member.filename}")
                
                extract_path = temp_dir / member_path
                if not extract_path.resolve().is_relative_to(temp_dir):
                    raise ValueError(f"Path traversal attempt: {member.filename}")
                
                zf.extract(member, temp_dir)
        
        # Move contents to final destination
        final_dir = dest / Path(zip_path).stem
        shutil.move(temp_dir, final_dir)
        return final_dir
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir) 