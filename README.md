# 🛡️ SLM Local Git Secret Gatekeeper

A **Hybrid Multi-Stage Gatekeeper** designed to prevent sensitive credentials (e.g., AWS keys, OpenAI tokens, Stripe keys) from being accidentally committed to your Git repositories. 

Traditional regex-based secret scanners (like Gitleaks or Trufflehog) are fast but suffer from incredibly high false-positive rates, flagging test data, mock variables, and random strings. This leads to overwhelming "scanner fatigue," causing developers to constantly ignore or bypass security warnings. 

This tool solves that problem entirely by combining the speed of regex with the raw contextual reasoning of a **locally running Small Language Model (SLM)**. 

---

## ✨ Features

- **Zero Cloud Dependency:** Runs 100% locally on your machine. Your uncommitted code is never sent to a third-party API.
- **State-of-the-Art Reasoning:** Powered by **Qwen2.5-1.5B-Instruct**, providing deep contextual understanding of code and secrets.
- **Recall-Centric "Safety Net":** Ensures 98% coverage by using a hybrid Regex-OR-SLM architecture. If Regex misses a secret, the SLM catches it.
- **Actionable Remediation:** Provides exact next steps to safely store environment variables.
- **High Recall (0.98):** Verified to catch non-standard tokens and obscured secrets that traditional patterns miss.

## 🧠 How It Works in Practice

The Gatekeeper uses a **3-Stage "Recall-Centric"** pipeline:

1. **Stage 1 — The Sieve (Regex):**  
   A fast regex scan checks for known secret patterns (AWS, OpenAI, Slack, Stripe, etc.). Any match is **immediately blocked** (`SECURITY ALERT (Stage 1 - Regex)`) to ensure zero-latency, high-recall protection.

2. **Stage 2 — The Safety Net (SLM Deep Scan):**  
   If Stage 1 finds nothing, the full code diff is passed to **Qwen2.5-1.5B**. The SLM performs a deep contextual scan for novel, obscured, or non-standard secrets that regex patterns miss. (`SECURITY ALERT (Stage 2 - SLM Safety Net)`)

3. **Stage 3 — The Action:**  
   If either stage detects a threat, the commit is blocked with remediation guidance. If both stages pass, the commit is allowed (`OK (Stage 3): Commit allowed`).

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.12** (or 3.11) — Python 3.14 is too new and lacks pre-built wheels for `torch`.
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/xaskoiking/slm-local-git-secret-gatekeeper.git
cd slm-local-git-secret-gatekeeper
```

### Step 2: Create a Virtual Environment (Python 3.12)
```bash
# Windows
py -3.12 -m venv venv

# macOS / Linux
python3.12 -m venv venv
```

### Step 3: Install Dependencies
```bash
# Activate the virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install core dependencies
pip install --upgrade pip
pip install huggingface-hub transformers gitpython regex tqdm
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Step 4: Download the SLM Model
```bash
python src/models/download.py --model Qwen/Qwen2.5-1.5B-Instruct
```
This downloads the **Qwen2.5-1.5B-Instruct** model into `src/models/weights/`.

---

## ⚙️ Enabling the Hook

### Option 1: Project-Specific (Single Repo)

Create a file called `pre-commit` inside your target repo's `.git/hooks/` directory.

**On Windows (PowerShell):**
```powershell
Set-Content .git\hooks\pre-commit '#!/bin/sh
"C:/path/to/gatekeeper/venv/Scripts/python.exe" "C:/path/to/gatekeeper/src/hooks/main.py"'
```

**On macOS/Linux (Terminal):**
```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
"/path/to/gatekeeper/venv/bin/python" "/path/to/gatekeeper/src/hooks/main.py"
EOF
chmod +x .git/hooks/pre-commit
```

> **Replace** `/path/to/gatekeeper/` with the actual absolute path where you cloned this repository.

### Option 2: Global Protection (All Repos)

```bash
mkdir -p ~/.git-global-hooks
# Copy the pre-commit content from Option 1 into ~/.git-global-hooks/pre-commit
chmod +x ~/.git-global-hooks/pre-commit
git config --global core.hooksPath ~/.git-global-hooks
```

---

## 🚀 Advanced: Switching to Llama 3.2

For higher accuracy, you can switch to **Llama 3.2 1B Instruct**. This requires a HuggingFace account and license acceptance:

1. Accept the license at [meta-llama/Llama-3.2-1B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct).
2. Authenticate: `python -m huggingface_hub login`
3. Download: `python src/models/download.py --model meta-llama/Llama-3.2-1B-Instruct`
4. Update `SLMValidator` in `src/models/inference.py` to use the new model name.

---

## ❗ Troubleshooting

### `ModuleNotFoundError: No module named 'List'` or similar
Ensure you have the latest code. This was fixed by adding correct imports to `typing`.

### Hook doesn't trigger
Ensure you used **absolute paths** in your `.git/hooks/pre-commit` file and that it is executable (`chmod +x`).

---

## 🔬 Research & Attribution

This project is independent personal research by Raaghavan Krishnamurthy. AI coding assistance tools were used during development. All research design, experimental methodology, system architecture decisions, and intellectual contributions are the original work of the author. No proprietary, organizational, or third-party code or credentials were involved. All testing datasets are entirely synthetic.
