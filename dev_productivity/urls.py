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
    path('admin/', admin.site.urls),
    
    # Main dashboard
    path('', views.index, name='index'),
    
    # Batch-related views
    path('batches/', views.batch_list, name='batch_list'),
    path('batch/<int:batch_id>/', views.batch_detail, name='batch_detail'),
    
    # Commit details
    path('commit/<str:commit_hash>/', views.commit_detail, name='commit_detail'),
    
    # Analytics
    path('analytics/', views.clustering_analytics, name='analytics'),
    
    # API endpoints
    path('api/batch-data/', views.api_batch_data, name='api_batch_data'),
]
