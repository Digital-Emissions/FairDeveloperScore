"""
Jira API Client with authentication and rate limiting.

This module provides a robust client for interacting with Jira REST API
with proper authentication, rate limiting, and error handling.
"""

import os
import time
import requests
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class JiraConfig:
    """Configuration for Jira API client."""
    base_url: str
    username: Optional[str] = None
    token: Optional[str] = None
    rate_limit_delay: float = 0.2  # 200ms between requests
    max_results: int = 100
    timeout: int = 30


class RateLimiter:
    """Simple rate limiter to avoid hitting API limits."""
    
    def __init__(self, delay: float = 0.2):
        self.delay = delay
        self.last_request = 0.0
    
    def wait(self):
        """Wait if necessary to respect rate limits."""
        now = time.time()
        time_since_last = now - self.last_request
        if time_since_last < self.delay:
            time.sleep(self.delay - time_since_last)
        self.last_request = time.time()


class JiraAPIError(Exception):
    """Custom exception for Jira API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[requests.Response] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class JiraClient:
    """
    Jira API client with authentication and rate limiting.
    
    Supports both anonymous access (for public projects like Apache Kafka)
    and authenticated access with username/token.
    """
    
    def __init__(self, config: JiraConfig):
        self.config = config
        self.rate_limiter = RateLimiter(config.rate_limit_delay)
        self.session = requests.Session()
        
        # Set up authentication if credentials provided
        if config.username and config.token:
            auth_string = f"{config.username}:{config.token}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            self.session.headers.update({
                'Authorization': f'Basic {auth_b64}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
            logger.info("Configured authenticated access")
        else:
            self.session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
            logger.info("Configured anonymous access")
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make a rate-limited request to the Jira API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            **kwargs: Additional arguments for requests
            
        Returns:
            requests.Response object
            
        Raises:
            JiraAPIError: If the request fails
        """
        self.rate_limiter.wait()
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.config.timeout,
                **kwargs
            )
            
            if response.status_code >= 400:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"API request failed: {error_msg}")
                raise JiraAPIError(error_msg, response.status_code, response)
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {str(e)}")
            raise JiraAPIError(f"Request failed: {str(e)}")
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a GET request to a Jira API endpoint.
        
        Args:
            endpoint: API endpoint (e.g., '/rest/api/3/search')
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        url = f"{self.config.base_url}{endpoint}"
        response = self._make_request('GET', url, params=params or {})
        return response.json()
    
    def get_paginated(self, endpoint: str, params: Optional[Dict] = None, 
                     start_at_key: str = 'startAt', 
                     max_results_key: str = 'maxResults',
                     items_key: str = 'issues') -> List[Dict[str, Any]]:
        """
        Get all results from a paginated API endpoint.
        
        Args:
            endpoint: API endpoint
            params: Base query parameters
            start_at_key: Parameter name for pagination start
            max_results_key: Parameter name for page size
            items_key: Key in response containing the items
            
        Returns:
            List of all items from all pages
        """
        all_items = []
        start_at = 0
        params = params or {}
        
        while True:
            current_params = params.copy()
            current_params.update({
                start_at_key: start_at,
                max_results_key: self.config.max_results
            })
            
            logger.info(f"Fetching page starting at {start_at}")
            response_data = self.get(endpoint, current_params)
            
            # Extract items using the specified key
            if items_key in response_data:
                items = response_data[items_key]
            elif 'values' in response_data:  # Alternative key for some endpoints
                items = response_data['values']
            else:
                items = response_data.get('results', [])
            
            all_items.extend(items)
            
            # Check if we have more pages
            total = response_data.get('total', len(items))
            max_results = response_data.get('maxResults', self.config.max_results)
            
            if start_at + max_results >= total:
                break
                
            start_at += max_results
        
        logger.info(f"Retrieved {len(all_items)} total items")
        return all_items
    
    def search_issues(self, jql: str, fields: Optional[List[str]] = None, 
                     expand: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Search for issues using JQL.
        
        Args:
            jql: JQL query string
            fields: List of fields to include in response
            expand: List of additional data to expand
            
        Returns:
            List of issue dictionaries
        """
        params = {'jql': jql}
        
        if fields:
            params['fields'] = ','.join(fields)
        
        if expand:
            params['expand'] = ','.join(expand)
        
        logger.info(f"Searching issues with JQL: {jql}")
        return self.get_paginated('/rest/api/2/search', params)
    
    def get_issue(self, issue_key: str, expand: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get detailed information for a specific issue.
        
        Args:
            issue_key: Issue key (e.g., 'KAFKA-1234')
            expand: List of additional data to expand
            
        Returns:
            Issue data dictionary
        """
        endpoint = f'/rest/api/2/issue/{issue_key}'
        params = {}
        
        if expand:
            params['expand'] = ','.join(expand)
        
        return self.get(endpoint, params)
    
    def get_fields(self) -> List[Dict[str, Any]]:
        """
        Get all available fields in the Jira instance.
        
        Returns:
            List of field definitions
        """
        logger.info("Retrieving field definitions")
        return self.get('/rest/api/2/field')
    
    def get_boards(self, project_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all boards, optionally filtered by project.
        
        Args:
            project_key: Optional project key to filter boards
            
        Returns:
            List of board dictionaries
        """
        params = {}
        if project_key:
            params['projectKeyOrId'] = project_key
        
        logger.info(f"Retrieving boards for project: {project_key or 'all'}")
        return self.get_paginated('/rest/agile/1.0/board', params, items_key='values')
    
    def get_sprints(self, board_id: int, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get sprints for a specific board.
        
        Args:
            board_id: Board ID
            state: Optional state filter (active, closed, future)
            
        Returns:
            List of sprint dictionaries
        """
        endpoint = f'/rest/agile/1.0/board/{board_id}/sprint'
        params = {}
        
        if state:
            params['state'] = state
        
        logger.info(f"Retrieving sprints for board {board_id}")
        return self.get_paginated(endpoint, params, items_key='values')
    
    def get_sprint_issues(self, board_id: int, sprint_id: int) -> List[Dict[str, Any]]:
        """
        Get all issues in a specific sprint.
        
        Args:
            board_id: Board ID
            sprint_id: Sprint ID
            
        Returns:
            List of issue dictionaries
        """
        endpoint = f'/rest/agile/1.0/board/{board_id}/sprint/{sprint_id}/issue'
        logger.info(f"Retrieving issues for sprint {sprint_id}")
        return self.get_paginated(endpoint, items_key='issues')
    
    def get_issue_worklogs(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Get worklogs for a specific issue.
        
        Args:
            issue_key: Issue key
            
        Returns:
            List of worklog dictionaries
        """
        endpoint = f'/rest/api/2/issue/{issue_key}/worklog'
        response = self.get(endpoint)
        return response.get('worklogs', []) 