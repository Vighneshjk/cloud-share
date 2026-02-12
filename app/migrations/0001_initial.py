
import app.models
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UploadedFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='uploads/')),
                ('original_name', models.CharField(blank=True, max_length=255)),
                ('size', models.BigIntegerField(default=0)),
                ('link_id', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(default=app.models.default_expiry)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ShareLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('link_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('expires_at', models.DateTimeField()),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.uploadedfile')),
            ],
        ),
        migrations.CreateModel(
            name='SecureLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('expiry_time', models.DateTimeField()),
                ('is_active', models.BooleanField(default=True)),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.uploadedfile')),
            ],
        ),
    ]
