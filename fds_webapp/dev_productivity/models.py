from django.db import models
from django.utils import timezone
import json


class FDSAnalysis(models.Model):
    """Model to store FDS analysis jobs and results"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Input parameters
    repo_url = models.URLField(max_length=500, help_text="GitHub repository URL")
    access_token = models.CharField(max_length=200, help_text="GitHub access token")
    commit_limit = models.IntegerField(default=300, help_text="Number of commits to analyze")
    
    # Analysis metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results summary
    total_commits = models.IntegerField(null=True, blank=True)
    total_batches = models.IntegerField(null=True, blank=True)
    total_developers = models.IntegerField(null=True, blank=True)
    execution_time = models.FloatField(null=True, blank=True, help_text="Execution time in seconds")
    
    # Error handling
    error_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "FDS Analysis"
        verbose_name_plural = "FDS Analyses"
    
    def __str__(self):
        return f"FDS Analysis for {self.repo_url} ({self.status})"


class DeveloperScore(models.Model):
    """Model to store individual developer FDS scores"""
    
    analysis = models.ForeignKey(FDSAnalysis, on_delete=models.CASCADE, related_name='developer_scores')
    
    # Developer info
    author_email = models.EmailField()
    
    # FDS scores
    fds_score = models.FloatField(help_text="Fair Developer Score")
    avg_effort = models.FloatField(help_text="Average effort score")
    avg_importance = models.FloatField(help_text="Average importance score")
    
    # Activity metrics
    total_commits = models.IntegerField()
    unique_batches = models.IntegerField()
    total_churn = models.FloatField()
    total_files = models.IntegerField()
    
    # Effort components (detailed metrics)
    share_mean = models.FloatField(help_text="Average share in collaborative work")
    scale_z_mean = models.FloatField(help_text="Average scale (normalized)")
    reach_z_mean = models.FloatField(help_text="Average reach (normalized)")
    centrality_z_mean = models.FloatField(help_text="Average centrality (normalized)")
    dominance_z_mean = models.FloatField(help_text="Average dominance (normalized)")
    novelty_z_mean = models.FloatField(help_text="Average novelty (normalized)")
    speed_z_mean = models.FloatField(help_text="Average speed (normalized)")
    
    # Time span
    first_commit_date = models.DateTimeField()
    last_commit_date = models.DateTimeField()
    activity_span_days = models.FloatField()
    
    class Meta:
        ordering = ['-fds_score']
        unique_together = ['analysis', 'author_email']
    
    def __str__(self):
        return f"{self.author_email}: {self.fds_score:.3f}"


class BatchMetrics(models.Model):
    """Model to store batch-level metrics"""
    
    analysis = models.ForeignKey(FDSAnalysis, on_delete=models.CASCADE, related_name='batch_metrics')
    
    batch_id = models.IntegerField()
    unique_authors = models.IntegerField()
    total_contribution = models.FloatField()
    avg_contribution = models.FloatField()
    max_contribution = models.FloatField()
    avg_effort = models.FloatField()
    importance = models.FloatField()
    total_churn = models.FloatField()
    total_files = models.IntegerField()
    commit_count = models.IntegerField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    duration_hours = models.FloatField()
    
    class Meta:
        ordering = ['-total_contribution']
        unique_together = ['analysis', 'batch_id']
    
    def __str__(self):
        return f"Batch {self.batch_id}: {self.total_contribution:.3f}"