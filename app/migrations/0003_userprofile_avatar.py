
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_paymenttransaction_userprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='avatar',
            field=models.ImageField(blank=True, null=True, upload_to='avatars/'),
        ),
    ]
