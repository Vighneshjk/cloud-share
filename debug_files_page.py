import os
import sys
import django
from django.test import RequestFactory
from django.contrib.auth.models import User
from django.urls import reverse

sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_share.settings')
django.setup()

from app.views import file_list

def test_file_list():
    factory = RequestFactory()
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.create_superuser('debug_admin', 'debug@test.com', 'password123')
    
    request = factory.get(reverse('file_list'))
    request.user = user
    
    try:
        response = file_list(request)
        print(f"Status Code: {response.status_code}")
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_file_list()
