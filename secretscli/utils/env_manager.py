"""
ENV File Manager

Handles reading and writing to .env and .env.example files.
Updates individual keys without clearing existing content.

HOW IT WORKS:

1. PARSE: Read the .env file and convert it into a Python dictionary
   - "API_KEY=sk_123" becomes {"API_KEY": "sk_123"}
   
2. UPDATE: Merge new secrets into the existing dictionary
   - If key exists: updates the value
   - If key is new: adds it to the dictionary
   
3. WRITE: Convert the dictionary back to text and save
   - {"API_KEY": "sk_123"} becomes "API_KEY=sk_123"

"""

from pathlib import Path
from typing import Dict, List, Optional, Union


class EnvManager:
    """
    Manages .env and .env.example file operations.
    
    The .env file contains KEY=VALUE pairs with real secrets.
    The .env.example file contains just KEYs (for documentation/templates).
    
    Usage:
        env = EnvManager()  # Uses .env and .env.example in current directory
        
        # Write secrets (handles one or many)
        env.write({"API_KEY": "sk_123", "DB_URL": "postgres://..."})
        
        # Read secrets
        all_secrets = env.read()
        
        # Delete a secret
        env.delete("OLD_KEY")
    """
    
    def __init__(self, directory: Optional[str] = None):
        """
        Initialize the EnvManager.
        
        Args:
            directory: Path to the directory containing .env files.
                       Defaults to current working directory (where the user runs the command).
        
        EXPLANATION:
        We store paths to both files. Using Path.cwd() means "current working directory"
        - this is where the user is when they run a command, not where our code lives.
        """
        base_dir = Path(directory) if directory else Path.cwd()
        self.env_path = base_dir / ".env"
        self.env_example_path = base_dir / ".env.example"
    
    def _parse_env_file_(self, file_path: Path) -> Dict[str, str]:
        """
        Read a .env file and convert it to a dictionary.
        
        Args:
            file_path: Path to the .env file to parse
            
        Returns:
            Dictionary of {KEY: VALUE} pairs
        
        EXPLANATION:
        A .env file looks like this:
            # This is a comment
            API_KEY=sk_live_123
            DB_URL="postgres://localhost/mydb"
            EMPTY_VALUE=
        
        This function:
        1. Reads all the text from the file
        2. Splits it into lines
        3. For each line:
           - Skip if empty or starts with # (comment)
           - Split on the first = sign (KEY=VALUE)
           - Strip whitespace and quotes from the value
           - Add to our dictionary
        """
        # If file doesn't exist, return empty dictionary
        if not file_path.exists():
            return {}
        
        secrets = {}
        content = file_path.read_text()
        
        for line in content.splitlines():
            line = line.strip()
            
            # Skip empty lines and comments (lines starting with #)
            if not line or line.startswith("#"):
                continue
            
            if "=" in line:
                key, value = line.split("=", 1)
                
                key = key.strip()
                value = value.strip()
                
                # Remove surrounding quotes if present
                if len(value) >= 2:
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]  # Remove first and last character
                
                secrets[key] = value
        
        return secrets
    
    def _write_env_file_(self, file_path: Path, secrets: Dict[str, str], keys_only: bool = False) -> None:
        """
        Write secrets to a .env file.
        
        Args:
            file_path: Path to write to
            secrets: Dictionary of {KEY: VALUE} pairs
            keys_only: If True, write only keys (for .env.example)
        
        EXPLANATION:
        This does the reverse of _parse_env_file_.
        
        For .env file (keys_only=False):
            {"API_KEY": "sk_123"} -> "API_KEY=sk_123\n"
            
        For .env.example file (keys_only=True):
            {"API_KEY": "sk_123"} -> "API_KEY=\n"
            (We only write the key so people know what variables are needed,
             but we don't expose the actual secret values)
        """
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Build the file content
        lines = []
        for key, value in secrets.items():
            if keys_only:
                # .env.example: just the key with empty value
                lines.append(f"{key}=")
            else:
                # .env: full KEY=VALUE
                lines.append(f"{key}={value}")
        
        # Join all lines with newlines
        content = "\n".join(lines)
        
        # Add trailing newline
        if content:
            content += "\n"
        
        file_path.write_text(content)
    
    def read(self) -> Dict[str, str]:
        """
        Read all secrets from .env file.
        
        Returns:
            Dictionary of all {KEY: VALUE} pairs
        """
        return self._parse_env_file_(self.env_path)
    
    def write(self, secrets: Dict[str, str]) -> None:
        """
        Write secrets to both .env and .env.example files.
        
        This is the main method you'll use. It:
        1. Reads existing secrets from .env
        2. Merges in the new secrets (updates existing, adds new)
        3. Writes back to .env (with values)
        4. Writes back to .env.example (keys only, for documentation)
        
        Args:
            secrets: Can be either:
                     - Dict: {"KEY": "VALUE", "KEY2": "VALUE2"}
                     - List of dicts: [{"key": "KEY", "value": "VALUE"}, ...]
                       (this is the API bulk format)
        """
        # Convert list format to dict if needed
        if isinstance(secrets, list):
            secrets = {item["key"]: item["value"] for item in secrets}
        
        # Step 1: Read existing secrets (parse)
        existing_secrets = self._parse_env_file_(self.env_path)
        
        # Step 2: Merge new secrets into existing (update)
        existing_secrets.update(secrets)
        
        # Step 3: Write to .env (with values)
        self._write_env_file_(self.env_path, existing_secrets, keys_only=False)
        
        # Step 4: Write to .env.example (keys only)
        self._write_env_file_(self.env_example_path, existing_secrets, keys_only=True)
    
    def delete(self, key: str) -> bool:
        """
        Delete a secret from both .env and .env.example.
        
        Args:
            key: The key to delete
            
        Returns:
            True if deleted, False if key didn't exist
        """
        existing_secrets = self._parse_env_file_(self.env_path)
        
        if key in existing_secrets:
            del existing_secrets[key]
            self._write_env_file_(self.env_path, existing_secrets, keys_only=False)
            self._write_env_file_(self.env_example_path, existing_secrets, keys_only=True)
            return True
        
        return False
    
    def exists(self) -> bool:
        """Check if .env file exists."""
        return self.env_path.exists()
    
    def create_if_missing(self) -> bool:
        """
        Create empty .env and .env.example if they don't exist.
        
        Returns:
            True if created, False if already existed
        """
        created = False
        
        for path in [self.env_path, self.env_example_path]:
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# Add your secrets here\n")
                created = True
        
        return created

env = EnvManager()