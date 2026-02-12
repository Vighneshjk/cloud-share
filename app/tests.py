from django.test import TestCase, Client, RequestFactory
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from .models import UploadedFile, ShareLink
from unittest.mock import patch, MagicMock
from datetime import timedelta
import uuid

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_uploaded_file_creation(self):
        file = SimpleUploadedFile("test_file.txt", b"file_content")
        uploaded_file = UploadedFile.objects.create(
            user=self.user,
            file=file,
            original_name="test_file.txt",
            size=file.size
        )
        self.assertEqual(uploaded_file.original_name, "test_file.txt")
        self.assertEqual(uploaded_file.user, self.user)
        self.assertTrue(uploaded_file.uploaded_at)

    def test_share_link_creation_and_expiry(self):
        file = SimpleUploadedFile("test.txt", b"content")
        uploaded_file = UploadedFile.objects.create(user=self.user, file=file)
        
        future_time = timezone.now() + timedelta(hours=1)
        link = ShareLink.objects.create(file=uploaded_file, expires_at=future_time)
        self.assertFalse(link.is_expired())
        
        past_time = timezone.now() - timedelta(hours=1)
        expired_link = ShareLink.objects.create(file=uploaded_file, expires_at=past_time)
        self.assertTrue(expired_link.is_expired())

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        
        file = SimpleUploadedFile("test.txt", b"content")
        self.uploaded_file = UploadedFile.objects.create(
            user=self.user,
            original_name="test.txt",
            file=file,
            size=len(b"content")
        )

    def test_dashboard_view(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "test.txt")

    def test_file_list_view(self):
        response = self.client.get(reverse('file_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "test.txt")

    def test_download_file_direct(self):
        response = self.client.get(reverse('download_file_direct', args=[self.uploaded_file.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="test.txt"')

    def test_generate_secure_link(self):
        response = self.client.post(reverse('generate_secure_link', args=[self.uploaded_file.id]), {
            'expiry': '1h'
        })
        self.assertEqual(response.status_code, 200) # Returns link_success.html
        self.assertTrue(ShareLink.objects.filter(file=self.uploaded_file).exists())

    def test_upload_from_url_success(self):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"remote content"
            mock_response.headers = {'Content-Disposition': 'attachment; filename="remote.txt"'}
            mock_get.return_value = mock_response

            response = self.client.post(reverse('upload_from_url'), {'url': 'http://example.com/test.txt'})
            
            self.assertEqual(response.status_code, 302) # Redirects to file_list
            self.assertTrue(UploadedFile.objects.filter(original_name="remote.txt").exists())

    def test_upload_from_url_failure(self):
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection error")
            
            response = self.client.post(reverse('upload_from_url'), {'url': 'http://bad-url.com'})
            
            self.assertEqual(response.status_code, 302)
            messages = list(response.wsgi_request._messages)
            self.assertTrue(any("Failed to download file" in str(m) for m in messages))

class TemplateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')

    def test_downloader_page_renders(self):
        response = self.client.get(reverse('downloader'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'downloader.html')
