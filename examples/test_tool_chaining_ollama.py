from jsonAI.main import Jsonformer
from jsonAI.tool_registry import ToolRegistry
from jsonAI.model_backends import OllamaBackend
import os

def get_user(user_id):
    # Simulate user lookup (for fallback)
    users = {1: {"id": 1, "name": "Alice"}, 2: {"id": 2, "name": "Bob"}}
    return users.get(user_id, {"id": user_id, "name": "Unknown"})

def get_profile(user_id):
    # Simulate profile lookup (for fallback)
    profiles = {1: {"bio": "Engineer", "age": 30}, 2: {"bio": "Designer", "age": 25}}
    return profiles.get(user_id, {"bio": "N/A", "age": 0})

def test_compositional_tool_chaining_ollama():
    registry = ToolRegistry()
    registry.register(get_user)
    registry.register(get_profile)

    # Use OllamaBackend (ensure Ollama is running and accessible)
    backend = OllamaBackend(model_name=os.environ.get("OLLAMA_MODEL", "qwen3:0.6b"))

    user_ids = [1, 2]
    combined = []
    for uid in user_ids:
        print(f"[OLLAMA CALL] Requesting user info for user_id={uid}")
        jf_user = Jsonformer(
            model_backend=backend,
            json_schema={
                "type": "object",
                "properties": {"id": {"type": "integer"}, "name": {"type": "string"}},
                "x-jsonai-tool-call": {
                    "name": "get_user",
                    "arguments": {"user_id": "id"}
                }
            },
            prompt=f"Get user info for user {uid}.",
            tool_registry=registry,
            debug=True
        )
        jf_user.value = {"id": uid}
        user_result = jf_user._execute_tool_call(jf_user.value)
        print(f"[OLLAMA RESPONSE] User tool call for user_id={uid}: {user_result}")
        user_info = user_result["tool_result"]

        print(f"[OLLAMA CALL] Requesting profile info for user_id={uid}")
        jf_profile = Jsonformer(
            model_backend=backend,
            json_schema={
                "type": "object",
                "properties": {"bio": {"type": "string"}, "age": {"type": "integer"}},
                "x-jsonai-tool-call": {
                    "name": "get_profile",
                    "arguments": {"user_id": "id"}
                }
            },
            prompt=f"Get profile for user {uid}.",
            tool_registry=registry,
            debug=True
        )
        jf_profile.value = {"id": uid}
        profile_result = jf_profile._execute_tool_call(jf_profile.value)
        print(f"[OLLAMA RESPONSE] Profile tool call for user_id={uid}: {profile_result}")
        profile_info = profile_result["tool_result"]

        combined.append({"user": user_info, "profile": profile_info})

    final = {"users": combined}
    print("[OLLAMA DEBUG] Final composed result:", final)
    for idx, entry in enumerate(combined):
        print(f"[OLLAMA DEBUG] User {idx+1}:", entry["user"])
        print(f"[OLLAMA DEBUG] Profile {idx+1}:", entry["profile"])
    print("Compositional tool chaining test (Ollama) completed.")

if __name__ == "__main__":
    test_compositional_tool_chaining_ollama()
