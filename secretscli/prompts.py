import questionary
from questionary import Style
import rich
from .utils.validators import EmailValidator, PasswordValidator

custom_style = Style([
    ('qmark', 'fg:#673ab7 bold'),       
    ('question', 'bold'),                
    ('answer', 'fg:#f44336 bold'),     
    ('pointer', 'fg:#673ab7 bold'),     
    ('highlighted', 'fg:#673ab7 bold'), 
    ('selected', 'fg:#cc5454'),       
    ('separator', 'fg:#cc5454'),        
    ('instruction', ''),                
    ('text', ''),                       
])

class Form:

    @staticmethod
    def signup_form() -> dict:
        rich.print("Create your SecretsCLI account")

        first_name = questionary.text("First name:", style=custom_style).ask()
        last_name = questionary.text("Last name:", style=custom_style).ask()
        email = questionary.text("Email address: ", style=custom_style, validate=EmailValidator, validate_while_typing=False).ask()

        while True:
            password = questionary.password("Password: ", style=custom_style, validate=PasswordValidator, validate_while_typing=False).ask()
            password_confirm = questionary.password("Password (again)", style=custom_style, validate_while_typing=False).ask()
            
            if password_confirm is None:
                return None
            
            if password == password_confirm:
                break
            
            # Show error and loop back
            print("❌ Passwords do not match. Please try again.\n")

        return {
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "email": email.strip(),
            "password": password
        }
    
    @staticmethod
    def login_form() -> dict:
        rich.print("Login to your SecretsCLI account")

        email = questionary.text("Email address: ", style=custom_style, validate=EmailValidator, validate_while_typing=False).ask()
        password = questionary.password("Password: ", style=custom_style).ask()

        if not email or not password:
            return None

        
        return {
            "email": email.strip(),
            "password": password
        }
