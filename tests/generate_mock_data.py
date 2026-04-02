import json
import random
import os

def generate_mock_data(count=10000):
    data = []
    formats = {
        "AWS": ("AKIA", 16, "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
        "OpenAI": ("sk-proj-", 32, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
        "Slack": ("xoxb-", 24, "0123456789abcdefghijklmnopqrstuvwxyz"),
        "GitHub": ("ghp_", 36, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
        "Stripe": ("sk_live_", 24, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"),
        "Gemini": ("AIza", 35, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"),
        "Azure": ("AZURE_", 32, "abcdef0123456789"),
        "GoogleCloud": ("goog-", 40, "abcdefghijklmnopqrstuvwxyz0123456789"),
        "GenericSecret": ("", 32, "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    }

    print(f"Generating {count} mock secrets...")
    for i in range(count):
        is_leak = random.choice([True, False])
        source, (prefix, length, charset) = random.choice(list(formats.items()))
        key = prefix + ''.join(random.choice(charset) for _ in range(length))
        
        if is_leak:
            context = random.choice([
                f"export {source}_KEY='{key}'",
                f"config['{source.lower()}_api_key'] = '{key}'",
                f"const client = new {source}Client('{key}');",
                f"password: \"{key}\",",
                f"token = \"{key}\"",
                f"SECRET_KEY = '{key}'",
                f"db.connect('protocol://user:{key}@host:port/db')"
            ])
            label = "LEAK"
        else:
            # Common False Positives for Regex
            context = random.choice([
                f"# Example {source} key: {key}",
                f"test_{source.lower()}_key = '{key}' # mock for unittest",
                f"API_KEY = 'YOUR_{source}_KEY_HERE'",
                f"// TODO: replace with real {source} key {key}",
                f"if (apiKey === '{key}') {{ console.log('Mock login'); }}",
                f"const version = '{key}'; // Hash of build",
                f"let uuid = '{key}'; // Randomized session ID"
            ])
            label = "SAFE"

        data.append({
            "id": f"s_{i}",
            "snippet": context,
            "label": label,
            "type": source
        })

    os.makedirs("data/synthetic", exist_ok=True)
    with open("data/synthetic/mock_dataset.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"Successfully saved {count} samples to data/synthetic/mock_dataset.json")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate mock secret data.")
    parser.add_argument("--count", type=int, default=1000, help="Number of samples to generate")
    args = parser.parse_args()
    generate_mock_data(args.count)
