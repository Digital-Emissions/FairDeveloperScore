from django import forms
from .models import FDSAnalysis
import re


class FDSAnalysisForm(forms.ModelForm):
    """Form for creating a new FDS analysis"""
    
    class Meta:
        model = FDSAnalysis
        fields = ['repo_url', 'access_token', 'commit_limit']
        widgets = {
            'repo_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/owner/repo',
                'required': True,
            }),
            'access_token': forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'ghp_...',
                'value': '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',
                'required': True,
            }),
            'commit_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 50,
                'max': 2000,
                'value': 300,
                'required': True,
            }),
        }
        help_texts = {
            'repo_url': 'Enter the full GitHub repository URL (e.g., https://github.com/torvalds/linux)',
            'access_token': 'Your GitHub personal access token for API access',
            'commit_limit': 'Number of recent commits to analyze (50-2000, recommended: 300)',
        }
    
    def clean_repo_url(self):
        """Validate GitHub repository URL format"""
        repo_url = self.cleaned_data.get('repo_url')
        
        if not repo_url:
            raise forms.ValidationError("Repository URL is required.")
        
        # Validate GitHub URL format
        github_pattern = r'^https://github\.com/[\w\-\.]+/[\w\-\.]+/?$'
        if not re.match(github_pattern, repo_url.rstrip('/')):
            raise forms.ValidationError(
                "Please enter a valid GitHub repository URL format: "
                "https://github.com/owner/repo"
            )
        
        return repo_url.rstrip('/')
    
    def clean_access_token(self):
        """Validate GitHub access token format"""
        access_token = self.cleaned_data.get('access_token')
        
        if not access_token:
            raise forms.ValidationError("GitHub access token is required.")
        
        # Basic validation for GitHub token format
        if not (access_token.startswith('ghp_') or access_token.startswith('github_pat_')):
            raise forms.ValidationError(
                "Please enter a valid GitHub personal access token. "
                "It should start with 'ghp_' or 'github_pat_'."
            )
        
        if len(access_token) < 36:
            raise forms.ValidationError(
                "GitHub access token appears to be too short. "
                "Please check your token."
            )
        
        return access_token
    
    def clean_commit_limit(self):
        """Validate commit limit range"""
        commit_limit = self.cleaned_data.get('commit_limit')
        
        if commit_limit is None:
            raise forms.ValidationError("Number of commits is required.")
        
        if commit_limit < 50:
            raise forms.ValidationError("Minimum number of commits is 50.")
        
        if commit_limit > 2000:
            raise forms.ValidationError("Maximum number of commits is 2000.")
        
        return commit_limit
    
    def extract_repo_info(self):
        """Extract owner and repo name from URL"""
        repo_url = self.cleaned_data.get('repo_url', '')
        if repo_url:
            # Extract owner/repo from https://github.com/owner/repo
            parts = repo_url.rstrip('/').split('/')
            if len(parts) >= 2:
                return parts[-2], parts[-1]  # owner, repo
        return None, None