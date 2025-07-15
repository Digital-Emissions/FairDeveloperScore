"""
URL configuration for dev_productivity project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("developers/", views.developer_list_view, name="developer_list"),
    path("developers/<int:developer_id>/", views.developer_detail_view, name="developer_detail"),
    path("metrics/", views.productivity_metrics_view, name="productivity_metrics"),
    path("projects/", views.projects_view, name="projects"),
    path("api/productivity-data/", views.api_productivity_data, name="api_productivity_data"),
    path("admin/", admin.site.urls),
]
