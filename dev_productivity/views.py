from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Count, Sum, Avg, Min, Max, Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime
import json

from .models import LinuxKernelCommit, BatchStatistics


def index(request):
    """
    Main dashboard showing TORQUE clustering overview.
    """
    # Get basic statistics
    total_commits = LinuxKernelCommit.objects.count()
    total_batches = LinuxKernelCommit.objects.values('batch_id').distinct().count()
    total_authors = LinuxKernelCommit.objects.values('author_email').distinct().count()
    
    # Get recent batches for quick view
    recent_batches = (
        LinuxKernelCommit.objects
        .values('batch_id')
        .annotate(
            commit_count=Count('hash'),
            total_insertions=Sum('insertions'),
            total_deletions=Sum('deletions'),
            author_name=Min('author_name'),
            start_time=Min('commit_timestamp'),
            end_time=Max('commit_timestamp')
        )
        .order_by('-batch_id')[:10]
    )
    
    # Calculate summary statistics
    avg_commits_per_batch = total_commits / total_batches if total_batches > 0 else 0
    
    context = {
        'total_commits': total_commits,
        'total_batches': total_batches,
        'total_authors': total_authors,
        'avg_commits_per_batch': round(avg_commits_per_batch, 2),
        'recent_batches': recent_batches,
        'page_title': 'TORQUE Clustering Dashboard'
    }
    
    return render(request, 'dashboard.html', context)


def batch_list(request):
    """
    Display list of all batches with pagination and statistics.
    """
    # Get batch statistics
    batches = (
        LinuxKernelCommit.objects
        .values('batch_id')
        .annotate(
            commit_count=Count('hash'),
            total_insertions=Sum('insertions'),
            total_deletions=Sum('deletions'),
            total_files=Sum('files_changed'),
            author_name=Min('author_name'),
            author_email=Min('author_email'),
            start_time=Min('commit_timestamp'),
            end_time=Max('commit_timestamp'),
            merge_count=Count('hash', filter=Q(is_merge=True))
        )
        .order_by('batch_id')
    )
    
    # Add calculated fields
    for batch in batches:
        batch['total_changes'] = batch['total_insertions'] + batch['total_deletions']
        if batch['start_time'] and batch['end_time']:
            duration = (batch['end_time'] - batch['start_time']).total_seconds()
            batch['duration_minutes'] = round(duration / 60, 1)
        else:
            batch['duration_minutes'] = 0
        
        batch['avg_changes_per_commit'] = (
            round(batch['total_changes'] / batch['commit_count'], 1) 
            if batch['commit_count'] > 0 else 0
        )
    
    # Pagination
    paginator = Paginator(batches, 20)  # Show 20 batches per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_batches': len(batches),
        'page_title': 'All Batches'
    }
    
    return render(request, 'batch_list.html', context)


def batch_detail(request, batch_id):
    """
    Display detailed view of a specific batch.
    """
    # Get all commits in this batch
    commits = (
        LinuxKernelCommit.objects
        .filter(batch_id=batch_id)
        .order_by('commit_timestamp')
    )
    
    if not commits.exists():
        return render(request, '404.html', {'message': f'Batch {batch_id} not found'})
    
    # Calculate batch statistics
    batch_stats = commits.aggregate(
        commit_count=Count('hash'),
        total_insertions=Sum('insertions'),
        total_deletions=Sum('deletions'),
        total_files=Sum('files_changed'),
        start_time=Min('commit_timestamp'),
        end_time=Max('commit_timestamp'),
        merge_count=Count('hash', filter=Q(is_merge=True))
    )
    
    # Get primary author (most commits in batch)
    author_stats = (
        commits.values('author_name', 'author_email')
        .annotate(commit_count=Count('hash'))
        .order_by('-commit_count')
        .first()
    )
    
    # Calculate duration
    if batch_stats['start_time'] and batch_stats['end_time']:
        duration = (batch_stats['end_time'] - batch_stats['start_time']).total_seconds()
        batch_stats['duration_minutes'] = round(duration / 60, 1)
    else:
        batch_stats['duration_minutes'] = 0
    
    batch_stats['total_changes'] = batch_stats['total_insertions'] + batch_stats['total_deletions']
    
    # Get unique directories and file types
    all_dirs = []
    all_file_types = []
    for commit in commits:
        if commit.dirs_touched:
            all_dirs.extend(commit.dirs_list)
        if commit.file_types:
            all_file_types.extend(commit.file_types_list)
    
    unique_dirs = list(set(all_dirs))
    unique_file_types = list(set(all_file_types))
    
    context = {
        'batch_id': batch_id,
        'commits': commits,
        'batch_stats': batch_stats,
        'author_stats': author_stats,
        'unique_dirs': sorted(unique_dirs),
        'unique_file_types': sorted(unique_file_types),
        'page_title': f'Batch {batch_id} Details'
    }
    
    return render(request, 'batch_detail.html', context)


def commit_detail(request, commit_hash):
    """
    Display detailed view of a specific commit.
    """
    commit = get_object_or_404(LinuxKernelCommit, hash=commit_hash)
    
    # Get related commits in the same batch
    batch_commits = (
        LinuxKernelCommit.objects
        .filter(batch_id=commit.batch_id)
        .exclude(hash=commit_hash)
        .order_by('commit_timestamp')[:10]
    )
    
    context = {
        'commit': commit,
        'batch_commits': batch_commits,
        'page_title': f'Commit {commit.short_hash}'
    }
    
    return render(request, 'commit_detail.html', context)


def clustering_analytics(request):
    """
    Display clustering analytics and statistics.
    """
    # Batch size distribution
    batch_sizes = list(
        LinuxKernelCommit.objects
        .values('batch_id')
        .annotate(size=Count('hash'))
        .values_list('size', flat=True)
    )
    
    # Author productivity by batch
    author_batch_stats = (
        LinuxKernelCommit.objects
        .values('author_name')
        .annotate(
            batch_count=Count('batch_id', distinct=True),
            total_commits=Count('hash'),
            avg_insertions=Avg('insertions'),
            avg_deletions=Avg('deletions')
        )
        .order_by('-total_commits')[:20]
    )
    
    # Timeline data for visualization
    timeline_data = list(
        LinuxKernelCommit.objects
        .values('batch_id')
        .annotate(
            start_time=Min('commit_timestamp'),
            commit_count=Count('hash'),
            author=Min('author_name')
        )
        .order_by('start_time')
    )
    
    # Convert datetime to timestamp for JavaScript
    for item in timeline_data:
        if item['start_time']:
            item['timestamp'] = int(item['start_time'].timestamp() * 1000)
    
    context = {
        'batch_sizes': batch_sizes,
        'author_stats': author_batch_stats,
        'timeline_data': json.dumps(timeline_data),
        'page_title': 'Clustering Analytics'
    }
    
    return render(request, 'analytics.html', context)


def api_batch_data(request):
    """
    API endpoint for batch data (for charts/AJAX).
    """
    batches = list(
        LinuxKernelCommit.objects
        .values('batch_id')
        .annotate(
            commit_count=Count('hash'),
            total_changes=Sum('insertions') + Sum('deletions'),
            author=Min('author_name'),
            start_time=Min('commit_timestamp')
        )
        .order_by('batch_id')
    )
    
    # Convert datetime to string for JSON serialization
    for batch in batches:
        if batch['start_time']:
            batch['start_time'] = batch['start_time'].isoformat()
    
    return JsonResponse({'batches': batches}) 