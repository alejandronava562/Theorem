import os
from pathlib import Path
from functools import lru_cache
# Loads OpenAI API key from environment or local .env file (with caching)

# Reads key-value pairs from .env file into a dictionary
def _parse_env_file(env_path: Path) -> dict:
    data = {}
    try:
        lines = env_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return data

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


@lru_cache(maxsize=1)
# Returns OpenAI API key (checks env first, then .env file, caches result)
def get_openai_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key

    env_path = Path(__file__).resolve().parent / ".env"
    env_data = _parse_env_file(env_path)
    api_key = env_data.get("OPENAI_API_KEY")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        return api_key

    raise EnvironmentError("OPENAI_API_KEY environment variable is not set")
