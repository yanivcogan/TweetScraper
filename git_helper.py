import subprocess
from typing import Optional


def has_uncommitted_changes():
    """Check for uncommitted git changes in the current directory."""
    try:
        # Check if there are any staged but uncommitted changes
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            capture_output=True,
        )
        if result.returncode != 0:
            return True

        # Check if there are any unstaged changes
        result = subprocess.run(
            ["git", "diff", "--quiet"],
            capture_output=True,
        )
        if result.returncode != 0:
            return True

        # Check for untracked files
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
        )
        if result.stdout.strip():
            return True

        return False
    except FileNotFoundError:
        print("Git is not installed or not available in the PATH.")
        return True


def get_current_commit_id() -> Optional[str]:
    """Get the commit ID of the current HEAD."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("Error: Unable to retrieve the current commit ID. Is this a git repository?")
        return None
    except FileNotFoundError:
        print("Git is not installed or not available in the PATH.")
        return None
