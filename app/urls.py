from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from app import views
from app import views_auth

urlpatterns = [
    path('', views.landing_page, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('login/', views_auth.login_view, name='login'),
    path('logout/', views_auth.logout_view, name='logout'),
    path('register/', views_auth.register_view, name='register'),
    path('forgot-password/', views_auth.forgot_password, name='forgot_password'),

    path('profile/', views.profile_page, name='profile'),
    path('profile/<str:username>/', views.profile_page, name='user_profile'),
    path('upload/', views.upload_file, name='upload'), # Consolidated upload path
    path('payment/initiate/', views.initiate_payment, name='initiate_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),

    path('files/', views.file_list, name='file_list'),
    path("file/<int:file_id>/", views.file_detail, name="file_detail"),
    path("file/<int:file_id>/delete/", views.delete_file, name="delete_file"),
    path("file/<int:file_id>/generate-link/", views.generate_secure_link, name="generate_secure_link"),
    path("file/<int:file_id>/download-direct/", views.download_file_direct, name="download_file_direct"),
    path("upload-url/", views.upload_from_url, name="upload_from_url"),
    path("downloader/", views.downloader, name="downloader"),

    path('links/', views.link_list, name='link_list'),
    path('links/<int:link_id>/delete/', views.delete_secure_link, name='delete_secure_link'),
    path('download/<uuid:token>/', views.download_file, name='secure_download'),
    path('s/<uuid:link_id>/', views.download_page, name='share_page'),
    path('s/<uuid:link_id>/now/', views.download_now, name='share_download'),

    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    path("password-change/", 
         auth_views.PasswordChangeView.as_view(template_name="auth/change_password.html"),
         name="password_change"),
    path("password-change-done/", 
         auth_views.PasswordChangeDoneView.as_view(template_name="auth/change_password_done.html"),
         name="password_change_done"),

]


handler404 = "app.views.custom_404"
handler500 = "app.views.custom_500"
