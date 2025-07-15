"""
Jira Data Collector with field discovery and data processing.

This module handles the collection, processing, and export of Jira data
for developer productivity metrics calculation.
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import re
from pathlib import Path

from .jira_client import JiraClient, JiraConfig

logger = logging.getLogger(__name__)


class FieldDiscovery:
    """Utility class for discovering and mapping Jira custom fields."""
    
    def __init__(self, client: JiraClient):
        self.client = client
        self._field_cache = None
    
    def get_fields(self) -> List[Dict[str, Any]]:
        """Get all fields, caching the result."""
        if self._field_cache is None:
            self._field_cache = self.client.get_fields()
        return self._field_cache
    
    def find_story_points_field(self) -> Optional[str]:
        """
        Find the Story Points custom field ID.
        
        Returns:
            Field ID (e.g., 'customfield_10016') or None if not found
        """
        fields = self.get_fields()
        
        # Common patterns for Story Points field names
        story_points_patterns = [
            r'story\s*points?',
            r'points?',
            r'estimate',
            r'effort'
        ]
        
        for field in fields:
            field_name = field.get('name', '').lower()
            for pattern in story_points_patterns:
                if re.search(pattern, field_name):
                    logger.info(f"Found Story Points field: {field['name']} ({field['id']})")
                    return field['id']
        
        logger.warning("Story Points field not found")
        return None
    
    def find_epic_link_field(self) -> Optional[str]:
        """Find the Epic Link custom field ID."""
        fields = self.get_fields()
        
        for field in fields:
            field_name = field.get('name', '').lower()
            if 'epic' in field_name and 'link' in field_name:
                logger.info(f"Found Epic Link field: {field['name']} ({field['id']})")
                return field['id']
        
        return None
    
    def get_custom_field_mapping(self) -> Dict[str, str]:
        """
        Get mapping of common custom field names to their IDs.
        
        Returns:
            Dictionary mapping field names to IDs
        """
        mapping = {}
        
        story_points = self.find_story_points_field()
        if story_points:
            mapping['story_points'] = story_points
        
        epic_link = self.find_epic_link_field()
        if epic_link:
            mapping['epic_link'] = epic_link
        
        return mapping


class DataProcessor:
    """Processes raw Jira data into structured formats for analysis."""
    
    @staticmethod
    def normalize_issue_data(issues: List[Dict[str, Any]], 
                           custom_fields: Dict[str, str]) -> pd.DataFrame:
        """
        Normalize issue data into a flat structure.
        
        Args:
            issues: Raw issue data from Jira API
            custom_fields: Mapping of custom field names to IDs
            
        Returns:
            Normalized DataFrame
        """
        normalized_data = []
        
        for issue in issues:
            fields = issue.get('fields', {})
            
            # Extract basic fields
            row = {
                'key': issue.get('key'),
                'id': issue.get('id'),
                'created': fields.get('created'),
                'updated': fields.get('updated'),
                'resolution_date': fields.get('resolutiondate'),
                'summary': fields.get('summary'),
                'description': fields.get('description'),
                'status': fields.get('status', {}).get('name'),
                'status_category': fields.get('status', {}).get('statusCategory', {}).get('name'),
                'issue_type': fields.get('issuetype', {}).get('name'),
                'priority': fields.get('priority', {}).get('name'),
                'assignee': fields.get('assignee', {}).get('displayName') if fields.get('assignee') else None,
                'reporter': fields.get('reporter', {}).get('displayName') if fields.get('reporter') else None,
                'project_key': fields.get('project', {}).get('key'),
                'project_name': fields.get('project', {}).get('name'),
            }
            
            # Extract custom fields
            if 'story_points' in custom_fields:
                row['story_points'] = fields.get(custom_fields['story_points'])
            
            if 'epic_link' in custom_fields:
                row['epic_link'] = fields.get(custom_fields['epic_link'])
            
            # Extract components
            components = fields.get('components', [])
            row['components'] = ','.join([comp.get('name', '') for comp in components])
            
            # Extract labels
            labels = fields.get('labels', [])
            row['labels'] = ','.join(labels)
            
            # Extract fix versions
            fix_versions = fields.get('fixVersions', [])
            row['fix_versions'] = ','.join([ver.get('name', '') for ver in fix_versions])
            
            normalized_data.append(row)
        
        return pd.DataFrame(normalized_data)
    
    @staticmethod
    def extract_worklog_data(issues: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Extract worklog data from issues.
        
        Args:
            issues: Issues with worklog data expanded
            
        Returns:
            DataFrame with worklog entries
        """
        worklog_data = []
        
        for issue in issues:
            issue_key = issue.get('key')
            worklogs = issue.get('fields', {}).get('worklog', {}).get('worklogs', [])
            
            for worklog in worklogs:
                row = {
                    'issue_key': issue_key,
                    'worklog_id': worklog.get('id'),
                    'author': worklog.get('author', {}).get('displayName'),
                    'time_spent_seconds': worklog.get('timeSpentSeconds'),
                    'started': worklog.get('started'),
                    'created': worklog.get('created'),
                    'updated': worklog.get('updated'),
                    'comment': worklog.get('comment', {}).get('content', [{}])[0].get('content', [{}])[0].get('text', '') if worklog.get('comment') else ''
                }
                worklog_data.append(row)
        
        return pd.DataFrame(worklog_data)
    
    @staticmethod
    def extract_changelog_data(issues: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Extract changelog/history data from issues.
        
        Args:
            issues: Issues with changelog data expanded
            
        Returns:
            DataFrame with status change history
        """
        changelog_data = []
        
        for issue in issues:
            issue_key = issue.get('key')
            changelog = issue.get('changelog', {})
            histories = changelog.get('histories', [])
            
            for history in histories:
                created = history.get('created')
                author = history.get('author', {}).get('displayName')
                
                for item in history.get('items', []):
                    if item.get('field') == 'status':
                        row = {
                            'issue_key': issue_key,
                            'change_date': created,
                            'author': author,
                            'field': item.get('field'),
                            'from_string': item.get('fromString'),
                            'to_string': item.get('toString'),
                            'from_id': item.get('from'),
                            'to_id': item.get('to')
                        }
                        changelog_data.append(row)
        
        return pd.DataFrame(changelog_data)
    
    @staticmethod
    def normalize_sprint_data(sprints: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Normalize sprint data.
        
        Args:
            sprints: Raw sprint data from Jira API
            
        Returns:
            Normalized DataFrame
        """
        normalized_data = []
        
        for sprint in sprints:
            row = {
                'sprint_id': sprint.get('id'),
                'sprint_name': sprint.get('name'),
                'state': sprint.get('state'),
                'board_id': sprint.get('originBoardId'),
                'start_date': sprint.get('startDate'),
                'end_date': sprint.get('endDate'),
                'complete_date': sprint.get('completeDate'),
                'goal': sprint.get('goal')
            }
            normalized_data.append(row)
        
        return pd.DataFrame(normalized_data)


class JiraDataCollector:
    """
    Main data collector for Jira project data.
    
    Orchestrates the collection of issues, sprints, and related data
    for developer productivity analysis.
    """
    
    def __init__(self, client: JiraClient, output_dir: str = 'data'):
        self.client = client
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize field discovery
        self.field_discovery = FieldDiscovery(client)
        self.custom_fields = self.field_discovery.get_custom_field_mapping()
        
        logger.info(f"Initialized data collector with custom fields: {self.custom_fields}")
    
    def collect_recent_issues(self, project_key: str, days: int = 30, 
                            additional_jql: str = "") -> pd.DataFrame:
        """
        Collect issues updated in the last N days.
        
        Args:
            project_key: Jira project key (e.g., 'KAFKA')
            days: Number of days to look back
            additional_jql: Additional JQL conditions
            
        Returns:
            DataFrame with issue data
        """
        # Build JQL query
        date_str = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        jql = f'project = {project_key} AND updated >= "{date_str}"'
        
        if additional_jql:
            jql += f' AND ({additional_jql})'
        
        # Define fields to retrieve
        fields = [
            'key', 'created', 'updated', 'resolutiondate', 'summary', 'description',
            'status', 'issuetype', 'priority', 'assignee', 'reporter', 'project',
            'components', 'labels', 'fixVersions', 'worklog'
        ]
        
        # Add custom fields
        if 'story_points' in self.custom_fields:
            fields.append(self.custom_fields['story_points'])
        if 'epic_link' in self.custom_fields:
            fields.append(self.custom_fields['epic_link'])
        
        # Search for issues with expanded data
        expand = ['changelog', 'worklog']
        issues = self.client.search_issues(jql, fields, expand)
        
        logger.info(f"Collected {len(issues)} issues from project {project_key}")
        
        # Normalize the data
        df_issues = DataProcessor.normalize_issue_data(issues, self.custom_fields)
        
        return df_issues
    
    def collect_worklog_data(self, project_key: str, days: int = 30) -> pd.DataFrame:
        """
        Collect worklog data for recent issues.
        
        Args:
            project_key: Jira project key
            days: Number of days to look back
            
        Returns:
            DataFrame with worklog data
        """
        # Get issues with worklog data
        date_str = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        jql = f'project = {project_key} AND updated >= "{date_str}" AND worklogDate >= "{date_str}"'
        
        fields = ['key', 'worklog']
        expand = ['worklog']
        
        issues = self.client.search_issues(jql, fields, expand)
        
        # Extract worklog data
        df_worklogs = DataProcessor.extract_worklog_data(issues)
        
        logger.info(f"Collected {len(df_worklogs)} worklog entries")
        return df_worklogs
    
    def collect_status_history(self, project_key: str, days: int = 30) -> pd.DataFrame:
        """
        Collect status change history for issues.
        
        Args:
            project_key: Jira project key
            days: Number of days to look back
            
        Returns:
            DataFrame with status change history
        """
        date_str = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        jql = f'project = {project_key} AND updated >= "{date_str}"'
        
        fields = ['key', 'status']
        expand = ['changelog']
        
        issues = self.client.search_issues(jql, fields, expand)
        
        # Extract changelog data
        df_changelog = DataProcessor.extract_changelog_data(issues)
        
        logger.info(f"Collected {len(df_changelog)} status change records")
        return df_changelog
    
    def collect_board_and_sprint_data(self, project_key: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Collect board, sprint, and sprint issue data.
        
        Args:
            project_key: Jira project key
            
        Returns:
            Tuple of (boards_df, sprints_df, sprint_issues_df)
        """
        # Get boards for the project
        boards = self.client.get_boards(project_key)
        df_boards = pd.DataFrame(boards)
        
        if df_boards.empty:
            logger.warning(f"No boards found for project {project_key}")
            return df_boards, pd.DataFrame(), pd.DataFrame()
        
        # Collect sprint data for each board
        all_sprints = []
        all_sprint_issues = []
        
        for board in boards:
            board_id = board['id']
            board_name = board['name']
            
            logger.info(f"Processing board: {board_name} (ID: {board_id})")
            
            # Get sprints for this board (active and closed)
            sprints = self.client.get_sprints(board_id, state='active,closed')
            
            for sprint in sprints:
                sprint['board_id'] = board_id
                all_sprints.append(sprint)
                
                # Get issues for this sprint
                sprint_id = sprint['id']
                try:
                    sprint_issues = self.client.get_sprint_issues(board_id, sprint_id)
                    
                    for issue in sprint_issues:
                        issue_data = {
                            'board_id': board_id,
                            'sprint_id': sprint_id,
                            'issue_key': issue.get('key'),
                            'issue_id': issue.get('id'),
                            'issue_type': issue.get('fields', {}).get('issuetype', {}).get('name'),
                            'status': issue.get('fields', {}).get('status', {}).get('name'),
                            'assignee': issue.get('fields', {}).get('assignee', {}).get('displayName') if issue.get('fields', {}).get('assignee') else None,
                        }
                        
                        # Add story points if available
                        if 'story_points' in self.custom_fields:
                            story_points_field = self.custom_fields['story_points']
                            issue_data['story_points'] = issue.get('fields', {}).get(story_points_field)
                        
                        all_sprint_issues.append(issue_data)
                        
                except Exception as e:
                    logger.error(f"Error collecting issues for sprint {sprint_id}: {str(e)}")
        
        # Normalize sprint data
        df_sprints = DataProcessor.normalize_sprint_data(all_sprints)
        df_sprint_issues = pd.DataFrame(all_sprint_issues)
        
        logger.info(f"Collected {len(df_sprints)} sprints and {len(df_sprint_issues)} sprint-issue relationships")
        
        return df_boards, df_sprints, df_sprint_issues
    
    def export_to_csv(self, dataframes: Dict[str, pd.DataFrame], prefix: str = ""):
        """
        Export DataFrames to CSV files.
        
        Args:
            dataframes: Dictionary mapping filename to DataFrame
            prefix: Optional prefix for filenames
        """
        for name, df in dataframes.items():
            if df.empty:
                logger.warning(f"Skipping empty DataFrame: {name}")
                continue
                
            filename = f"{prefix}_{name}.csv" if prefix else f"{name}.csv"
            filepath = self.output_dir / filename
            
            df.to_csv(filepath, index=False, encoding='utf-8')
            logger.info(f"Exported {len(df)} records to {filepath}")
    
    def run_full_collection(self, project_key: str, days: int = 30) -> Dict[str, pd.DataFrame]:
        """
        Run a complete data collection for a project.
        
        Args:
            project_key: Jira project key
            days: Number of days to look back for issues
            
        Returns:
            Dictionary of collected DataFrames
        """
        logger.info(f"Starting full data collection for project {project_key}")
        
        results = {}
        
        try:
            # Collect issue data
            logger.info("Collecting issue data...")
            results['issues'] = self.collect_recent_issues(project_key, days)
            
            # Collect worklog data
            logger.info("Collecting worklog data...")
            results['worklogs'] = self.collect_worklog_data(project_key, days)
            
            # Collect status history
            logger.info("Collecting status history...")
            results['status_history'] = self.collect_status_history(project_key, days)
            
            # Collect board and sprint data
            logger.info("Collecting board and sprint data...")
            boards_df, sprints_df, sprint_issues_df = self.collect_board_and_sprint_data(project_key)
            results['boards'] = boards_df
            results['sprints'] = sprints_df
            results['sprint_issues'] = sprint_issues_df
            
            # Export all data to CSV
            self.export_to_csv(results, prefix=project_key.lower())
            
            logger.info("Full data collection completed successfully")
            
        except Exception as e:
            logger.error(f"Error during data collection: {str(e)}")
            raise
        
        return results 