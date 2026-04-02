import os
import sys
import subprocess
import re
from typing import List, Dict, Tuple

# Ensure we can find the models package even when run from another repo
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

try:
    from models.inference import SLMValidator
except ImportError:
    # Use direct path if relative import fails in different contexts
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        from models.inference import SLMValidator
    except ImportError:
        SLMValidator = None

# Stage 1: Fast Regex Sifter
SECRET_PATTERNS = [
    r'(?:aws_access_key_id|aws_secret_access_key|aws_session_token|AKIA[0-9A-Z]{16})',
    r'sk-proj-[a-zA-Z0-9]{32,}', # OpenAI
    r'xoxb-[a-zA-Z0-9-]{12,}', # Slack
    r'ghp_[a-zA-Z0-9]{36}', # GitHub
    r'sk_live_[a-zA-Z0-9]{24}', # Stripe
    r'AIza[0-9A-Za-z-_]{35}', # Gemini / Google Cloud
    r'AZURE_[a-f0-9]{32}', # Azure
    r'goog-[a-z0-9]{40}', # Google Cloud Generic
    r'(?i)password\s*[:=]\s*["\'][^"\']+["\']',
    r'(?i)api[-_]key\s*[:=]\s*["\'][^"\']+["\']',
    r'(?i)secret\s*[:=]\s*["\'][^"\']+["\']',
]

def get_staged_diff() -> str:
    """Fetch the diff of staged files."""
    try:
        return subprocess.check_output(['git', 'diff', '--cached'], text=True)
    except subprocess.CalledProcessError:
        return ""

def fast_scan(diff_text: str) -> List[Dict[str, str]]:
    """Stage 1: Identify potential secrets using regex and capture context."""
    found_candidates = []
    lines = diff_text.splitlines()
    for line in lines:
        for pattern in SECRET_PATTERNS:
            matches = re.findall(pattern, line, re.IGNORECASE)
            if matches:
                for match in matches:
                    found_candidates.append({
                        "candidate": match,
                        "context": line.strip()
                    })
    return found_candidates

def slm_validation(context: str, mode: str = "validate") -> bool:
    """Stage 2 & 3: High-fidelity scanning or validation."""
    if not SLMValidator:
        return False

    try:
        validator = SLMValidator()
        if mode == "scan":
            # Deep scan of the entire context (Safety Net)
            print("INFO: Performing SLM Safety Net scan...")
            return validator.scan_for_secrets(context)
        else:
            # Placeholder for standard validation if needed later
            return False
    except Exception as e:
        print(f"ERROR: SLM Error: {e}. Falling back to safe mode.")
        return False

def main():
    diff_text = get_staged_diff()
    if not diff_text:
        sys.exit(0)

    # Stage 1: Fast Regex Sifter
    regex_candidates = fast_scan(diff_text)
    
    if regex_candidates:
        # PIVOT: Retain regex hits immediately to maximize Recall
        print("\nSECURITY ALERT (Stage 1 - Regex): Potential secrets detected!")
        for cand in regex_candidates:
            print(f"  - Possible secret found: {cand['candidate']}")
        print("\nACTION REQUIRED: Remove these secrets or use # gatekeeper:ignore")
        sys.exit(1)

    # Stage 2: SLM Safety Net (Only runs if Regex found nothing)
    # Perform a deep scan of the entire diff
    is_leak = slm_validation(diff_text, mode="scan")
    
    if is_leak:
        print("\nSECURITY ALERT (Stage 2 - SLM Safety Net): Potential secrets detected!")
        print("ACTION (Stage 3): Commit blocked. Review code for missed secrets (passwords, tokens, custom keys).")
        sys.exit(1)
    else:
        print("OK (Stage 3): No secrets detected by Regex or SLM Safety Net. Commit allowed.")
        sys.exit(0)

if __name__ == "__main__":
    main()
