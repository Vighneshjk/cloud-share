from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import uuid
import qrcode
from app.models import UploadedFile, SecureLink, ShareLink, get_user_storage_used


@login_required
def upload_file(request):
    if request.method == "POST":
        file = request.FILES.get("file")
        if file:
            UploadedFile.objects.create(
                user=request.user,
                file=file,
                original_name=file.name,
                size=file.size
            )
            messages.success(request, "File uploaded successfully!")
            return redirect("upload")

        messages.error(request, "No file selected!")

    return render(request, "upload.html")


@login_required
def files_list(request):
    search = request.GET.get("search", "")
    files = UploadedFile.objects.filter(user=request.user)

    if search:
        files = files.filter(original_name__icontains=search)

    sort = request.GET.get("sort")
    if sort == "name":
        files = files.order_by("original_name")
    elif sort == "size":
        files = files.order_by("size")
    elif sort == "date":
        files = files.order_by("-uploaded_at")

    return render(request, "files_list.html", {"files": files})


@login_required
def delete_file(request, file_id):
    file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    file.delete()
    messages.success(request, "File deleted successfully!")
    return redirect("files_list")


@login_required
def file_detail(request, file_id):
    file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    links = ShareLink.objects.filter(file=file)

    return render(request, "file_detail.html", {
        "file": file,
        "links": links,
    })


@login_required
def generate_link(request, file_id):
    file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    
    link = ShareLink.objects.create(
        file=file,
        expires_at=timezone.now() + timedelta(days=7)
    )

    messages.success(request, "Share link created!")
    return redirect("file_detail", file_id=file_id)


@login_required
def delete_link(request, link_id):
    link = get_object_or_404(ShareLink, id=link_id, file__user=request.user)
    file_id = link.file.id
    link.delete()
    messages.success(request, "Link removed.")
    return redirect("file_detail", file_id=file_id)


@login_required
def create_link(request, file_id):
    file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    return render(request, "create_link.html", {"file": file})


@login_required
def generate_secure_link(request, file_id):

    if request.method != "POST":
        return redirect("create_link", file_id=file_id)

    file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    expiry = request.POST.get("expiry")

    expiry_map = {
        "30m": timezone.now() + timedelta(minutes=30),
        "1h": timezone.now() + timedelta(hours=1),
        "24h": timezone.now() + timedelta(hours=24),
        "7d": timezone.now() + timedelta(days=7),
    }

    expires_at = expiry_map.get(expiry, timezone.now() + timedelta(hours=1))

    secure_link = SecureLink.objects.create(
        file=file,
        expiry_time=expires_at
    )

    qr_img = qrcode.make(
        request.build_absolute_uri(f"/download/{secure_link.token}/")
    )
    qr_path = f"media/qr/{secure_link.token}.png"
    qr_img.save(qr_path)

    return render(request, "link_success.html", {
        "file": file,
        "link": secure_link,
        "qr_path": "/" + qr_path
    })


@login_required
def links_list(request):
    links = SecureLink.objects.filter(file__user=request.user)
    return render(request, "links_list.html", {"links": links})


@login_required
def delete_secure_link(request, link_id):
    link = get_object_or_404(SecureLink, id=link_id, file__user=request.user)
    link.delete()
    messages.success(request, "Secure link deleted.")
    return redirect("links_list")


@login_required
def regenerate_link(request, link_id):
    old_link = get_object_or_404(SecureLink, id=link_id, file__user=request.user)
    file = old_link.file

    old_link.delete()

    new_link = SecureLink.objects.create(
        file=file,
        expiry_time=timezone.now() + timedelta(days=7)
    )
    messages.success(request, "New secure link generated.")
    return redirect("links_list")


@login_required
def dashboard(request):
    files = UploadedFile.objects.filter(user=request.user).order_by("-uploaded_at")

    return render(request, "dashboard/dashboard.html", {
        "files": files,
        "storage_used": get_user_storage_used(request.user),
    })


@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    files = UploadedFile.objects.all()
    return render(request, "admin/admin_dashboard.html", {"files": files})
