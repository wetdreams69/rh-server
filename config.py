import os
import yaml

def ensure_assets_directory():
    os.makedirs("assets", exist_ok=True)

def load_configuration():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)