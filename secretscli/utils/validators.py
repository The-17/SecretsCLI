from email_validator import validate_email as ev, EmailNotValidError
import questionary
from questionary import Validator, ValidationError


class EmailValidator(Validator):

    def validate(self, document):
        email = document.text.strip()

        if not email:
            raise ValidationError(message="Email address cannot be empty", cursor_position=0)

        try:
            ev(email, check_deliverability=False)
        except EmailNotValidError as e:
            error_message = EmailValidator._get_friendly_error_message_(str(e))
            raise ValidationError(message=error_message, cursor_position=len(document.text))

    @staticmethod
    def _get_friendly_error_message_(technical_error: str) -> str:
        """
        Convert technical error messages to user-friendly ones.
        
        Args:
            technical_error: The technical error from email-validator
            
        Returns:
            A clean, user-friendly error message
        """
        error_lower = technical_error.lower()
        
        # Map common errors to friendly messages
        if "@-sign" in error_lower or "must have an @" in error_lower:
            return "Email must contain an @ symbol"
        
        elif "domain name" in error_lower or "after the @" in error_lower:
            return "Invalid domain name (e.g., use 'example.com')"
        
        elif "too long" in error_lower:
            return "Email address is too long"
        
        elif "empty" in error_lower or "blank" in error_lower:
            return "Email cannot be empty"
        
        elif "invalid character" in error_lower or "bad character" in error_lower:
            return "Email contains invalid characters"
        
        elif "quoted string" in error_lower:
            return "Invalid email format"
        
        elif "dots" in error_lower or "period" in error_lower:
            return "Invalid use of dots in email address"
        
        # Default fallback
        return "Please enter a valid email address (e.g., user@example.com)"


class PasswordValidator(Validator):

    def validate(self, document):
        password = document.text.strip()
        if not password:
            raise ValidationError(message="Password cannot be empty", cursor_position=0)
        
        if len(password) < 8:
            raise ValidationError(message="Password must be at least 8 characters long", cursor_position=len(password))
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            raise ValidationError(
                message="Password must contain uppercase, lowercase, and numbers", cursor_position=len(password))
        
