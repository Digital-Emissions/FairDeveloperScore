from django.contrib import admin
from .models import FDSAnalysis, DeveloperScore, BatchMetrics


@admin.register(FDSAnalysis)
class FDSAnalysisAdmin(admin.ModelAdmin):
    list_display = ['id', 'repo_url', 'status', 'total_commits', 'total_developers', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['repo_url']
    readonly_fields = ['created_at', 'started_at', 'completed_at', 'execution_time']
    
    fieldsets = (
        ('Repository Info', {
            'fields': ('repo_url', 'access_token', 'commit_limit')
        }),
        ('Analysis Status', {
            'fields': ('status', 'error_message')
        }),
        ('Results', {
            'fields': ('total_commits', 'total_batches', 'total_developers', 'execution_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at')
        }),
    )


@admin.register(DeveloperScore)
class DeveloperScoreAdmin(admin.ModelAdmin):
    list_display = ['author_email', 'analysis', 'fds_score', 'total_commits', 'unique_batches']
    list_filter = ['analysis']
    search_fields = ['author_email']
    ordering = ['-fds_score']


@admin.register(BatchMetrics)
class BatchMetricsAdmin(admin.ModelAdmin):
    list_display = ['batch_id', 'analysis', 'unique_authors', 'commit_count', 'total_contribution']
    list_filter = ['analysis', 'unique_authors']
    ordering = ['-total_contribution']