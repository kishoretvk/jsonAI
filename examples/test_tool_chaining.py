from jsonAI.main import Jsonformer
from jsonAI.tool_registry import ToolRegistry

def get_user(user_id):
    # Simulate user lookup
    users = {1: {"id": 1, "name": "Alice"}, 2: {"id": 2, "name": "Bob"}}
    return users.get(user_id, {"id": user_id, "name": "Unknown"})

def get_profile(user_id):
    # Simulate profile lookup
    profiles = {1: {"bio": "Engineer", "age": 30}, 2: {"bio": "Designer", "age": 25}}
    return profiles.get(user_id, {"bio": "N/A", "age": 0})

def test_compositional_tool_chaining():
    registry = ToolRegistry()
    registry.register(get_user)
    registry.register(get_profile)

    # Step 1: Use a fixed value for user_ids (simulate deterministic generation)
    user_ids = [1, 2]

    # Step 2: For each user ID, get user and profile, then combine
    combined = []
    from jsonAI.model_backends import DummyBackend
    for uid in user_ids:
        jf_user = Jsonformer(
            model_backend=DummyBackend(),
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
            debug=False
        )
        jf_user.value = {"id": uid}
        user_info = jf_user._execute_tool_call(jf_user.value)["tool_result"]

        jf_profile = Jsonformer(
            model_backend=DummyBackend(),
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
            debug=False
        )
        jf_profile.value = {"id": uid}
        profile_info = jf_profile._execute_tool_call(jf_profile.value)["tool_result"]

        combined.append({"user": user_info, "profile": profile_info})

    # Step 3: Compose final output
    final = {"users": combined}
    print("[DEBUG] Final composed result:", final)
    for idx, entry in enumerate(combined):
        print(f"[DEBUG] User {idx+1}:", entry["user"])
        print(f"[DEBUG] Profile {idx+1}:", entry["profile"])
    assert final == {
        "users": [
            {"user": {"id": 1, "name": "Alice"}, "profile": {"bio": "Engineer", "age": 30}},
            {"user": {"id": 2, "name": "Bob"}, "profile": {"bio": "Designer", "age": 25}}
        ]
    }
    print("Compositional tool chaining test passed.")

if __name__ == "__main__":
    test_compositional_tool_chaining()
