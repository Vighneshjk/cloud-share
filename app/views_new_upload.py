import re
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from urllib.parse import urlparse
import requests
from django.core.files.base import ContentFile
from .models import UploadedFile, ShareLink

@login_required
def upload_from_url(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        if not url:
            messages.error(request, 'Please provide a valid URL.')
            return redirect('file_list')
        
        try:
            parsed_url = urlparse(url)
            
            internal_link_pattern = r'/s/([0-9a-f-]{36})/?(?:now/)?'
            match = re.search(internal_link_pattern, parsed_url.path)
            
            if match:
                link_id = match.group(1)
                
                try:
                    share_link = ShareLink.objects.get(link_id=link_id)
                    
                    if share_link.is_expired():
                        messages.error(request, 'This share link has expired.')
                        return redirect('file_list')
                    
                    original_file = share_link.file
                    
                    if original_file.user == request.user:
                        messages.warning(request, 'This is your own file! You already have it in your files.')
                        return redirect('file_list')
                    
                    with original_file.file.open('rb') as source_file:
                        content = ContentFile(source_file.read())
                        
                        new_file = UploadedFile(
                            user=request.user,
                            original_name=original_file.original_name,
                            size=original_file.size
                        )
                        new_file.file.save(original_file.original_name, content, save=True)
                    
                    messages.success(request, f'File "{original_file.original_name}" successfully copied to your vault from share link!')
                    return redirect('file_list')
                    
                except ShareLink.DoesNotExist:
                    messages.error(request, 'Invalid share link.')
                    return redirect('file_list')
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            filename = None
            if 'Content-Disposition' in response.headers:
                fname_match = re.findall('filename="?([^"]+)"?', response.headers['Content-Disposition'])
                if fname_match:
                    filename = fname_match[0]
            
            if not filename:
                filename = os.path.basename(parsed_url.path)
            
            if not filename:
                filename = 'downloaded_file'

            content = ContentFile(response.content)
            
            uploaded_file = UploadedFile(
                user=request.user,
                original_name=filename,
                size=len(response.content)
            )
            uploaded_file.file.save(filename, content, save=True)

            messages.success(request, 'File downloaded from external URL successfully!')
        except Exception as e:
            messages.error(request, f'Failed to download file: {str(e)}')
            
        return redirect('file_list')
    return redirect('file_list')
