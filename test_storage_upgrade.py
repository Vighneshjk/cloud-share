
"""
Test script to verify user profile storage logic and payment transaction flow
"""
import os
import sys

sys.path.insert(0, r'd:\projects\cloud_share')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web_share.settings')
import django
django.setup()

from django.contrib.auth.models import User
from app.models import UserProfile, PaymentTransaction, get_user_storage_limit

def test_storage_logic():
    print("=" * 60)
    print("Testing Storage Upgrade Logic")
    print("=" * 60)
    
    username = "storage_tester"
    if User.objects.filter(username=username).exists():
        User.objects.filter(username=username).delete()
        
    user = User.objects.create_user(username=username, password="testpassword")
    print(f"✓ Created test user: {user.username}")
    
    try:
        profile = user.profile
        print(f"✓ User profile created automatically: {profile}")
        print(f"  Default storage limit: {profile.storage_limit_mb} MB")
        
        limit = get_user_storage_limit(user)
        assert limit == 1024.0
        print(f"✓ get_user_storage_limit returned correct default: {limit} MB")
        
    except UserProfile.DoesNotExist:
        print("✗ User profile was NOT created automatically!")
        return False
        
    print("\nSimulating Payment Transaction...")
    mb_increase = 5120.0 # 5GB
    amount = 100.0
    
    transaction = PaymentTransaction.objects.create(
        user=user,
        order_id="order_test_12345",
        payment_id="pay_test_12345",
        amount=amount,
        storage_increase_mb=mb_increase,
        status='SUCCESS'
    )
    print(f"✓ Created success transaction: {transaction}")
    
    user.profile.storage_limit_mb += transaction.storage_increase_mb
    user.profile.save()
    print(f"✓ Applied upgrade to user profile")
    
    user.refresh_from_db()
    new_limit = get_user_storage_limit(user)
    expected_limit = 1024.0 + 5120.0
    
    print(f"  New storage limit: {new_limit} MB")
    
    if new_limit == expected_limit:
        print(f"✓ Storage limit updated correctly! (1GB + 5GB = {new_limit/1024}GB)")
    else:
        print(f"✗ Storage limit mismatch! Expected {expected_limit}, got {new_limit}")
        return False
        
    print("\n" + "=" * 60)
    print("All Tests Passed! ✓")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_storage_logic()
