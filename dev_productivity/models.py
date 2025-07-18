from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator


class LinuxKernelCommit(models.Model):
    """
    Model representing Linux kernel commits with TORQUE clustering data.
    Table name: test_pretrained_data_linux_kernel_commits
    """
    # Primary commit information
    hash = models.CharField(max_length=40, primary_key=True, verbose_name="Commit Hash")
    author_name = models.CharField(max_length=255, verbose_name="Author Name")
    author_email = models.EmailField(verbose_name="Author Email")
    commit_timestamp = models.DateTimeField(verbose_name="Commit Timestamp")
    
    # Time delta features
    dt_prev_commit_sec = models.FloatField(
        null=True, 
        blank=True, 
        verbose_name="Seconds Since Previous Commit"
    )
    dt_prev_author_sec = models.FloatField(
        null=True, 
        blank=True, 
        verbose_name="Seconds Since Author's Previous Commit"
    )
    
    # File and code change metrics
    files_changed = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0)],
        verbose_name="Files Changed"
    )
    insertions = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0)],
        verbose_name="Lines Inserted"
    )
    deletions = models.IntegerField(
        default=0, 
        validators=[MinValueValidator(0)],
        verbose_name="Lines Deleted"
    )
    
    # Commit characteristics
    is_merge = models.BooleanField(default=False, verbose_name="Is Merge Commit")
    dirs_touched = models.TextField(blank=True, verbose_name="Directories Touched")
    file_types = models.TextField(blank=True, verbose_name="File Types")
    msg_subject = models.CharField(max_length=255, verbose_name="Commit Message Subject")
    
    # TORQUE clustering result
    batch_id = models.IntegerField(
        validators=[MinValueValidator(0)],
        verbose_name="Batch ID"
    )
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    
    class Meta:
        db_table = 'test_pretrained_data_linux_kernel_commits'
        ordering = ['commit_timestamp']
        verbose_name = "Linux Kernel Commit"
        verbose_name_plural = "Linux Kernel Commits"
        indexes = [
            models.Index(fields=['author_email']),
            models.Index(fields=['batch_id']),
            models.Index(fields=['commit_timestamp']),
            models.Index(fields=['is_merge']),
        ]
    
    def __str__(self):
        return f"{self.hash[:8]} - {self.author_name} - Batch {self.batch_id}"
    
    @property
    def total_lines_changed(self):
        """Calculate total lines changed (insertions + deletions)."""
        return self.insertions + self.deletions
    
    @property
    def dirs_list(self):
        """Return list of directories touched."""
        return [d.strip() for d in self.dirs_touched.split(';') if d.strip()] if self.dirs_touched else []
    
    @property
    def file_types_list(self):
        """Return list of file types."""
        return [t.strip() for t in self.file_types.split(';') if t.strip()] if self.file_types else []
    
    @property
    def short_hash(self):
        """Return shortened commit hash."""
        return self.hash[:8]
    
    @property
    def commit_date(self):
        """Return just the date part of commit timestamp."""
        return self.commit_timestamp.date()


class BatchStatistics(models.Model):
    """
    Model for storing computed statistics for each batch.
    """
    batch_id = models.IntegerField(unique=True, verbose_name="Batch ID")
    commit_count = models.IntegerField(default=0, verbose_name="Number of Commits")
    total_insertions = models.IntegerField(default=0, verbose_name="Total Insertions")
    total_deletions = models.IntegerField(default=0, verbose_name="Total Deletions")
    total_files_changed = models.IntegerField(default=0, verbose_name="Total Files Changed")
    
    # Time span of the batch
    start_time = models.DateTimeField(verbose_name="Batch Start Time")
    end_time = models.DateTimeField(verbose_name="Batch End Time")
    duration_seconds = models.FloatField(verbose_name="Batch Duration (seconds)")
    
    # Author information
    primary_author_email = models.EmailField(verbose_name="Primary Author Email")
    primary_author_name = models.CharField(max_length=255, verbose_name="Primary Author Name")
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Created At")
    
    class Meta:
        ordering = ['batch_id']
        verbose_name = "Batch Statistics"
        verbose_name_plural = "Batch Statistics"
    
    def __str__(self):
        return f"Batch {self.batch_id} - {self.commit_count} commits - {self.primary_author_name}"
    
    @property
    def total_lines_changed(self):
        """Calculate total lines changed in this batch."""
        return self.total_insertions + self.total_deletions
    
    @property
    def avg_lines_per_commit(self):
        """Calculate average lines changed per commit."""
        return self.total_lines_changed / self.commit_count if self.commit_count > 0 else 0 