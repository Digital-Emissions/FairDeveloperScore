# Fair Developer Score (FDS) Web Application

A Django web application that calculates Fair Developer Scores for GitHub repositories using our advanced FDS algorithm.

## Features

- 🎯 **Repository Analysis**: Input any GitHub repository URL for analysis
- 🔐 **GitHub API Integration**: Secure token-based access to GitHub data
- 📊 **Fair Developer Scoring**: Calculate FDS using our sophisticated algorithm
- 🏆 **Developer Rankings**: View top contributors with detailed metrics
- 📈 **Batch Analysis**: Understand collaborative work patterns
- 🔄 **Real-time Updates**: Monitor analysis progress in real-time
- 💾 **Result Storage**: Persistent storage of all analysis results

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
   - Explore batch-level collaboration metrics
   - Compare developers side-by-side

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

### Batch Importance
- **Scale**: Batch size and scope
- **Centrality**: Directory architectural importance
- **Complexity**: Technical difficulty assessment
- **Type**: Change classification (feature/fix/refactor)

### Final Formula
```
FDS = Developer Effort × Batch Importance
```

## Project Structure

```
fds_webapp/
├── dev_productivity/           # Main Django app
│   ├── models.py              # Database models
│   ├── views.py               # View logic
│   ├── forms.py               # Input forms
│   ├── services.py            # FDS analysis service
│   ├── templates/             # HTML templates
│   ├── fds_algorithm/         # FDS algorithm modules
│   └── torque_clustering/     # TORQUE clustering module
├── fds_webapp/                # Django project settings
└── manage.py                  # Django management script
```

## API Endpoints

- `/` - Home page with analysis form
- `/analyses/` - List all analyses
- `/analysis/<id>/` - View analysis results
- `/analysis/<id>/status/` - Get analysis status (JSON)
- `/analysis/<id>/developer/<email>/` - Developer details
- `/analysis/<id>/batch/<id>/` - Batch details
- `/analysis/<id>/compare/` - Compare developers

## Database Models

### FDSAnalysis
Stores analysis jobs and metadata:
- Repository URL and access token
- Analysis status (pending/running/completed/failed)
- Summary statistics (commits, developers, batches)
- Execution time and error handling

### DeveloperScore
Stores individual developer FDS scores:
- Fair Developer Score and components
- Effort metrics (share, scale, reach, etc.)
- Activity metrics (commits, batches, churn)

### BatchMetrics
Stores batch-level collaboration data:
- Batch composition and importance
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

## Support

For questions about the FDS algorithm or web application, please refer to the main project documentation.