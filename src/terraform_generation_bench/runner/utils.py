"""Utility functions for the runner."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color


def log_info(message: str) -> None:
    """Log an info message."""
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {message}", file=sys.stderr)


def log_error(message: str) -> None:
    """Log an error message."""
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}", file=sys.stderr)


def log_warn(message: str) -> None:
    """Log a warning message."""
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {message}", file=sys.stderr)


def export_localstack_env() -> Dict[str, str]:
    """Export LocalStack AWS environment variables.
    
    Returns:
        Dictionary of environment variables to set.
    """
    env = {
        'AWS_ACCESS_KEY_ID': 'test',
        'AWS_SECRET_ACCESS_KEY': 'test',
        'AWS_DEFAULT_REGION': 'us-east-1',
        'AWS_REGION': 'us-east-1',
    }
    os.environ.update(env)
    log_info("Exported LocalStack AWS environment variables")
    return env


def check_localstack() -> bool:
    """Check if LocalStack is running.
    
    Returns:
        True if LocalStack is running, False otherwise.
    """
    try:
        import requests
        response = requests.get('http://localhost:4566/_localstack/health', timeout=5)
        if response.status_code == 200:
            log_info("LocalStack is running")
            return True
    except Exception:
        pass
    
    log_error("LocalStack is not running. Please start it with: docker compose up -d")
    return False


def load_spec(spec_file: Path) -> Dict[str, Any]:
    """Load task specification from YAML file.
    
    Args:
        spec_file: Path to the spec.yaml file.
        
    Returns:
        Dictionary containing the spec data.
    """
    with open(spec_file, 'r') as f:
        return yaml.safe_load(f)


def get_var(spec: Dict[str, Any], var_name: str) -> Any:
    """Get a variable value from spec.
    
    Args:
        spec: The loaded spec dictionary.
        var_name: Name of the variable to get.
        
    Returns:
        The variable value, or None if not found.
    """
    return spec.get('vars', {}).get(var_name)


def run_command(cmd: List[str], cwd: Optional[Path] = None, 
                capture_output: bool = True, 
                check: bool = True,
                timeout: Optional[int] = None) -> subprocess.CompletedProcess:
    """Run a shell command.
    
    Args:
        cmd: Command to run as a list of strings.
        cwd: Working directory for the command.
        capture_output: Whether to capture stdout/stderr.
        check: Whether to raise on non-zero exit code.
        timeout: Timeout in seconds (default: None for no timeout).
        
    Returns:
        CompletedProcess object.
    """
    env = os.environ.copy()
    export_localstack_env()
    env.update(os.environ)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            capture_output=capture_output,
            text=True,
            check=check,
            env=env,
            timeout=timeout
        )
        return result
    except subprocess.TimeoutExpired as e:
        log_error(f"Command timed out after {timeout}s: {' '.join(cmd)}")
        if capture_output and e.stdout:
            log_error(f"stdout (partial): {e.stdout}")
        if capture_output and e.stderr:
            log_error(f"stderr (partial): {e.stderr}")
        raise
    except subprocess.CalledProcessError as e:
        log_error(f"Command failed: {' '.join(cmd)}")
        if capture_output:
            log_error(f"stdout: {e.stdout}")
            log_error(f"stderr: {e.stderr}")
        raise

