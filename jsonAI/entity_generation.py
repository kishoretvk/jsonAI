from typing import Any, Dict, Callable, Optional
import random
import string

class BaseEntityGenerationConfig:
    """Base class for entity generation configuration."""
    name: str = ""
    description: str = ""

    def generate(self) -> Any:
        raise NotImplementedError("generate() must be implemented by subclasses.")

class EntityGenerationRegistry:
    """Registry for entity generation configs."""
    _configs: Dict[str, BaseEntityGenerationConfig] = {}

    @classmethod
    def register(cls, config: BaseEntityGenerationConfig):
        cls._configs[config.name] = config

    @classmethod
    def get(cls, name: str) -> Optional[BaseEntityGenerationConfig]:
        return cls._configs.get(name)

    @classmethod
    def all_configs(cls):
        return list(cls._configs.keys())

# Example: Email generation config
class EmailGenerationConfig(BaseEntityGenerationConfig):
    name = "email"
    description = "Generates random but valid email addresses."

    def generate(self) -> str:
        user = ''.join(random.choices(string.ascii_lowercase, k=8))
        domain = ''.join(random.choices(string.ascii_lowercase, k=5))
        tld = random.choice(["com", "org", "net", "io"])
        return f"{user}@{domain}.{tld}"

# Register the example config
EntityGenerationRegistry.register(EmailGenerationConfig())

# US Social Security Number (SSN) generation config
class SSNGenerationConfig(BaseEntityGenerationConfig):
    name = "ssn"
    description = "Generates random US Social Security Numbers (format: XXX-XX-XXXX)."

    def generate(self) -> str:
        area = random.randint(100, 899)
        group = random.randint(10, 99)
        serial = random.randint(1000, 9999)
        return f"{area:03d}-{group:02d}-{serial:04d}"

# Passport number generation config (generic, 6-9 alphanumeric)
class PassportGenerationConfig(BaseEntityGenerationConfig):
    name = "passport"
    description = "Generates random passport numbers (6-9 alphanumeric characters)."

    def generate(self) -> str:
        length = random.randint(6, 9)
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# US Tax ID (EIN) generation config (format: XX-XXXXXXX)
class TaxIDGenerationConfig(BaseEntityGenerationConfig):
    name = "tax_id"
    description = "Generates random US Employer Identification Numbers (EIN, format: XX-XXXXXXX)."

    def generate(self) -> str:
        prefix = random.randint(10, 99)
        suffix = random.randint(1000000, 9999999)
        return f"{prefix:02d}-{suffix:07d}"

EntityGenerationRegistry.register(SSNGenerationConfig())
EntityGenerationRegistry.register(PassportGenerationConfig())
EntityGenerationRegistry.register(TaxIDGenerationConfig())

class EntityGenerationController:
    """
    Controls entity generation with user overrides, validation, and max attempts.
    """
    def __init__(
        self,
        registry: EntityGenerationRegistry,
        validation_registry: Optional[Any] = None,
        user_overrides: Optional[Dict[str, BaseEntityGenerationConfig]] = None,
        skip_validation: bool = False,
        max_attempts: int = 5,
    ):
        self.registry = registry
        self.validation_registry = validation_registry
        self.user_overrides = user_overrides or {}
        self.skip_validation = skip_validation
        self.max_attempts = max_attempts

    def generate(self, entity_type: str) -> Any:
        config = self.user_overrides.get(entity_type) or self.registry.get(entity_type)
        if not config:
            raise ValueError(f"No generation config found for entity type: {entity_type}")
        for attempt in range(self.max_attempts):
            value = config.generate()
            if self.skip_validation or not self.validation_registry:
                return value
            rule = self.validation_registry.get(entity_type)
            if not rule or rule.validate(value):
                return value
        raise ValueError(f"Failed to generate valid value for {entity_type} after {self.max_attempts} attempts.")
