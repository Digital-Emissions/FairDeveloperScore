from django.db import models
from django.utils import timezone


class Developer(models.Model):
    """
    Model representing a developer and their productivity metrics.
    """
    name = models.CharField(max_length=100, verbose_name="Developer Name")
    email = models.EmailField(unique=True, verbose_name="Email Address")
    github_username = models.CharField(max_length=100, blank=True, verbose_name="GitHub Username")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    
    class Meta:
        ordering = ['name']
        verbose_name = "Developer"
        verbose_name_plural = "Developers"
    
    def __str__(self):
        return self.name


class ProductivityMetric(models.Model):
    """
    Model representing productivity metrics for a developer.
    """
    developer = models.ForeignKey(Developer, on_delete=models.CASCADE, related_name='metrics')
    date = models.DateField(verbose_name="Date")
    commit_count = models.IntegerField(default=0, verbose_name="Commit Count")
    lines_added = models.IntegerField(default=0, verbose_name="Lines Added")
    lines_deleted = models.IntegerField(default=0, verbose_name="Lines Deleted")
    productivity_score = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        verbose_name="Productivity Score"
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    
    class Meta:
        ordering = ['-date']
        unique_together = ['developer', 'date']
        verbose_name = "Productivity Metric"
        verbose_name_plural = "Productivity Metrics"
    
    def __str__(self):
        return f"{self.developer.name} - {self.date}"
    
    @property
    def total_lines_changed(self):
        """Calculate total lines changed (added + deleted)."""
        return self.lines_added + self.lines_deleted


class Project(models.Model):
    """
    Model representing a project.
    """
    name = models.CharField(max_length=200, verbose_name="Project Name")
    description = models.TextField(blank=True, verbose_name="Description")
    repository_url = models.URLField(blank=True, verbose_name="Repository URL")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    
    class Meta:
        ordering = ['name']
        verbose_name = "Project"
        verbose_name_plural = "Projects"
    
    def __str__(self):
        return self.name 