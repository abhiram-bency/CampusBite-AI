# CampusBite AI Backend
## 07_PYDANTIC_GUIDE.md

Version: 1.0

Status: Pydantic Development Guide

---

# Purpose

This document defines how **Pydantic v2** must be used throughout the CampusBite AI Backend.

Every request schema, response schema, validator, serialization rule, and model configuration must follow these standards.

The objective is to ensure all validation happens consistently at the API boundary and nowhere else.

---

# Pydantic Version

The project uses

```
Pydantic v2
```

Never generate code using Pydantic v1 syntax.

Avoid

```
validator

root_validator

parse_obj

dict()

from_orm
```

Use

```
field_validator

model_validator

model_dump()

model_validate()

ConfigDict
```

---

# Responsibility

Pydantic owns

- request validation
- response serialization
- type conversion
- normalization
- OpenAPI documentation

Pydantic does **not** own

- business logic
- authentication
- authorization
- SQL
- persistence
- API routing

---

# Schema Types

Every module should define three categories of schemas.

```
Request Schemas

↓

Response Schemas

↓

Internal Helper Schemas
```

---

# Request Schemas

Used only for incoming requests.

Example

```python
class LoginRequest(BaseModel):
    email: EmailStr
    password: SecretStr
```

Request schemas validate client input.

---

# Response Schemas

Used only for outgoing responses.

Example

```python
class VendorProfileResponse(BaseModel):
    ...
```

Never return ORM models directly.

---

# Internal Schemas

Used internally between modules.

Example

```
Token

TokenPayload

PaginationMetadata
```

---

# Schema Naming

Requests

```
LoginRequest

RegisterRequest

UpdateVendorRequest
```

Responses

```
LoginResponse

VendorProfileResponse

BookingResponse
```

Never use generic names like

```
Data

Info

Payload
```

---

# BaseModel

All schemas inherit

```python
BaseModel
```

No custom framework is required.

---

# Model Configuration

Always use

```python
ConfigDict
```

Example

```python
model_config = ConfigDict(
    from_attributes=True
)
```

Never use

```python
class Config:
```

---

# ORM Conversion

Use

```python
model_validate()
```

Example

```python
VendorProfileResponse.model_validate(
    vendor
)
```

Never use

```python
from_orm()
```

---

# Serialization

Use

```python
model_dump()
```

Example

```python
payload.model_dump()
```

Partial update

```python
payload.model_dump(
    exclude_unset=True
)
```

Never use

```python
dict()
```

---

# Secret Values

Passwords must use

```python
SecretStr
```

Example

```python
password: SecretStr
```

Access

```python
payload.password.get_secret_value()
```

Never store plaintext passwords.

---

# Email Fields

Always use

```python
EmailStr
```

Example

```python
email: EmailStr
```

---

# UUID Fields

Always use

```python
UUID
```

Never use strings for identifiers.

---

# Enum Fields

Use project enums.

Example

```python
role: UserRoleEnum
```

Never compare raw strings.

---

# DateTime Fields

Use

```python
datetime
```

Always store UTC.

---

# Field Metadata

Document fields.

Example

```python
phone_number: str = Field(
    ...,
    description="User phone number."
)
```

Use descriptions wherever they improve API documentation.

---

# Field Constraints

Prefer built-in constraints.

Example

```python
Field(
    min_length=1,
    max_length=100
)
```

---

# Regex Validation

Example

```python
Field(
    pattern=r"^\+?[0-9]{8,15}$"
)
```

Avoid manual regex checks inside services.

---

# Validators

Use

```python
field_validator()
```

Example

```python
@field_validator("email")
@classmethod
def normalize_email(
    cls,
    value: str,
) -> str:
    return value.lower()
```

---

# Model Validators

Use

```python
model_validator()
```

only when validation depends on multiple fields.

Example

```
password

confirm_password
```

---

# Normalization

Normalize values inside schemas.

Examples

- lowercase emails
- trim whitespace
- normalize phone numbers
- strip unnecessary spaces

Never duplicate normalization inside services.

---

# Default Values

Good

```python
token_type: str = "bearer"
```

Bad

```python
token_type: str
```

when always identical.

---

# Optional Fields

Use

```python
str | None
```

Example

```python
business_registration_no: str | None
```

---

# Partial Updates

PATCH schemas should make fields optional.

Example

```python
business_name: str | None = None
```

Services should use

```python
exclude_unset=True
```

---

# Nested Models

Use nested schemas instead of dictionaries.

Good

```python
class LoginResponse(BaseModel):
    access_token: str
    user: UserResponse
```

Bad

```python
user: dict
```

---

# Response Composition

Prefer composition.

Good

```
LoginResponse

↓

AuthenticatedUserResponse
```

Avoid duplicate fields across schemas.

---

# Schema Reuse

Extract reusable schemas.

Example

```
AuthenticatedUserResponse

↓

LoginResponse

↓

RegisterResponse
```

---

# Business Rules

Business rules never belong in validators.

Bad

```
email already exists

password already used

vendor already approved
```

These belong in services.

---

# Validation Errors

Pydantic should generate

```
422 Unprocessable Entity
```

automatically.

Never manually raise validation exceptions.

---

# Type Safety

Always use explicit types.

Good

```python
price: Decimal
```

Bad

```python
price
```

---

# Lists

Example

```python
list[BookingResponse]
```

Never use

```python
List
```

unless compatibility requires it.

---

# Dictionaries

Use explicit typing.

Example

```python
dict[str, str]
```

---

# Literal Types

Use

```python
Literal
```

only when enums are unnecessary.

Otherwise prefer project enums.

---

# Aliases

Avoid aliases unless integrating with external APIs.

Internal APIs should use consistent field names.

---

# Computed Fields

If computed values are needed

Use

```python
@computed_field
```

rather than manual property serialization.

---

# OpenAPI

Descriptions should make documentation readable.

Example

```python
Field(
    description="Vendor's business name."
)
```

Avoid excessive descriptions for obvious fields.

---

# File Uploads

Use

```python
UploadFile
```

not Pydantic schemas.

---

# AI Responses

Future AI endpoints should define dedicated schemas.

Example

```
ChatRequest

ChatResponse

RecommendationResponse
```

Never return raw LLM output.

---

# Testing

Every schema should be tested for

- valid input
- invalid input
- normalization
- serialization
- optional fields
- validators

---

# AI Development Rules

When generating schemas

Always

- use Pydantic v2
- use BaseModel
- use ConfigDict
- use model_validate()
- use model_dump()
- use field_validator()
- document important fields

Never

- use Pydantic v1 syntax
- put business logic into validators
- return ORM models
- duplicate validation inside services

---

# Example Request Schema

```python
class VendorProfileUpdateRequest(BaseModel):
    business_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    business_registration_no: str | None = Field(
        default=None,
        max_length=100,
    )
```

---

# Example Response Schema

```python
class VendorProfileResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: UUID
    full_name: str
    business_name: str
    email: str
```

---

# Golden Rules

1. Pydantic validates data—not business logic.

2. Use Pydantic v2 syntax only.

3. Normalize data inside schemas.

4. Services should trust validated schemas.

5. Always use response models.

6. Never expose ORM models directly.

7. Use SecretStr for passwords.

8. Use model_validate() and model_dump().

9. Keep request and response schemas separate.

10. Schemas should remain lightweight, reusable, and deterministic.

This document is the canonical Pydantic development guide for the CampusBite AI Backend.