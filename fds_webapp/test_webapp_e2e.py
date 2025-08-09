#!/usr/bin/env python3
"""
End-to-end test that drives the existing Django web app directly (no new app).

- Posts the home form with repo URL, token, and commit count
- Forces the analysis to run synchronously (no background thread)
- Fetches the analysis detail page HTML and saves it locally

Usage:
  set GITHUB_TOKEN=... && python test_webapp_e2e.py
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.append(str(PROJECT_ROOT))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fds_webapp.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from dev_productivity.models import FDSAnalysis, DeveloperScore
from dev_productivity.services import FDSAnalysisService


def run_e2e(repo_url: str, token: str, commit_limit: int = 50) -> Path:
    # Monkeypatch: run analysis synchronously inside the request
    original_start = FDSAnalysisService.start_analysis

    def _sync_start(self, analysis_id: int):
        # Directly run the analysis in the same thread
        self._run_analysis(analysis_id)

    FDSAnalysisService.start_analysis = _sync_start

    try:
        client = Client()

        # 1) Load home page (GET)
        client.get(reverse('home'))

        # 2) Submit form (POST)
        response = client.post(reverse('home'), data={
            'repo_url': repo_url,
            'access_token': token,
            'commit_limit': commit_limit,
        }, follow=True)

        # Expect redirect to analysis detail page
        assert response.status_code == 200, f"Unexpected status: {response.status_code}"

        # Get the latest analysis created
        analysis = FDSAnalysis.objects.order_by('-id').first()
        assert analysis is not None, "No analysis record found."
        assert analysis.status == 'completed', f"Analysis status is {analysis.status}"

        # Ensure developer scores exist
        dev_count = DeveloperScore.objects.filter(analysis=analysis).count()
        assert dev_count > 0, "No developer scores stored."

        # 3) Fetch the analysis detail page HTML and save it
        detail_url = reverse('analysis_detail', kwargs={'analysis_id': analysis.id})
        page = client.get(detail_url)
        assert page.status_code == 200, f"Detail page status {page.status_code}"

        out_dir = PROJECT_ROOT / 'e2e_output'
        out_dir.mkdir(exist_ok=True)
        out_file = out_dir / f'analysis_{analysis.id}.html'
        out_file.write_bytes(page.content)

        return out_file
    finally:
        # Restore original behavior
        FDSAnalysisService.start_analysis = original_start


if __name__ == '__main__':
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print('Error: set GITHUB_TOKEN environment variable.')
        sys.exit(2)

    output = run_e2e(
        repo_url='https://github.com/torvalds/linux',
        token=token,
        commit_limit=50,
    )
    print(f'SUCCESS. Saved analysis detail page to: {output}')

