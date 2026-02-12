import os
import django
import sys
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_share.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

def test_page():
    c = Client()
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.create_superuser('admin_test', 'admin@test.com', 'admin')
    
    c.force_login(user)
    try:
        response = c.get('/files/')
        print(f"Status Code: {response.status_code}")
        if response.status_code == 500:
             print(response.content.decode('utf-8')[:1000])
        else:
             print("Success!")
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_page()
