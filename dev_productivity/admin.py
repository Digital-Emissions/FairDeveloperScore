from django.contrib import admin
from .models import Developer, ProductivityMetric, Project


@admin.register(Developer)
class DeveloperAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'github_username', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'email', 'github_username']
    readonly_fields = ['created_at']


@admin.register(ProductivityMetric)
class ProductivityMetricAdmin(admin.ModelAdmin):
    list_display = ['developer', 'date', 'commit_count', 'lines_added', 'lines_deleted', 'productivity_score']
    list_filter = ['date', 'developer']
    search_fields = ['developer__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'date'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at'] 