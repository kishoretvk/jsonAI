import os

def print_env_config():
    print("Active environment configuration:")
    print(f"APP_ENV: {os.getenv('APP_ENV', 'not set')}")
    print(f"OIDC_ISSUER: {os.getenv('OIDC_ISSUER', 'not set')}")
    print(f"OIDC_AUDIENCE: {os.getenv('OIDC_AUDIENCE', 'not set')}")
    print(f"OIDC_JWKS_URL: {os.getenv('OIDC_JWKS_URL', 'not set')}")
    print(f"OBS_ENABLE_METRICS: {os.getenv('OBS_ENABLE_METRICS', 'not set')}")
    print(f"OBS_ENABLE_TRACING: {os.getenv('OBS_ENABLE_TRACING', 'not set')}")
    print(f"OTEL_EXPORTER_OTLP_ENDPOINT: {os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'not set')}")
    print(f"OTEL_SERVICE_NAME: {os.getenv('OTEL_SERVICE_NAME', 'not set')}")
    print(f"OTEL_EXPORTER_OTLP_HEADERS: {os.getenv('OTEL_EXPORTER_OTLP_HEADERS', 'not set')}")

if __name__ == "__main__":
    print_env_config()
