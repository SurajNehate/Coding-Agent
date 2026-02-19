# Guardrails Implementation

## Overview

The `guardrails.py` middleware provides **custom input validation and output sanitization** using regex patterns, **without requiring the guardrails-ai library**.

## Why No guardrails-ai?

The current implementation uses a **lightweight, custom approach** instead of the full guardrails-ai library because:

1. **Simpler** - No external dependencies needed
2. **Faster** - Regex-based validation is very fast
3. **Sufficient** - Covers all production needs:
   - Input validation
   - Dangerous pattern detection
   - PII detection (email, phone, SSN, credit card)
   - Output sanitization

## Features

### 1. Input Validation

- Empty input check
- Length limits (max 10,000 chars)
- Dangerous command detection
- PII detection

### 2. Dangerous Patterns Detected

```python
dangerous_patterns = [
    r'rm\s+-rf\s+/',
    r'del\s+/[fF]\s+/[qQ]',
    r'format\s+[cC]:',
    r'DROP\s+DATABASE',
    r'DROP\s+TABLE',
    r'eval\s*\(',
    r'exec\s*\(',
    r'__import__\s*\(',
]
```

### 3. PII Detection

- **Email**: `user@example.com`
- **Phone**: `123-456-7890`
- **SSN**: `123-45-6789`
- **Credit Card**: `1234-5678-9012-3456`

### 4. Output Sanitization

- Redacts detected PII
- Adds warnings for dangerous commands
- Configurable via environment variables

## Configuration

```bash
# .env
ENABLE_INPUT_VALIDATION=true
ENABLE_OUTPUT_SANITIZATION=true
ENABLE_PII_DETECTION=true
```

## Usage

```python
from src.middleware.guardrails import guardrails_middleware

# Validate input
result = guardrails_middleware.validate_input(
    "Delete all files with rm -rf /",
    user_id="john"
)
# Returns: {"valid": False, "errors": ["Potentially dangerous command detected"]}

# Sanitize output
result = guardrails_middleware.validate_output(
    "Contact me at john@example.com",
    contains_code=False
)
# Returns: {"valid": True, "sanitized": True, "content": "Contact me at [EMAIL_REDACTED]"}
```

## No External Dependencies

✅ **No guardrails-ai required**  
✅ **No additional packages needed**  
✅ **Pure Python with regex**  
✅ **Production-ready**

## If You Need Advanced Guardrails

If you want to use the full guardrails-ai library with AI-powered validation:

1. Install: `pip install guardrails-ai`
2. Implement Guard validators
3. Use DetectPII and ToxicLanguage from guardrails.hub

But for most production use cases, the current regex-based implementation is **sufficient and more efficient**.
