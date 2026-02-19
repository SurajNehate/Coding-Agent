"""Guardrails for input validation and output sanitization."""
import os
import re
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()


class GuardrailsMiddleware:
    """Input validation and output sanitization."""
    
    def __init__(self):
        """Initialize guardrails."""
        self.input_validation_enabled = os.getenv("ENABLE_INPUT_VALIDATION", "true").lower() == "true"
        self.output_sanitization_enabled = os.getenv("ENABLE_OUTPUT_SANITIZATION", "true").lower() == "true"
        self.pii_detection_enabled = os.getenv("ENABLE_PII_DETECTION", "true").lower() == "true"
        
        # PII patterns
        self.pii_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        }
        
        # Dangerous patterns in code
        self.dangerous_patterns = [
            r'rm\s+-rf\s+/',
            r'del\s+/[fF]\s+/[qQ]',
            r'format\s+[cC]:',
            r'DROP\s+DATABASE',
            r'DROP\s+TABLE',
            r'eval\s*\(',
            r'exec\s*\(',
            r'__import__\s*\(',
        ]
    
    def validate_input(self, text: str, user_id: str) -> Dict[str, Any]:
        """Validate user input."""
        if not self.input_validation_enabled:
            return {"valid": True, "errors": []}
        
        errors = []
        
        # Check for empty input
        if not text or not text.strip():
            errors.append("Input cannot be empty")
        
        # Check length
        if len(text) > 10000:
            errors.append("Input too long (max 10000 characters)")
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                errors.append(f"Potentially dangerous command detected")
                break
        
        # Detect PII if enabled
        if self.pii_detection_enabled:
            pii_found = self._detect_pii(text)
            if pii_found:
                errors.append(f"PII detected: {', '.join(pii_found)}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "sanitized_input": text
        }
    
    def validate_output(
        self,
        text: str,
        contains_code: bool = False
    ) -> Dict[str, Any]:
        """Validate and sanitize output."""
        if not self.output_sanitization_enabled:
            return {
                "valid": True,
                "sanitized": False,
                "content": text
            }
        
        sanitized_text = text
        was_sanitized = False
        
        # Remove PII if detected
        if self.pii_detection_enabled:
            for pii_type, pattern in self.pii_patterns.items():
                if re.search(pattern, sanitized_text):
                    sanitized_text = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", sanitized_text)
                    was_sanitized = True
        
        # For code blocks, check for dangerous patterns
        if contains_code:
            for pattern in self.dangerous_patterns:
                if re.search(pattern, sanitized_text, re.IGNORECASE):
                    # Add warning comment
                    sanitized_text = f"⚠️ WARNING: Potentially dangerous command detected\n\n{sanitized_text}"
                    was_sanitized = True
                    break
        
        return {
            "valid": True,
            "sanitized": was_sanitized,
            "content": sanitized_text
        }
    
    def _detect_pii(self, text: str) -> List[str]:
        """Detect PII in text."""
        found = []
        for pii_type, pattern in self.pii_patterns.items():
            if re.search(pattern, text):
                found.append(pii_type)
        return found
    
    def sanitize_for_logging(self, text: str) -> str:
        """Sanitize text for logging (remove all PII)."""
        sanitized = text
        for pii_type, pattern in self.pii_patterns.items():
            sanitized = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", sanitized)
        return sanitized


# Export singleton instance
guardrails_middleware = GuardrailsMiddleware()
