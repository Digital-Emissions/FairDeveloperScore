from django.contrib import admin
from .models import LinuxKernelCommit, BatchStatistics


@admin.register(LinuxKernelCommit)
class LinuxKernelCommitAdmin(admin.ModelAdmin):
    list_display = ('short_hash', 'author_name', 'batch_id', 'commit_timestamp', 'files_changed', 'insertions', 'deletions', 'is_merge')
    list_filter = ('batch_id', 'is_merge', 'author_email', 'commit_timestamp')
    search_fields = ('hash', 'author_name', 'author_email', 'msg_subject')
    readonly_fields = ('hash', 'created_at')
    list_per_page = 50
    date_hierarchy = 'commit_timestamp'
    
    fieldsets = (
        ('Commit Information', {
            'fields': ('hash', 'msg_subject', 'commit_timestamp', 'batch_id')
        }),
        ('Author Information', {
            'fields': ('author_name', 'author_email')
        }),
        ('Time Deltas', {
            'fields': ('dt_prev_commit_sec', 'dt_prev_author_sec'),
            'classes': ('collapse',)
        }),
        ('Code Changes', {
            'fields': ('files_changed', 'insertions', 'deletions', 'is_merge')
        }),
        ('File System', {
            'fields': ('dirs_touched', 'file_types'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(BatchStatistics)
class BatchStatisticsAdmin(admin.ModelAdmin):
    list_display = ('batch_id', 'primary_author_name', 'commit_count', 'total_lines_changed', 'duration_seconds', 'start_time')
    list_filter = ('primary_author_name', 'start_time')
    search_fields = ('batch_id', 'primary_author_name', 'primary_author_email')
    readonly_fields = ('created_at',)
    ordering = ('batch_id',)
    
    fieldsets = (
        ('Batch Information', {
            'fields': ('batch_id', 'primary_author_name', 'primary_author_email')
        }),
        ('Statistics', {
            'fields': ('commit_count', 'total_insertions', 'total_deletions', 'total_files_changed')
        }),
        ('Time Information', {
            'fields': ('start_time', 'end_time', 'duration_seconds')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    ) 