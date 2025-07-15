# Jira Project Data Acquisition Module

This module provides comprehensive data collection capabilities for Jira projects, specifically designed for developer productivity measurement and analysis. It includes specialized support for Apache Kafka project data collection.

## Features

- **Comprehensive Data Collection**: Issues, worklogs, status history, sprints, and boards
- **Field Discovery**: Automatic detection of custom fields like Story Points and Epic Links
- **Rate Limiting**: Respectful API usage with configurable delays
- **Error Handling**: Robust error handling and retry mechanisms
- **Multiple Output Formats**: CSV export with detailed summaries
- **Apache Kafka Support**: Pre-configured for Apache Kafka Jira project

## Architecture

### Core Components

1. **JiraClient** (`jira_client.py`): Low-level API client with authentication and rate limiting
2. **JiraDataCollector** (`data_collector.py`): High-level data collection and processing
3. **KafkaJiraCollector** (`kafka_collector.py`): Specialized collector for Apache Kafka project
4. **FieldDiscovery**: Automatic custom field mapping
5. **DataProcessor**: Data normalization and export utilities

## Usage

### Basic Usage

```python
from data_acquisition.jira_project import KafkaJiraCollector

# Initialize collector
collector = KafkaJiraCollector(output_dir="data")

# Collect sample data
results = collector.collect_sample_data(days=7)

# Full data collection
results = collector.collect_kafka_performance_data(days=14)
```

### Command Line Interface

```bash
# Field validation
python run_kafka_collection.py --validate

# Sample data collection (7 days max)
python run_kafka_collection.py --sample

# Full data collection
python run_kafka_collection.py --days 14

# Custom output directory
python run_kafka_collection.py --output-dir /path/to/data --days 30
```

## Data Collected

### Issue Data (`kafka_recent_issues.csv`)
- Basic issue information (key, created, updated, status, etc.)
- Story Points and Epic Links (if available)
- Components, labels, and fix versions
- Assignee and reporter information

### Status History (`kafka_status_history.csv`)
- Status change timeline for CSI (Return-to-work ratio) calculation
- Change author and timestamps
- From/to status transitions

### Bug and Improvement Data (`kafka_bugs_improvements.csv`)
- Filtered view of issues for quality metrics
- Bug reports and improvement requests
- Feature development tracking

### Worklog Data (when available)
- Time tracking information
- Developer work patterns
- Time spent on issues

### Sprint Data (when available)
- Sprint planning and execution data
- Story points commitment vs completion
- Predictability Score (PS) calculation

## Key Metrics Supported

Based on the four-layer indicator hierarchy:

### 1. Commit ⇢ Batch
- **Torque Batch Size**: Collected from GitHub (not Jira)

### 2. Batch ⇢ Issue  
- **CTL (Commit-to-Ticket Lead Time)**: Using issue creation and resolution dates

### 3. Issue ⇢ Sprint/Iteration
- **CSI (Return-to-work ratio)**: Using status history and worklog data
- **Issue Type/Priority**: Value weighting for different issue types

### 4. Sprint ⇢ Release
- **PS (Predictability Score)**: Completed vs committed story points

## Configuration

### Apache Kafka Project (Default)
- Base URL: `https://issues.apache.org/jira`
- Project Key: `KAFKA`
- API Version: 2 (Apache uses older Jira version)
- Rate Limit: 0.5 seconds between requests
- Batch Size: 50 items per request

### Custom Configuration

```python
from data_acquisition.jira_project import JiraClient, JiraConfig, JiraDataCollector

config = JiraConfig(
    base_url="https://your-jira-instance.com",
    username="your-username",  # Optional for public projects
    token="your-api-token",    # Optional for public projects
    rate_limit_delay=0.2,
    max_results=100,
    timeout=30
)

client = JiraClient(config)
collector = JiraDataCollector(client, output_dir="data")
```

## Data Output

### CSV Files Generated
- `kafka_recent_issues.csv`: Recent issues (configurable time range)
- `kafka_bugs_improvements.csv`: Bugs and improvements specifically
- `kafka_status_history.csv`: Status change timeline
- `kafka_worklogs.csv`: Time tracking data (if available)
- `kafka_boards.csv`: Board information (if accessible)
- `kafka_sprints.csv`: Sprint data (if accessible)
- `kafka_sprint_issues.csv`: Issues in sprints (if accessible)

### Summary Files
- `kafka_collection_summary.json`: Collection metadata and statistics
- `kafka_field_validation.json`: Field discovery results

## Error Handling

The module includes comprehensive error handling:

- **Authentication Issues**: Graceful fallback for public vs private projects
- **Rate Limiting**: Automatic delays and respect for API limits
- **Network Issues**: Retry mechanisms and timeout handling
- **Data Validation**: Field existence checking and data type validation

## Recent Collection Results

From the latest Apache Kafka data collection (July 15, 2025):

- **Total Records**: 487
- **Recent Issues**: 188 (last 14 days)
- **Bugs/Improvements**: 116 
- **Status Changes**: 183
- **Custom Fields Found**: 2 (Story Points, Epic Link)
- **Total Issues in Project**: 18,243+

## Dependencies

- `requests`: HTTP client for API calls
- `pandas`: Data processing and CSV export
- `python-dotenv`: Environment variable management (optional)

## Installation

```bash
pip install requests pandas python-dotenv
```

## Best Practices

1. **Rate Limiting**: Always respect API rate limits, especially for public projects
2. **Data Privacy**: Be mindful of data sensitivity when collecting from private projects
3. **Incremental Collection**: Use date filters to avoid re-collecting unchanged data
4. **Error Monitoring**: Monitor logs for API issues and authentication problems
5. **Data Validation**: Verify field mappings before large-scale collection

## Extending for Other Projects

To adapt this module for other Jira projects:

1. Create a new collector class similar to `KafkaJiraCollector`
2. Update base URL and project key
3. Adjust custom field mappings as needed
4. Modify JQL queries for project-specific requirements
5. Update rate limiting and batch sizes based on API limits

## Troubleshooting

### Common Issues

1. **401 Authentication Error**: Some endpoints require authentication even for public projects
2. **Rate Limiting**: Increase delays if getting rate limit errors
3. **Field Not Found**: Custom field IDs vary between Jira instances
4. **Large Data Sets**: Use smaller time ranges for initial testing

### Debug Mode

Enable verbose logging:

```bash
python run_kafka_collection.py --verbose --sample
```

## Future Enhancements

- Support for additional Jira Cloud features
- Integration with GitHub data for complete CTL calculation  
- Automated metric calculation and reporting
- Real-time data streaming capabilities
- Enhanced custom field detection 