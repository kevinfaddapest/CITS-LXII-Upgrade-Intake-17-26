from django.contrib.auth import get_user_model
import getpass
User = get_user_model()

try:
    # Replace 'Administrator' with the actual username
    user = User.objects.get(username='Administrator')
    user.is_superuser = True
    user.is_staff = True
    user.save()
    print(f"{user.username} is now a superuser and staff.")
except User.DoesNotExist:
    print("User 'Administrator' does not exist.")

# OR this one.

username = 'Administrator'
email = 'admin@example.com'
password = 'admin123'  # You should change this to a strong one

user, created = User.objects.get_or_create(username=username, defaults={
    'email': email
})

# Set superuser and staff privileges
user.is_superuser = True
user.is_staff = True

# Only set the password if it's a newly created user
if created:
    user.set_password(password)

user.save()

if created:
    print(f"User '{username}' was created as a superuser and staff.")
else:
    print(f"User '{username}' already existed and was promoted to superuser and staff.")

# OR

User = get_user_model()

username = 'Administrator'
email = 'admin@example.com'

try:
    user = User.objects.get(username=username)
    created = False
    print(f"User '{username}' already exists.")
except User.DoesNotExist:
    password = getpass.getpass("Enter password for Administrator: ")
    user = User.objects.create_user(username=username, email=email, password=password)
    created = True

# Promote to superuser and staff
user.is_superuser = True
user.is_staff = True
user.save()

if created:
    print(f"User '{username}' was created and granted superuser/staff rights.")
else:
    print(f"User '{username}' was granted superuser/staff rights.")
