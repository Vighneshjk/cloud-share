from django.urls import path
from . import views

urlpatterns = [
    path("upload/", views.upload_file, name="upload"),
    path("files/", views.files_list, name="files_list"),
    path("file/<int:file_id>/generate-link/", views.generate_link, name="generate_link"),
    path("file/<int:file_id>/delete/", views.delete_file, name="delete_file"),
    path("file/<int:file_id>/", views.file_detail, name="file_detail"),
    path("file/<int:file_id>/generate-link/", views.generate_link, name="generate_link"),
    path("link/<int:link_id>/delete/", views.delete_link, name="delete_link"),
    path("file/<int:file_id>/create-link/", views.create_link, name="create_link"),
    path("file/<int:file_id>/create-link/process/", views.generate_secure_link, name="generate_secure_link"),
    path("links/", views.links_list, name="links_list"),
    path("link/<int:link_id>/delete/", views.delete_secure_link, name="delete_secure_link"),
    path("link/<int:link_id>/regenerate/", views.regenerate_link, name="regenerate_link"),
]
