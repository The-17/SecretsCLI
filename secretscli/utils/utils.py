
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


def get_relative_time(timestamp_str: str) -> str:
    """
    Convert an ISO timestamp string to a human-readable relative time.
    e.g. "2023-01-01T12:00:00" -> "2 hours ago"
    """
    from datetime import datetime, timezone
    
    try:
        dt = datetime.fromisoformat(timestamp_str)
        now = datetime.now(timezone.utc)
        
        # Ensure dt is timezone-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
            
        diff = now - dt
        seconds = diff.total_seconds()
        
        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds < 604800: # 7 days
            days = int(seconds // 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            # For older dates, return formatted date
            return dt.strftime("%b %d, %Y")
            
    except Exception:
        return timestamp_str