from aiohttp import web

"""
[auth] > should return > {"enabled": true, "header_name": "X-API-Key", "api_keys": {...}}
[header_name] > should look in the key 'header_name' inside > return > str "X-API-Key"
[api_keys] > should look in the key 'api_keys' inside > return > dict {"<key>": "<client_name>"}
"""

class APIKeyValidator:

    def __init__(self, conf: dict):
        auth_conf = conf.get("auth", {})
        self.ENABLED = auth_conf.get("enabled", False)
        self.HEADER_NAME = auth_conf.get("header_name", "X-API-Key")
        self.API_KEYS = auth_conf.get("api_keys", {})

    def VALIDATE_KEY(self, key: str) -> str | None:
        if key is None:
            return None
        return self.API_KEYS.get(key)


def BUILD_AUTH_ERROR(message: str, status: int) -> web.Response:
    return web.json_response({"error": message}, status=status)