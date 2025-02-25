from django.core.exceptions import ValidationError

def custom_create_user(strategy, details, backend, user=None, *args, **kwargs):
    if user:
        return {'is_new': False}

    firstname = details.get('first_name', '')
    lastname = details.get('last_name', '')
    usernmae = details.get('username', '')

    return {
        'is_new': True,
        'user': strategy.storage.user.create_user(
            email=details['email'],
            firstname=firstname,
            lastname=lastname,
            username=usernmae,
        )
    }

def handle_conflicts(strategy, details, user=None, *args, **kwargs):
    """
    Handle conflicts when a social account email matches an existing user.
    """
    if user:
        # User is already associated with a social account; no conflict.
        return

    email = details.get('email')
    if email:
        # Check if the email already exists in the database.
        existing_user = strategy.storage.user.get_user_by_email(email)
        if existing_user:
            # If desired, associate the Google account with the existing user.
            return {'user': existing_user}
        
def activate_user(strategy, details, user=None, *args, **kwargs):
    """
    Activates the user if not already activated.
    """
    if user and not user.is_active:
        user.is_active = True
        user.save()
    return {'is_new_user': user is None}