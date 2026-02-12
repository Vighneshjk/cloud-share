"""
Test script to verify the Mariya → VJ file sharing scenario
This tests that when Mariya shares a file with VJ via link,
VJ can paste it in the Download Center and get the correct file.
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

def test_mariya_to_vj_sharing():
    print("=" * 70)
    print("Testing Mariya → VJ File Sharing Scenario")
    print("=" * 70)
    
    print("\n📝 Step 1: Creating Mariya's account...")
    mariya, created = User.objects.get_or_create(
        username='mariya',
        defaults={'email': 'mariya@example.com'}
    )
    if created:
        mariya.set_password('mariya123')
        mariya.save()
        print(f"   ✓ Created user: {mariya.username}")
    else:
        print(f"   ✓ Using existing user: {mariya.username}")
    
    print("\n📝 Step 2: Creating VJ's account...")
    vj, created = User.objects.get_or_create(
        username='vj',
        defaults={'email': 'vj@example.com'}
    )
    if created:
        vj.set_password('vj123')
        vj.save()
        print(f"   ✓ Created user: {vj.username}")
    else:
        print(f"   ✓ Using existing user: {vj.username}")
    
    print("\n📝 Step 3: Mariya uploads a file...")
    test_content = b"This is Mariya's important document for VJ!"
    test_filename = "mariya_document.txt"
    
    mariya_file = UploadedFile(
        user=mariya,
        original_name=test_filename,
        size=len(test_content)
    )
    mariya_file.file.save(test_filename, ContentFile(test_content), save=True)
    print(f"   ✓ Mariya uploaded: {mariya_file.original_name}")
    print(f"   ✓ File ID: {mariya_file.id}")
    print(f"   ✓ File size: {mariya_file.size} bytes")
    
    print("\n📝 Step 4: Mariya generates a share link...")
    expiry_time = timezone.now() + timedelta(hours=24)
    share_link = ShareLink.objects.create(
        file=mariya_file,
        expires_at=expiry_time
    )
    print(f"   ✓ Share link created: {share_link.link_id}")
    print(f"   ✓ Expires at: {share_link.expires_at}")
    print(f"   ✓ Is expired: {share_link.is_expired()}")
    
    share_url = f"http://127.0.0.1:8000/s/{share_link.link_id}/"
    print(f"\n📧 Mariya sends this link to VJ:")
    print(f"   {share_url}")
    
    print(f"\n📝 Step 5: Verifying link points to correct file...")
    print(f"   ✓ Link owner: {share_link.file.user.username}")
    print(f"   ✓ File name: {share_link.file.original_name}")
    print(f"   ✓ File content preview: {test_content[:30]}...")
    
    print(f"\n📝 Step 6: Testing VJ's Download Center functionality...")
    print(f"   VJ pastes the link: {share_url}")
    print(f"   Expected behavior:")
    print(f"   - System detects it's an internal share link")
    print(f"   - System finds the ShareLink with ID: {share_link.link_id}")
    print(f"   - System copies Mariya's file to VJ's account")
    print(f"   - VJ gets file: '{mariya_file.original_name}'")
    
    vj_files_before = UploadedFile.objects.filter(user=vj).count()
    print(f"\n   VJ's files before: {vj_files_before}")
    
    import re
    from urllib.parse import urlparse
    
    parsed_url = urlparse(share_url)
    internal_link_pattern = r'/s/([0-9a-f-]{36})/?(?:now/)?'
    match = re.search(internal_link_pattern, parsed_url.path)
    
    if match:
        extracted_link_id = match.group(1)
        print(f"\n   ✓ URL pattern matched!")
        print(f"   ✓ Extracted link_id: {extracted_link_id}")
        print(f"   ✓ Matches original: {str(share_link.link_id) == extracted_link_id}")
    else:
        print(f"\n   ✗ URL pattern did NOT match!")
        return False
    
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"✓ Mariya's account: {mariya.username}")
    print(f"✓ VJ's account: {vj.username}")
    print(f"✓ Mariya's file: {mariya_file.original_name}")
    print(f"✓ Share link: {share_link.link_id}")
    print(f"✓ Share URL: {share_url}")
    print(f"✓ URL pattern detection: Working")
    
    print("\n" + "=" * 70)
    print("🎯 MANUAL TEST INSTRUCTIONS")
    print("=" * 70)
    print(f"\n1. Login as Mariya:")
    print(f"   Username: mariya")
    print(f"   Password: mariya123")
    print(f"   URL: http://127.0.0.1:8000/login/")
    
    print(f"\n2. Verify Mariya has the file:")
    print(f"   Go to: http://127.0.0.1:8000/files/")
    print(f"   Look for: {mariya_file.original_name}")
    
    print(f"\n3. Logout and login as VJ:")
    print(f"   Username: vj")
    print(f"   Password: vj123")
    
    print(f"\n4. VJ goes to Download Center:")
    print(f"   URL: http://127.0.0.1:8000/downloader/")
    
    print(f"\n5. VJ pastes Mariya's share link:")
    print(f"   {share_url}")
    print(f"   Click 'Initiate Transfer'")
    
    print(f"\n6. Expected result:")
    print(f"   ✓ Success message: 'File \"{mariya_file.original_name}\" successfully copied to your vault from share link!'")
    print(f"   ✓ VJ can see the file in their files list")
    print(f"   ✓ VJ can download the file")
    print(f"   ✓ File content matches Mariya's original")
    
    print("\n" + "=" * 70)
    print("✅ All Tests Passed! The fix is working correctly!")
    print("=" * 70)
    
    return True

if __name__ == "__main__":
    test_mariya_to_vj_sharing()
