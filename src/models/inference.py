from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os

class SLMValidator:
    def __init__(self, model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"):
        """Initialize the SLM with optional 4-bit optimization."""
        # Check for local weights first
        local_weights = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "weights")
        if os.path.exists(local_weights) and os.path.isdir(local_weights):
            model_name = local_weights
            print(f"INFO: Using local model weights from {local_weights}")

        # Optimize for CPU performance
        torch.set_num_threads(4) 
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Optimization: Attempt 4-bit loading if bitsandbytes is available
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name, 
                load_in_4bit=True, 
                device_map="auto"
            )
            print("INFO: Loaded model in 4-bit quantized mode.")
        except Exception:
            # Fallback to standard loading
            self.model = AutoModelForCausalLM.from_pretrained(model_name).to(self.device)
            print(f"INFO: Loaded model in standard mode on {self.device}.")
        
        self.model.eval() # Ensure model is in evaluation mode

    def scan_for_secrets(self, context: str) -> bool:
        """Deep scan a code block for any secrets missed by Stage 1."""
        messages = [
            {
                "role": "system", 
                "content": (
                    "You are a security auditor. Scan the following code for any sensitive secrets, "
                    "passwords, or API keys that should NOT be committed.\n"
                    "Respond ONLY with 'YES' if you find any leak, or 'NO' if the code is clean.\n"
                    "Ignore placeholders like 'YOUR_KEY_HERE' or 'EXAMPLE'."
                )
            },
            {"role": "user", "content": f"Does this code contain any genuine secrets?\nCODE:\n{context}"}
        ]
        
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_new_tokens=5)
        
        response = self.tokenizer.decode(outputs[0][len(inputs["input_ids"][0]):], skip_special_tokens=True)
        return "YES" in response.upper()

    def validate_candidate(self, candidate_string: str, context: str) -> bool:
        """Analyze a snippet and its context to determine if it's a genuine secret leak."""
        messages = [
            {
                "role": "system", 
                "content": (
                    "You are a security expert specialized in secret detection. "
                    "Analyze the code and respond ONLY with 'YES' or 'NO'.\n"
                    "- Respond NO if the string is a placeholder (e.g. 'YOUR_API_KEY_HERE', 'EXAMPLE_TOKEN'), "
                    "a test/mock variable, or obviously non-sensitive data.\n"
                    "- Respond YES if the string is a genuine, high-entropy production API key, "
                    "password, or secret intended for a live service."
                )
            },
            {"role": "user", "content": f"Is this a genuine production secret leak?\nSTRING: {candidate_string}\nCONTEXT: {context}"}
        ]
        
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_new_tokens=5)
        
        response = self.tokenizer.decode(outputs[0][len(inputs["input_ids"][0]):], skip_special_tokens=True)
        
        return "YES" in response.upper()

    def generate_remediation(self, candidate_string: str, context: str) -> str:
        """Stage 3: Generate dynamic remediation advice for a detected leak."""
        messages = [
            {"role": "system", "content": "You are a security expert. Provide a one-sentence instruction on how to remediate this detected secret leak."},
            {"role": "user", "content": f"A potential secret ('{candidate_string}') was found in this context: `{context}`. How should I fix this?"}
        ]
        
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_new_tokens=40)
        
        return self.tokenizer.decode(outputs[0][len(inputs["input_ids"][0]):], skip_special_tokens=True).strip()

def run_benchmarks():
    """Evaluate SLM validation performance."""
    print("Running benchmarks...")
    # Placeholder for benchmarking logic

if __name__ == "__main__":
    validator = SLMValidator()
    test_snippet = "sk-proj-4v56..." # OpenAI key-like
    is_leak = validator.validate_candidate(test_snippet)
    print(f"Candidate: {test_snippet} | Is Leak: {is_leak}")
