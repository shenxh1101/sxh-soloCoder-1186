import os
import zipfile
import io
from typing import Dict, List, Optional

def create_zip_from_directory(source_dir: str, output_path: Optional[str] = None) -> bytes:
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zf.write(file_path, arcname)
    
    zip_bytes = zip_buffer.getvalue()
    
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(zip_bytes)
    
    return zip_bytes

def create_zip_from_multiple_directories(dirs: Dict[str, str], output_path: Optional[str] = None) -> bytes:
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for zip_folder, source_dir in dirs.items():
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, source_dir)
                    arcname = os.path.join(zip_folder, rel_path)
                    zf.write(file_path, arcname)
    
    zip_bytes = zip_buffer.getvalue()
    
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(zip_bytes)
    
    return zip_bytes

def create_zip_from_files(files: Dict[str, str], output_path: Optional[str] = None) -> bytes:
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for arcname, file_path in files.items():
            if os.path.exists(file_path):
                zf.write(file_path, arcname)
    
    zip_bytes = zip_buffer.getvalue()
    
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(zip_bytes)
    
    return zip_bytes
