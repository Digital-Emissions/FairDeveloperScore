# Fair Developer Score (FDS) Web Application

A Django-based web application that analyzes GitHub repositories and computes a Fair Developer Score (FDS) per contributor. It clusters commits into meaningful Builds, evaluates Developer Effort and Build Importance, and combines them into a single interpretable score with rich, drill-down dashboards.

## Features

-  **Repository Analysis**: Input any GitHub repository URL for analysis
-  **GitHub API Integration**: Secure token-based access to GitHub data
-  **Fair Developer Scoring**: Calculate FDS using our sophisticated algorithm
-  **Developer Rankings**: View top contributors with detailed metrics
-  **Build Analysis**: Understand collaborative work patterns at the Build level
-  **Real-time Updates**: Monitor analysis progress in real-time
-  **Result Storage**: Persistent storage of all analysis results

## Quick Start

1. **Start the Django server**:
   ```bash
   cd fds_webapp
   python manage.py runserver
   ```

2. **Access the application**:
   Open your browser to `http://127.0.0.1:8000`

3. **Start an analysis**:
   - Enter a GitHub repository URL (e.g., `https://github.com/torvalds/linux`)
   - Provide your GitHub personal access token
   - Set the number of commits to analyze (recommended: 300)
   - Click "Start Analysis"

4. **View results**:
   - Monitor progress in real-time
   - View detailed FDS scores for each developer
   - Explore build-level collaboration metrics and importance
   - Open the integrated Dashboard for charts and developer cards

## GitHub Token Setup

1. Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select scopes: `repo` (or `public_repo` for public repositories only)
4. Copy the generated token (starts with `ghp_`)

## How the FDS Algorithm Works

The Fair Developer Score combines two main components:

### Developer Effort
- **Share**: Collaboration level in work batches
- **Scale**: Code size and complexity (normalized)
- **Reach**: Cross-module impact (normalized)
- **Centrality**: Architectural importance (normalized)
- **Dominance**: Leadership within batches (normalized)
- **Novelty**: New file creation (normalized)
- **Speed**: Development velocity (normalized)

### Build Importance
- **Scale**: Batch size and scope
- **Centrality**: Directory architectural importance
- **Complexity**: Technical difficulty assessment
- **Type**: Change classification (feature/fix/refactor)

### Final Formula
```
FDS = Developer Effort × Build Importance
```

## Project Structure

```
fds_webapp/
├── dev_productivity/           # Main Django app
│   ├── models.py              # Database models
│   ├── views.py               # View logic & JSON APIs (dashboard, downloads)
│   ├── forms.py               # Input forms
│   ├── services.py            # FDS analysis service (data acquisition → clustering → scoring)
│   ├── templates/             # HTML templates
│   ├── fds_algorithm/         # FDS algorithm modules (effort, importance, preprocessing)
│   └── torque_clustering/     # TORQUE clustering module
├── fds_webapp/                # Django project settings
└── manage.py                  # Django management script
```

## API Endpoints (selected)

- `/` - Home page with analysis form
- `/analyses/` - List all analyses
- `/analysis/<id>/` - View analysis results
- `/analysis/<id>/status/` - Get analysis status (JSON)
- `/analysis/<id>/developer/<email>/` - Developer details
- `/analysis/<id>/build/<build_id>/` - Build details
- `/analysis/<id>/dashboard/` - Integrated dashboard (charts and developer cards)
- `/analysis/<id>/download/` - Download all CSV artifacts as a zip

## Database Models

### FDSAnalysis
Stores analysis jobs and metadata:
- Repository URL and access token
- Analysis status (pending/running/completed/failed)
- Summary statistics (commits, developers, builds)
- Execution time and error handling

### DeveloperScore
Stores individual developer FDS scores:
- Fair Developer Score and components
- Effort metrics (share, scale, reach, etc.)
- Activity metrics (commits, batches, churn)

### BuildMetrics
Stores build-level collaboration data:
- Build composition and importance
- Contributor information
- Temporal data (start/end times)

## Administration

Access Django admin at `/admin/` to:
- View all analyses and their status
- Browse developer scores and batch metrics
- Monitor system usage and performance

## Troubleshooting

### Common Issues

1. **GitHub API Rate Limits**:
   - Ensure you're using a valid personal access token
   - Consider using GitHub Apps for higher rate limits

2. **Analysis Takes Too Long**:
   - Reduce the number of commits to analyze
   - Large repositories (1000+ commits) may take several minutes

3. **Template Not Found Errors**:
   - Ensure the templates directory exists
   - Check Django settings for template configuration

4. **ImportError for FDS Modules**:
   - Verify the FDS algorithm modules are copied correctly
   - Check Python path configuration

### Performance Tips

- Start with 100-300 commits for testing
- Use repositories with active development (not archived)
- Ensure stable internet connection for GitHub API calls

## Development

To modify the FDS algorithm:
1. Edit files in `dev_productivity/fds_algorithm/`
2. Restart the Django server
3. Test with a small repository first

## Security Notes

- GitHub tokens are stored in the database (consider encryption for production)
- Use HTTPS in production environments
- Implement rate limiting for public deployments

## Installation & Setup

Prerequisites:
- Python 3.10+ recommended
- A GitHub Personal Access Token (classic), scope: `public_repo` or `repo`

Steps:
1. Create and activate a virtual environment
   - Windows (PowerShell):
     ```bash
     cd fds_webapp
     python -m venv .venv
     .venv\\Scripts\\Activate.ps1
     ```
   - macOS/Linux:
     ```bash
     cd fds_webapp
     python3 -m venv .venv
     source .venv/bin/activate
     ```
2. Install dependencies
   ```bash
   python -m pip install -U pip setuptools wheel
   pip install django pandas numpy requests python-dateutil pytz scipy networkx tqdm
   ```
3. Run the development server
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
4. Open `http://127.0.0.1:8000` and start an analysis

Optional utilities:
- Local pipeline script (no web):
  ```bash
  python local_fds_analyzer.py
  ```
- Bulk queue multiple large analyses in background:
  ```bash
  python run_bulk_analyses.py
  ```

## License (MIT)

Copyright (c) 2025 Fair Developer Score Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Disclaimers

- This tool provides heuristic analytics. It should not be the sole basis for HR, performance, compensation, promotion, or hiring decisions.
- Scores may be sensitive to repository structure, commit practices, and data availability. Interpret trends in context.
- GitHub API quotas and data gaps can affect completeness and timeliness of results.
- Do not store or share personal tokens or sensitive repository data in plain text. Use environment variables or secret stores in production.
- By using this software, you accept the MIT license terms above.

## Support

For questions about the FDS algorithm or web application, please refer to the main project documentation.
