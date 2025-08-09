from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.paginator import Paginator
from .models import FDSAnalysis, DeveloperScore, BatchMetrics
from .forms import FDSAnalysisForm
from .services import FDSAnalysisService
import json


def home(request):
    """Home page with form to start new analysis"""
    if request.method == 'POST':
        form = FDSAnalysisForm(request.POST)
        if form.is_valid():
            analysis = form.save()
            # Start analysis in background
            service = FDSAnalysisService()
            service.start_analysis(analysis.id)
            messages.success(request, f'Analysis started for {analysis.repo_url}. Analysis ID: {analysis.id}')
            return redirect('analysis_detail', analysis_id=analysis.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FDSAnalysisForm()
    
    # Show recent analyses
    recent_analyses = FDSAnalysis.objects.all()[:5]
    
    context = {
        'form': form,
        'recent_analyses': recent_analyses,
    }
    return render(request, 'dev_productivity/home.html', context)


def analysis_list(request):
    """List all analyses with pagination"""
    analyses = FDSAnalysis.objects.all()
    paginator = Paginator(analyses, 10)  # Show 10 analyses per page
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'dev_productivity/analysis_list.html', context)


def analysis_detail(request, analysis_id):
    """Show detailed results of an analysis"""
    analysis = get_object_or_404(FDSAnalysis, id=analysis_id)
    
    # Get developer scores with pagination
    developer_scores = analysis.developer_scores.all()
    dev_paginator = Paginator(developer_scores, 20)
    dev_page = request.GET.get('dev_page')
    dev_page_obj = dev_paginator.get_page(dev_page)
    
    # Get top batches
    top_batches = analysis.batch_metrics.all()[:10]
    
    # Calculate statistics
    stats = {}
    if analysis.status == 'completed':
        scores = list(developer_scores.values_list('fds_score', flat=True))
        if scores:
            stats = {
                'total_fds': sum(scores),
                'avg_fds': sum(scores) / len(scores),
                'max_fds': max(scores),
                'min_fds': min(scores),
            }
    
    context = {
        'analysis': analysis,
        'dev_page_obj': dev_page_obj,
        'top_batches': top_batches,
        'stats': stats,
    }
    return render(request, 'dev_productivity/analysis_detail.html', context)


def analysis_status(request, analysis_id):
    """API endpoint to check analysis status"""
    analysis = get_object_or_404(FDSAnalysis, id=analysis_id)
    
    data = {
        'status': analysis.status,
        'total_commits': analysis.total_commits,
        'total_batches': analysis.total_batches,
        'total_developers': analysis.total_developers,
        'execution_time': analysis.execution_time,
        'error_message': analysis.error_message,
    }
    
    if analysis.completed_at:
        data['completed_at'] = analysis.completed_at.isoformat()
    
    return JsonResponse(data)


def developer_detail(request, analysis_id, developer_email):
    """Show detailed metrics for a specific developer"""
    analysis = get_object_or_404(FDSAnalysis, id=analysis_id)
    developer = get_object_or_404(
        DeveloperScore, 
        analysis=analysis, 
        author_email=developer_email
    )
    
    # Get batches this developer contributed to
    developer_batches = analysis.batch_metrics.filter(
        batch_id__in=analysis.batch_metrics.values_list('batch_id', flat=True)
    ).order_by('-total_contribution')[:10]
    
    context = {
        'analysis': analysis,
        'developer': developer,
        'developer_batches': developer_batches,
    }
    return render(request, 'dev_productivity/developer_detail.html', context)


def batch_detail(request, analysis_id, batch_id):
    """Show detailed metrics for a specific batch"""
    analysis = get_object_or_404(FDSAnalysis, id=analysis_id)
    batch = get_object_or_404(
        BatchMetrics, 
        analysis=analysis, 
        batch_id=batch_id
    )
    
    # Find developers who contributed to this batch
    batch_developers = analysis.developer_scores.all()[:10]  # Simplified for now
    
    context = {
        'analysis': analysis,
        'batch': batch,
        'batch_developers': batch_developers,
    }
    return render(request, 'dev_productivity/batch_detail.html', context)


def compare_developers(request, analysis_id):
    """Compare multiple developers side by side"""
    analysis = get_object_or_404(FDSAnalysis, id=analysis_id)
    
    selected_emails = request.GET.getlist('developers')
    developers = []
    
    if selected_emails:
        developers = analysis.developer_scores.filter(
            author_email__in=selected_emails
        ).order_by('-fds_score')
    
    all_developers = analysis.developer_scores.all()
    
    context = {
        'analysis': analysis,
        'developers': developers,
        'all_developers': all_developers,
        'selected_emails': selected_emails,
    }
    return render(request, 'dev_productivity/compare_developers.html', context)


@require_POST
def delete_analysis(request, analysis_id):
    """Delete an analysis and all related data"""
    analysis = get_object_or_404(FDSAnalysis, id=analysis_id)
    
    try:
        repo_name = analysis.repo_url.split('/')[-1] if analysis.repo_url else f"Analysis {analysis_id}"
        analysis.delete()  # This will cascade delete related DeveloperScore and BatchMetrics
        
        messages.success(request, f'Analysis for "{repo_name}" has been successfully deleted.')
        return redirect('analysis_list')
    
    except Exception as e:
        messages.error(request, f'Error deleting analysis: {str(e)}')
        return redirect('analysis_detail', analysis_id=analysis_id)