from django.db import models
from django.contrib.auth.models import User
import uuid
import os

def user_directory_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return f"user_{instance.user.id}/{filename}"

class UserFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to=user_directory_path)
    original_name = models.CharField(max_length=255)
    size = models.PositiveBigIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def filename(self):
        return os.path.basename(self.file.name)

    def __str__(self):
        return self.original_name
class FileLink(models.Model):
    file = models.ForeignKey(UserFile, on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def get_full_link(self):
        return f"/download/{self.uuid}/"

    def __str__(self):
        return str(self.uuid)
