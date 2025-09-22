import os
import sys
from pathlib import Path

def create_pgpass():
    """Create a .pgpass file for PostgreSQL authentication"""
    home = str(Path.home())
    pgpass_path = os.path.join(home, '.pgpass')
    
    print("Please enter your PostgreSQL password:")
    password = input().strip()
    
    # Write password file
    with open(pgpass_path, 'w') as f:
        f.write(f"localhost:5432:*:postgres:{password}")
    
    # Set correct permissions
    os.chmod(pgpass_path, 0o600)
    print(f"Created .pgpass file at {pgpass_path}")
    return password

if __name__ == "__main__":
    password = create_pgpass()