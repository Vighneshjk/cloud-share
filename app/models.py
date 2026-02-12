from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
from datetime import timedelta
from django.db.models.signals import post_save
from django.dispatch import receiver

def default_expiry():
    return timezone.now() + timedelta(days=1)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    storage_limit_mb = models.FloatField(default=1024.0)  # Default 1GB
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class UploadedFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(upload_to="uploads/")
    original_name = models.CharField(max_length=255, blank=True)
    size = models.BigIntegerField(default=0)
    link_id = models.UUIDField(default=uuid.uuid4, unique=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_expiry)

    def __str__(self):
        return self.original_name

class SecureLink(models.Model):
    file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    expiry_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def is_expired(self):
        return timezone.now() > self.expiry_time

    def __str__(self):
        return str(self.token)

class ShareLink(models.Model):
    file = models.ForeignKey(UploadedFile, on_delete=models.CASCADE)
    link_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    expires_at = models.DateTimeField()
    
    def is_expired(self):
        return timezone.now() > self.expires_at

class PaymentTransaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=100, unique=True)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Amount in INR
    storage_increase_mb = models.FloatField()  # How much storage was purchased
    status = models.CharField(max_length=20, default='PENDING')  # PENDING, SUCCESS, FAILED
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.order_id} - {self.status}"

def get_user_storage_used(user):
    total = UploadedFile.objects.filter(user=user).aggregate(models.Sum("size"))["size__sum"]
    return total or 0

def get_total_storage():
    total = UploadedFile.objects.aggregate(models.Sum("size"))["size__sum"]
    return total or 0

def get_user_storage_limit(user):
    try:
        return user.profile.storage_limit_mb
    except UserProfile.DoesNotExist:
        return 1024.0  # Default fallback if profile doesn't exist

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)
