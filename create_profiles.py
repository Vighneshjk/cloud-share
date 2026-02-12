import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_share.settings')
django.setup()

from django.contrib.auth.models import User
from app.models import UserProfile

for user in User.objects.all():
    try:
        if not hasattr(user, 'profile'):
            UserProfile.objects.create(user=user)
            print(f"Created profile for {user.username}")
        else:
            print(f"Profile exists for {user.username}")
    except Exception as e:
        print(f"Error creating profile for {user.username}: {e}")
