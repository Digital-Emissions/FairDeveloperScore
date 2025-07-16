import requests
import pandas as pd
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

BASE_URL = "https://issues.apache.org/jira"
PROJECT_KEY = "KAFKA"
DAYS = 90  # Extended to 90 days to find worklogs
OUTPUT_CSV = "../../../data/jira_project_data/kafka_worklogs.csv"

def get_recent_issues():
    date_str = (pd.Timestamp.now() - pd.Timedelta(days=DAYS)).strftime("%Y-%m-%d")
    
    # Try multiple JQL queries to find worklogs
    jql_queries = [
        f'project = {PROJECT_KEY} AND worklogDate >= "{date_str}"',  # Primary: issues with worklog in date range
        f'project = {PROJECT_KEY} AND updated >= "{date_str}" AND timespent > 0',  # Secondary: issues with time spent
        f'project = {PROJECT_KEY} AND updated >= "{date_str}"',  # Fallback: all recent issues
    ]
    
    all_issues = []
    
    for i, jql in enumerate(jql_queries):
        logging.info(f"Trying JQL query {i+1}/3: {jql}")
        url = f"{BASE_URL}/rest/api/2/search"
        issues = []
        start_at = 0
        
        try:
            while True:
                params = {
                    "jql": jql,
                    "fields": "key,worklog,timespent",
                    "startAt": start_at,
                    "maxResults": 50,
                    "expand": "worklog"
                }
                resp = requests.get(url, params=params, timeout=60)
                resp.raise_for_status()
                data = resp.json()
                batch = data.get("issues", [])
                issues.extend(batch)
                if start_at + data.get("maxResults", 50) >= data.get("total", 0):
                    break
                start_at += data.get("maxResults", 50)
                time.sleep(0.2)
            
            # Check if we found any worklogs
            worklog_count = 0
            for issue in issues:
                worklogs = issue.get("fields", {}).get("worklog", {}).get("worklogs", [])
                worklog_count += len(worklogs)
            
            logging.info(f"Query {i+1} found {len(issues)} issues with {worklog_count} worklogs")
            
            if worklog_count > 0:
                all_issues.extend(issues)
                break  # Found worklogs, stop trying other queries
            elif i == len(jql_queries) - 1:
                # Last query, use these issues even if no worklogs
                all_issues.extend(issues)
                
        except Exception as e:
            logging.error(f"Query {i+1} failed: {str(e)}")
            if i == len(jql_queries) - 1:
                raise  # Re-raise on last query
    
    return all_issues

def flatten_worklog(worklog, issue_key):
    # Handle comment field which can be either a string or a complex object
    comment = ""
    if worklog.get("comment"):
        comment_data = worklog.get("comment")
        if isinstance(comment_data, str):
            comment = comment_data
        elif isinstance(comment_data, dict):
            # Try to extract text from complex comment structure
            try:
                content = comment_data.get("content", [])
                if content and isinstance(content, list) and len(content) > 0:
                    first_content = content[0]
                    if isinstance(first_content, dict):
                        inner_content = first_content.get("content", [])
                        if inner_content and isinstance(inner_content, list) and len(inner_content) > 0:
                            comment = inner_content[0].get("text", "")
            except (AttributeError, IndexError, KeyError):
                comment = str(comment_data)  # Fallback to string representation
    
    return {
        "issue_key": issue_key,
        "worklog_id": worklog.get("id"),
        "author": worklog.get("author", {}).get("displayName"),
        "time_spent_seconds": worklog.get("timeSpentSeconds"),
        "time_spent": worklog.get("timeSpent"),
        "started": worklog.get("started"),
        "created": worklog.get("created"),
        "updated": worklog.get("updated"),
        "comment": comment
    }

def main():
    logging.info(f"Searching for worklogs in Kafka project over the last {DAYS} days...")
    issues = get_recent_issues()
    all_worklogs = []
    issues_with_worklogs = 0
    
    for issue in issues:
        issue_key = issue.get("key")
        worklogs = issue.get("fields", {}).get("worklog", {}).get("worklogs", [])
        if worklogs:
            issues_with_worklogs += 1
            logging.info(f"Found {len(worklogs)} worklogs in issue {issue_key}")
        for worklog in worklogs:
            all_worklogs.append(flatten_worklog(worklog, issue_key))
    
    logging.info(f"Processed {len(issues)} issues, {issues_with_worklogs} had worklogs")
    
    if not all_worklogs:
        logging.warning(f"No worklogs found in the last {DAYS} days. Creating empty CSV file.")
        # Create empty DataFrame with expected columns
        df = pd.DataFrame(columns=["issue_key", "worklog_id", "author", "time_spent_seconds", "time_spent", "started", "created", "updated", "comment"])
    else:
        df = pd.DataFrame(all_worklogs)
        logging.info(f"Successfully collected {len(all_worklogs)} worklog entries from {issues_with_worklogs} issues")
    
    df.to_csv(OUTPUT_CSV, index=False)
    logging.info(f"Saved {len(df)} worklog entries to {OUTPUT_CSV}")

if __name__ == "__main__":
    main() 