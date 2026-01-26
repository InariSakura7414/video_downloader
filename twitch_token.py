import json

TOKEN_PATH = "twitch_token.json"

def load_token():
    with open(TOKEN_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_token(data):
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def update_token_field(key, value):
    data = load_token()
    data[key] = value
    save_token(data)

token = load_token()
