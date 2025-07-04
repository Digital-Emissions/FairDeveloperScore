# Programmer Productivity Measurement

A Python-based tool for measuring programmer productivity and deployment frequency by analyzing GitHub commit data.

## Overview

This project provides tools to acquire and analyze GitHub commit data to measure software development metrics, particularly focusing on deployment frequency and commit patterns. It's designed to help teams understand their development velocity and identify areas for improvement.

## Features

- **GitHub Commit Data Acquisition**: Fetches commit data from any public GitHub repository
- **Deployment Frequency Analysis**: Calculates average commits per day over specified time periods
- **Detailed Commit Analytics**: Extracts comprehensive commit information including:
  - Commit SHA
  - Author information
  - Timestamp
  - Code changes (additions, deletions, total)
  - Commit messages
- **CSV Export**: Saves detailed commit data to CSV files for further analysis
- **Rate Limit Handling**: Supports both authenticated and unauthenticated GitHub API access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/BellowAverage/ProgrammerProductivityMeasurement.git
cd ProgrammerProductivityMeasurement
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. Install required dependencies:
```bash
pip install PyGithub pandas
```

## Usage

### Basic Usage

1. Update the repository in `AcquireGitHubCommitData.py`:
```python
repo = g.get_repo("owner/repository-name")
```

2. Optionally add your GitHub token for higher rate limits:
```python
g = Github("your_github_token_here")
```

3. Run the script:
```bash
python AcquireGitHubCommitData.py
```

### Example Output

```
deployment_frequency_in_30_days: 16.68
total_commits_in_30_days: 1501
unique_days_with_commits: 90
Collecting detailed commit data...
Processed 0 commits...
Processed 50 commits...
...
Saving 1501 commits to CSV...
Data saved to linux_commits.csv
```

## Configuration

### GitHub Authentication

For higher rate limits (5000 requests/hour vs 60), create a GitHub Personal Access Token:

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with 'repo' scope
3. Update the script:
```python
g = Github("your_token_here")
```

### Time Period

Adjust the analysis period by modifying the `days` parameter:
```python
since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
```

## Dependencies

- `PyGithub`: GitHub API client
- `pandas`: Data manipulation and CSV export
- `datetime`: Date/time handling

## File Structure

```
ProgrammerProductivityMeasurement/
├── AcquireGitHubCommitData.py  # Main script
├── README.md                   # This file
├── .gitignore                  # Git ignore rules
├── venv/                       # Virtual environment (ignored)
└── *.csv                       # Generated commit data files
```

## Output Files

The script generates CSV files containing detailed commit information:
- `sha`: Commit hash
- `author`: GitHub username of the commit author
- `time`: Commit timestamp
- `add`: Number of lines added
- `del`: Number of lines deleted
- `total`: Total lines changed
- `msg`: Commit message (first line)

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Created by BellowAverage for measuring and analyzing programmer productivity metrics. 