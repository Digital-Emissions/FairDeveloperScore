from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Avg, Sum, Count, Max, Min, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Developer, ProductivityMetric, Project


def index(request):
    return dashboard_view(request)


def dashboard_view(request):
    """
    Main dashboard view showing productivity overview.
    """
    # Get recent metrics (last 30 days)
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    recent_metrics = ProductivityMetric.objects.filter(date__gte=thirty_days_ago)
    
    # Calculate summary statistics
    total_developers = Developer.objects.count()
    total_projects = Project.objects.filter(is_active=True).count()
    total_commits = recent_metrics.aggregate(Sum('commit_count'))['commit_count__sum'] or 0
    avg_productivity = recent_metrics.aggregate(Avg('productivity_score'))['productivity_score__avg'] or 0
    
    # Get top performers
    top_developers = Developer.objects.annotate(
        total_commits=Sum('metrics__commit_count', filter=Q(metrics__date__gte=thirty_days_ago)),
        avg_productivity=Avg('metrics__productivity_score', filter=Q(metrics__date__gte=thirty_days_ago))
    ).filter(total_commits__gt=0).order_by('-avg_productivity')[:5]
    
    # Get recent activity
    recent_activity = recent_metrics.select_related('developer').order_by('-date')[:10]
    
    context = {
        'total_developers': total_developers,
        'total_projects': total_projects,
        'total_commits': total_commits,
        'avg_productivity': round(avg_productivity, 2) if avg_productivity else 0,
        'top_developers': top_developers,
        'recent_activity': recent_activity,
    }
    
    return render(request, 'dashboard.html', context)


def developer_list_view(request):
    """
    View to display all developers with their statistics.
    """
    developers = Developer.objects.annotate(
        total_commits=Sum('metrics__commit_count'),
        avg_productivity=Avg('metrics__productivity_score'),
        total_lines_added=Sum('metrics__lines_added'),
        total_lines_deleted=Sum('metrics__lines_deleted'),
        latest_activity=Max('metrics__date')
    ).order_by('name')
    
    context = {
        'developers': developers,
    }
    
    return render(request, 'developer_list.html', context)


def developer_detail_view(request, developer_id):
    """
    Detailed view for a specific developer.
    """
    developer = get_object_or_404(Developer, id=developer_id)
    
    # Get metrics for the last 30 days
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    metrics = developer.metrics.filter(date__gte=thirty_days_ago).order_by('-date')
    
    # Calculate statistics
    stats = metrics.aggregate(
        total_commits=Sum('commit_count'),
        avg_productivity=Avg('productivity_score'),
        total_lines_added=Sum('lines_added'),
        total_lines_deleted=Sum('lines_deleted'),
        max_productivity=Max('productivity_score'),
        min_productivity=Min('productivity_score')
    )
    
    context = {
        'developer': developer,
        'metrics': metrics,
        'stats': stats,
    }
    
    return render(request, 'developer_detail.html', context)


def productivity_metrics_view(request):
    """
    View to display productivity metrics in a table format.
    """
    # Get all metrics ordered by date (most recent first)
    metrics = ProductivityMetric.objects.select_related('developer').order_by('-date', 'developer__name')
    
    # Add pagination if needed
    from django.core.paginator import Paginator
    paginator = Paginator(metrics, 50)  # Show 50 metrics per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'metrics': page_obj.object_list,
    }
    
    return render(request, 'metrics.html', context)


def api_productivity_data(request):
    """
    API endpoint to get productivity data for charts.
    """
    # Get data for the last 30 days
    thirty_days_ago = timezone.now().date() - timedelta(days=30)
    metrics = ProductivityMetric.objects.filter(date__gte=thirty_days_ago)
    
    # Aggregate data by date
    daily_data = metrics.values('date').annotate(
        total_commits=Sum('commit_count'),
        avg_productivity=Avg('productivity_score'),
        total_lines_added=Sum('lines_added'),
        total_lines_deleted=Sum('lines_deleted')
    ).order_by('date')
    
    # Aggregate data by developer
    developer_data = metrics.values('developer__name').annotate(
        total_commits=Sum('commit_count'),
        avg_productivity=Avg('productivity_score'),
        total_lines_added=Sum('lines_added'),
        total_lines_deleted=Sum('lines_deleted')
    ).order_by('-avg_productivity')
    
    return JsonResponse({
        'daily_data': list(daily_data),
        'developer_data': list(developer_data),
    })


def projects_view(request):
    """
    View to display all projects.
    """
    projects = Project.objects.all().order_by('name')
    
    context = {
        'projects': projects,
    }
    
    return render(request, 'projects.html', context) 