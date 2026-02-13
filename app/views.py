import logging
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta
import requests
from django.core.files.base import ContentFile
from urllib.parse import urlparse

from .models import UploadedFile, SecureLink, ShareLink, get_user_storage_used, get_total_storage, get_user_storage_limit, PaymentTransaction, UserProfile
import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt


from django.utils.http import url_has_allowed_host_and_scheme

def redirect_back(request, default='dashboard'):
    """
    Redirects back to the referring page, or strict default.
    """
    referer = request.META.get('HTTP_REFERER')
    if referer and url_has_allowed_host_and_scheme(url=referer, allowed_hosts={request.get_host()}):
        return redirect(referer)
    return redirect(default)

def landing_page(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('dashboard')
    return render(request, "home.html")



@login_required
def dashboard(request):
    user = request.user
    files = UploadedFile.objects.filter(user=user).order_by('-uploaded_at')

    total_files = files.count()
    total_storage = sum(file.size for file in files)
    
    
    active_links = ShareLink.objects.filter(
        file__user=user,
        expires_at__gt=timezone.now()
    ).count()

    storage_mb = round(total_storage / (1024 * 1024), 2)

    context = {
        "files": files[:6],
        "total_files": total_files,
        "storage_mb": storage_mb,
        "active_links": active_links,
        "active_links_list": ShareLink.objects.filter(
            file__user=user, 
            expires_at__gt=timezone.now()
        )[:5]
    }

    return render(request, "dashboard/dashboard.html", context)


@login_required
def upload_file(request):
    if request.method == 'POST':
        uploaded_file = request.FILES['file']
        UploadedFile.objects.create(
            user=request.user,
            file=uploaded_file,
            original_name=uploaded_file.name,
            size=uploaded_file.size
        )
        messages.success(request, 'File uploaded successfully!')
        return redirect('dashboard')
    return render(request, 'upload.html')


@login_required
def generate_secure_link(request, file_id):
    file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    if request.method != 'POST':
        return render(request, 'create_link.html', {'file': file})
    
    expiry_choice = request.POST.get('expiry', '1h')
    durations = {
        '30m': timedelta(minutes=30),
        '1h': timedelta(hours=1),
        '24h': timedelta(hours=24),
        '48h': timedelta(hours=48),
        '2d': timedelta(days=2),
        '7d': timedelta(days=7),
    }
    expiry_time = timezone.now() + durations.get(expiry_choice, timedelta(hours=1))
    
    link = ShareLink.objects.create(file=file, expires_at=expiry_time)
    messages.success(request, 'Secure link created!')
    return render(request, 'link_success.html', {'link': link, 'file': file})


def download_file(request, token):
    link = get_object_or_404(ShareLink, link_id=token)
    if link.is_expired():
        return render(request, "download/expired.html", status=410)
    
    try:
        file_handle = link.file.file.open('rb')
        response = FileResponse(file_handle, as_attachment=True, filename=link.file.original_name)
        return response
    except FileNotFoundError:
        raise Http404("File not found")


def download_page(request, link_id):
    link = get_object_or_404(ShareLink, link_id=link_id)
    if link.is_expired():
        return render(request, "download/expired.html", status=410)
    return render(request, "download/download_page.html", {"link": link, "file": link.file})

def download_now(request, link_id):
    link = get_object_or_404(ShareLink, link_id=link_id)
    if link.is_expired():
        return render(request, "download/expired.html", status=410)
    
    try:
        file_handle = link.file.file.open('rb')
        response = FileResponse(file_handle, as_attachment=True, filename=link.file.original_name)
        return response
    except FileNotFoundError:
        raise Http404("File not found")


@login_required
def download_file_direct(request, file_id):
    file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    
    try:
        file_handle = file.file.open('rb')
        response = FileResponse(file_handle, as_attachment=True, filename=file.original_name)
        return response
    except FileNotFoundError:
        messages.error(request, "File not found on server.")
        return redirect('file_list')


@login_required
def downloader(request):
    return render(request, "downloader.html")

@login_required
def upload_from_url(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        if not url:
            messages.error(request, 'Please provide a valid URL.')
            return redirect('file_list')
        
        try:
            parsed_url = urlparse(url)
            
            import re
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
            
        return redirect_back(request, default='file_list')
    return redirect_back(request, default='file_list')



@login_required
def profile_page(request, username=None):
    if username and request.user.is_superuser and username != request.user.username:
        user = get_object_or_404(User, username=username)
        is_viewing_other = True
    elif username and username != request.user.username:
        messages.error(request, "You do not have permission to view this profile.")
        return redirect('dashboard')
    else:
        user = request.user
        is_viewing_other = False

    if request.method == "POST":
        new_username = request.POST.get("username")
        new_email = request.POST.get("email")
        
        if new_username and new_username != user.username:
            if User.objects.filter(username=new_username).exists():
                messages.error(request, f"Username '{new_username}' already taken!")
            else:
                user.username = new_username
        
        if new_email and new_email != user.email:
            if User.objects.filter(email=new_email).exists():
                messages.error(request, "Email already registered!")
            else:
                user.email = new_email
        
        if 'avatar' in request.FILES:
            profile = user.profile
            profile.avatar = request.FILES['avatar']
            profile.save()

        user.save()
        messages.success(request, f"Profile for '{user.username}' updated successfully!")
        
        if is_viewing_other:
            return redirect("user_profile", username=user.username)
        return redirect("profile")

    used = get_user_storage_used(user)
    used_mb = round(used / (1024 * 1024), 2)
    limit_mb = get_user_storage_limit(user)
    
    percent = 0
    if limit_mb > 0:
        percent = (used_mb / limit_mb) * 100
    
    remaining_mb = round(limit_mb - used_mb, 2)
    
    plans = [
        {"mb": 5120, "name": "5 GB", "price": 100},   # 100 INR
        {"mb": 10240, "name": "10 GB", "price": 180}, # 180 INR
        {"mb": 51200, "name": "50 GB", "price": 800}, # 800 INR
    ]
    
    transactions = None
    if is_viewing_other:
        transactions = PaymentTransaction.objects.filter(user=user).order_by('-created_at')
        for tx in transactions:
            tx.storage_increase_gb = round(tx.storage_increase_mb / 1024, 2)

    return render(request, "profile/profile.html", {
        "user": user,
        "is_viewing_other": is_viewing_other,
        "transactions": transactions,
        "used_mb": used_mb,
        "limit": limit_mb,
        "percent": percent,
        "remaining_mb": remaining_mb,
        "plans": plans,
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
    })

@csrf_exempt
@login_required
def initiate_payment(request):
    if request.method == "POST":
        try:
            amount = int(float(request.POST.get('amount')) * 100)  # Amount in paisa
            mb = float(request.POST.get('mb'))
            
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            payment = client.order.create({'amount': amount, 'currency': 'INR', 'payment_capture': '1'})
            
            PaymentTransaction.objects.create(
                user=request.user,
                order_id=payment['id'],
                amount=amount / 100,
                storage_increase_mb=mb,
                status='PENDING'
            )
            
            return JsonResponse({'order_id': payment['id'], 'amount': amount, 'currency': 'INR', 'key': settings.RAZORPAY_KEY_ID})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
@login_required
def payment_success(request):
    if request.method == "POST":
        try:
            data = request.POST
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            params_dict = {
                'razorpay_order_id': data.get('razorpay_order_id'),
                'razorpay_payment_id': data.get('razorpay_payment_id'),
                'razorpay_signature': data.get('razorpay_signature')
            }
            client.utility.verify_payment_signature(params_dict)
            
            transaction = PaymentTransaction.objects.get(order_id=data.get('razorpay_order_id'))
            transaction.payment_id = data.get('razorpay_payment_id')
            transaction.status = 'SUCCESS'
            transaction.save()
            
            profile = request.user.profile
            profile.storage_limit_mb += transaction.storage_increase_mb
            profile.save()
            
            messages.success(request, f"Storage increased by {transaction.storage_increase_mb/1024:.2f} GB!")
            return redirect('profile')
            
        except razorpay.errors.SignatureVerificationError:
            transaction = PaymentTransaction.objects.get(order_id=data.get('razorpay_order_id'))
            transaction.status = 'FAILED'
            transaction.save()
            messages.error(request, "Payment verification failed.")
            return redirect('profile')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('profile')
    return redirect('profile')


def admin_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)

@admin_required
def admin_dashboard(request):
    total_users = User.objects.count()
    total_storage = round(get_total_storage() / (1024 * 1024), 2)
    total_files = UploadedFile.objects.count()
    recent_files = UploadedFile.objects.order_by('-uploaded_at')[:10]
    
    users_list = []
    users = User.objects.all()
    for u in users:
        used = get_user_storage_used(u)
        limit = get_user_storage_limit(u)
        users_list.append({
            'obj': u,
            'used_mb': round(used / (1024 * 1024), 2),
            'limit_mb': limit,
            'file_count': UploadedFile.objects.filter(user=u).count()
        })
    
    chart_labels = [u.username for u in users]
    chart_data = [round(get_user_storage_used(u) / (1024 * 1024), 2) for u in users]
    
    return render(request, "admin/admin_dashboard.html", {
        "total_users": total_users,
        "total_storage": total_storage,
        "total_files": total_files,
        "recent_files": recent_files,
        "users": users_list,
        "user_storage_stats": zip(chart_labels, chart_data)
    })


def custom_404(request, exception):
    return render(request, "errors/error_404.html", status=404)

def custom_500(request):
    return render(request, "errors/error_500.html", status=500)


@login_required
def file_list(request):
    search = request.GET.get('search', '')
    sort = request.GET.get('sort', 'date')
    
    files = UploadedFile.objects.filter(user=request.user)
    if search:
        files = files.filter(original_name__icontains=search)
    
    if sort == 'name':
        files = files.order_by('original_name')
    elif sort == 'size':
        files = files.order_by('-size')
    else:
        files = files.order_by('-uploaded_at')
        
    return render(request, "my_files.html", {"files": files, "current_sort": sort})

@login_required
def file_detail(request, file_id):
    file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    links = ShareLink.objects.filter(file=file, expires_at__gt=timezone.now())
    return render(request, "file_detail.html", {"file": file, "links": links})


@login_required
def link_list(request):
    links = ShareLink.objects.filter(file__user=request.user).order_by('-expires_at')
    return render(request, "link_list.html", {"links": links})

@login_required
def delete_file(request, file_id):
    file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    if file.file:
        file.file.delete()
    file.delete()
    messages.success(request, "File deleted successfully.")
    return redirect_back(request, default='file_list')

@login_required
def delete_secure_link(request, link_id):
    link = get_object_or_404(ShareLink, id=link_id, file__user=request.user)
    link.delete()
    messages.success(request, "Link deleted successfully.")
    return redirect_back(request, default='link_list')