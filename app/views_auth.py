from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
import random

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Logged in successfully!")
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "auth/login.html")


def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "Logged out successfully!")
        return redirect("home")
    return redirect("dashboard") # Redirect to dashboard if someone tries to GET logout



def forgot_password(request):
    if request.method == "POST":
        email = request.POST["email"]

        if User.objects.filter(email=email).exists():
            otp = random.randint(100000, 999999)

            user = User.objects.get(email=email)
            user.set_password(str(otp))
            user.save()

            send_mail(
                subject="CloudShare Password Reset",
                message=f"Your temporary password is: {otp}",
                from_email="noreply@cloudshare.com",
                recipient_list=[email],
                fail_silently=True,
            )

            messages.success(request, "Temporary password sent to your email!")
            return redirect("login")
        else:
            messages.error(request, "Email not found")

    return render(request, "auth/forgot_password.html")


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect("register")

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        messages.success(request, "Account created successfully! Please login.")
        return redirect("login")

    return render(request, "auth/register.html")
