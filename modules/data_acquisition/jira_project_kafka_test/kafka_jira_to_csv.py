import requests
import pandas as pd
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Jira API settings
BASE_URL = "https://issues.apache.org/jira"
PROJECT_KEY = "KAFKA"
DAYS = 14
OUTPUT_CSV = "../../../data/jira_project_data/kafka_issues.csv"

# Fields to collect
FIELDS = [
    "key", "id", "created", "updated", "resolutiondate", "summary", "description",
    "status", "issuetype", "priority", "assignee", "reporter", "project",
    "components", "labels", "fixVersions"
]

# Helper to flatten issue fields
def flatten_issue(issue):
    fields = issue.get("fields", {})
    return {
        "key": issue.get("key"),
        "id": issue.get("id"),
        "created": fields.get("created"),
        "updated": fields.get("updated"),
        "resolutiondate": fields.get("resolutiondate"),
        "summary": fields.get("summary"),
        "description": fields.get("description"),
        "status": fields.get("status", {}).get("name"),
        "status_category": fields.get("status", {}).get("statusCategory", {}).get("name"),
        "issuetype": fields.get("issuetype", {}).get("name"),
        "priority": fields.get("priority", {}).get("name"),
        "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
        "reporter": fields.get("reporter", {}).get("displayName") if fields.get("reporter") else None,
        "project_key": fields.get("project", {}).get("key"),
        "project_name": fields.get("project", {}).get("name"),
        "components": ",".join([c.get("name", "") for c in fields.get("components", [])]),
        "labels": ",".join(fields.get("labels", [])),
        "fix_versions": ",".join([v.get("name", "") for v in fields.get("fixVersions", [])]),
    }

def fetch_issues():
    date_str = (datetime.now() - timedelta(days=DAYS)).strftime("%Y-%m-%d")
    jql = f'project = {PROJECT_KEY} AND updated >= "{date_str}" AND issuetype != "Dependency upgrade"'
    url = f"{BASE_URL}/rest/api/2/search"
    params = {
        "jql": jql,
        "fields": ",".join(FIELDS),
        "maxResults": 50,
        "expand": ""
    }
    issues = []
    start_at = 0
    total = 1
    while start_at < total:
        params["startAt"] = start_at
        logging.info(f"Fetching issues {start_at}...")
        resp = requests.get(url, params=params, timeout=60)
        if resp.status_code != 200:
            logging.error(f"Failed to fetch issues: {resp.status_code} {resp.text}")
            break
        data = resp.json()
        batch = data.get("issues", [])
        issues.extend(batch)
        total = data.get("total", len(issues))
        start_at += len(batch)
        if not batch:
            break
    return issues

def main():
    issues = fetch_issues()
    if not issues:
        logging.warning("No issues fetched.")
        return
    rows = [flatten_issue(issue) for issue in issues]
    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_CSV, index=False)
    logging.info(f"Saved {len(df)} issues to {OUTPUT_CSV}")

if __name__ == "__main__":
    main() 