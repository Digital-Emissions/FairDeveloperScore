from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('analyses/', views.analysis_list, name='analysis_list'),
    path('analysis/<int:analysis_id>/', views.analysis_detail, name='analysis_detail'),
    path('analysis/<int:analysis_id>/status/', views.analysis_status, name='analysis_status'),
    path('analysis/<int:analysis_id>/developer/<str:developer_email>/', views.developer_detail, name='developer_detail'),
    path('analysis/<int:analysis_id>/batch/<int:batch_id>/', views.batch_detail, name='batch_detail'),
    path('analysis/<int:analysis_id>/compare/', views.compare_developers, name='compare_developers'),
    path('analysis/<int:analysis_id>/delete/', views.delete_analysis, name='delete_analysis'),
]