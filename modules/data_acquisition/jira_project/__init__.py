"""
Jira Project Data Acquisition Module

This module provides functionality to collect data from Jira projects
for developer productivity measurement and analysis.
"""

__version__ = "1.0.0"
__author__ = "Dev Productivity Team"

from .jira_client import JiraClient
from .data_collector import JiraDataCollector
from .kafka_collector import KafkaJiraCollector

__all__ = ["JiraClient", "JiraDataCollector", "KafkaJiraCollector"] 