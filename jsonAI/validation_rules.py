from typing import Any, Dict, Callable, Optional, List
import re

class BaseValidationRule:
    """Abstract base class for all validation rules."""
    name: str = ""
    description: str = ""
    example: str = ""

    def validate(self, value: Any) -> bool:
        raise NotImplementedError("validate() must be implemented by subclasses.")

class ValidationRuleRegistry:
    """Registry for validation rules."""
    _rules: Dict[str, BaseValidationRule] = {}

    @classmethod
    def register(cls, rule: BaseValidationRule):
        cls._rules[rule.name] = rule

    @classmethod
    def get(cls, name: str) -> Optional[BaseValidationRule]:
        return cls._rules.get(name)

    @classmethod
    def all_rules(cls) -> List[str]:
        return list(cls._rules.keys())

# Example: Email validation rule
class EmailRule(BaseValidationRule):
    name = "email"
    description = "Validates email addresses (basic RFC 5322)."
    example = "user@example.com"
    _regex = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        return bool(self._regex.match(value))

# Phone number validation rule (E.164 format)
class PhoneNumberRule(BaseValidationRule):
    name = "phone"
    description = "Validates phone numbers (E.164 format, e.g., +1234567890)."
    example = "+14155552671"
    _regex = re.compile(r"^\+\d{10,15}$")

    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        return bool(self._regex.match(value))

# Credit card number validation rule (Luhn algorithm)
class CreditCardRule(BaseValidationRule):
    name = "credit_card"
    description = "Validates credit card numbers using the Luhn algorithm."
    example = "4111111111111111"

    def validate(self, value: Any) -> bool:
        if not isinstance(value, str) or not value.isdigit():
            return False
        digits = [int(d) for d in value]
        checksum = 0
        parity = len(digits) % 2
        for i, digit in enumerate(digits):
            if i % 2 == parity:
                digit *= 2
                if digit > 9:
                    digit -= 9
            checksum += digit
        return checksum % 10 == 0

# Country code validation rule (ISO 3166-1 alpha-2)
class CountryCodeRule(BaseValidationRule):
    name = "country"
    description = "Validates ISO 3166-1 alpha-2 country codes."
    example = "US"
    _codes = {
        "US", "CA", "GB", "FR", "DE", "IN", "CN", "JP", "BR", "RU", "AU", "ZA", "IT", "ES", "MX", "KR", "TR", "NL", "SE", "CH"
        # ...add more as needed
    }

    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        return value.upper() in self._codes

# ZIP code validation rule (US ZIP, 5 or 9 digits)
class ZipCodeRule(BaseValidationRule):
    name = "zip"
    description = "Validates US ZIP codes (5 or 9 digits)."
    example = "12345"
    _regex = re.compile(r"^\d{5}(-\d{4})?$")

    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        return bool(self._regex.match(value))

# URL validation rule (basic HTTP/HTTPS)
class URLRule(BaseValidationRule):
    name = "url"
    description = "Validates HTTP/HTTPS URLs."
    example = "https://example.com"
    _regex = re.compile(r"^https?://[^\s/$.?#].[^\s]*$")

    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        return bool(self._regex.match(value))

# UUID validation rule (versions 1-5)
class UUIDRule(BaseValidationRule):
    name = "uuid"
    description = "Validates UUIDs (versions 1-5)."
    example = "123e4567-e89b-12d3-a456-426614174000"
    _regex = re.compile(
        r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
    )

    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        return bool(self._regex.match(value))

# Register the example rule
ValidationRuleRegistry.register(EmailRule())
ValidationRuleRegistry.register(PhoneNumberRule())
ValidationRuleRegistry.register(CreditCardRule())
ValidationRuleRegistry.register(CountryCodeRule())
ValidationRuleRegistry.register(ZipCodeRule())
ValidationRuleRegistry.register(URLRule())
ValidationRuleRegistry.register(UUIDRule())

# US Social Security Number (SSN) validation rule
class SSNRule(BaseValidationRule):
    name = "ssn"
    description = "Validates US Social Security Numbers (SSN, format: XXX-XX-XXXX)."
    example = "123-45-6789"
    _regex = re.compile(r"^\d{3}-\d{2}-\d{4}$")

    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        return bool(self._regex.match(value))

# Passport number validation rule (generic, 6-9 alphanumeric)
class PassportRule(BaseValidationRule):
    name = "passport"
    description = "Validates passport numbers (6-9 alphanumeric characters)."
    example = "A1234567"
    _regex = re.compile(r"^[A-Za-z0-9]{6,9}$")

    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        return bool(self._regex.match(value))

# US Tax ID validation rule (EIN, format: XX-XXXXXXX)
class TaxIDRule(BaseValidationRule):
    name = "tax_id"
    description = "Validates US Employer Identification Numbers (EIN, format: XX-XXXXXXX)."
    example = "12-3456789"
    _regex = re.compile(r"^\d{2}-\d{7}$")

    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        return bool(self._regex.match(value))

ValidationRuleRegistry.register(SSNRule())
ValidationRuleRegistry.register(PassportRule())
ValidationRuleRegistry.register(TaxIDRule())
