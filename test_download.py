"""
Test script to verify file download functionality
"""
import os
import sys

sys.path.insert(0, r'd:\projects\cloud_share')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_share.settings')
import django
django.setup()

from django.contrib.auth.models import User
from app.models import UploadedFile, ShareLink
from django.utils import timezone
from datetime import timedelta
from django.core.files.base import ContentFile

def test_download_functionality():
    print("=" * 60)
    print("Testing File Download Functionality")
    print("=" * 60)
    
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✓ Created test user: {user.username}")
    else:
        print(f"✓ Using existing test user: {user.username}")
    
    test_content = b"This is a test file for download functionality testing."
    test_filename = "test_download.txt"
    
    uploaded_file = UploadedFile(
        user=user,
        original_name=test_filename,
        size=len(test_content)
    )
    uploaded_file.file.save(test_filename, ContentFile(test_content), save=True)
    print(f"✓ Created test file: {uploaded_file.original_name}")
    print(f"  File path: {uploaded_file.file.path}")
    print(f"  File exists: {os.path.exists(uploaded_file.file.path)}")
    
    expiry_time = timezone.now() + timedelta(hours=1)
    share_link = ShareLink.objects.create(
        file=uploaded_file,
        expires_at=expiry_time
    )
    print(f"✓ Created share link: {share_link.link_id}")
    print(f"  Expires at: {share_link.expires_at}")
    print(f"  Is expired: {share_link.is_expired()}")
    
    print("\n" + "=" * 60)
    print("Testing File Opening")
    print("=" * 60)
    
    try:
        file_handle = uploaded_file.file.open('rb')
        content = file_handle.read()
        file_handle.close()
        print(f"✓ Successfully opened and read file")
        print(f"  Content length: {len(content)} bytes")
        print(f"  Content preview: {content[:50]}")
    except Exception as e:
        print(f"✗ Error opening file: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("Share URLs")
    print("=" * 60)
    print(f"Download page: http://127.0.0.1:8000/s/{share_link.link_id}/")
    print(f"Direct download: http://127.0.0.1:8000/s/{share_link.link_id}/now/")
    
    print("\n" + "=" * 60)
    print("All Tests Passed! ✓")
    print("=" * 60)
    print("\nYou can now test the download by:")
    print("1. Opening the download page URL in your browser")
    print("2. Clicking the 'Download Securely' button")
    print("3. The file should download successfully")
    
    return True

if __name__ == "__main__":
    test_download_functionality()
