
from pathlib import Path
import json, os, sys

def _create_json_file_(file_path: Path, data: json, secure: bool) -> bool:

    """
    Helper function to create a JSON file.
    
    Args:
        file_path: Path to the file to create
        data: Dictionary data to write
        secure: If True, set restrictive permissions (0600) for sensitive files
    
    Returns:
        True if file was newly created, False if it already existed
    """

    try:
        if file_path.exists():
            return False
        
        file_path.write_text(json.dumps(data, indent=2))

        # Set restrictive permissions for sensitive files (Unix-like systems only)
        if secure and os.name != "nt":
            # Read/write for owner only
            os.chmod(file_path, 0o600)
            
        print(f"Created {file_path.name} at {file_path}")
        return True
    
    except PermissionError:
        print(f"Error: Permission denied when creating {file_path}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"Error: Failed to create {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


