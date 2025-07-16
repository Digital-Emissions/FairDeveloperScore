import requests
import pandas as pd
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

BASE_URL = "https://issues.apache.org/jira"
PROJECT_KEY = "KAFKA"
DAYS = 14
OUTPUT_CSV = "../../../data/jira_project_data/kafka_status_history.csv"

def get_recent_issues():
    date_str = (pd.Timestamp.now() - pd.Timedelta(days=DAYS)).strftime("%Y-%m-%d")
    jql = f'project = {PROJECT_KEY} AND updated >= "{date_str}"'
    url = f"{BASE_URL}/rest/api/2/search"
    issues = []
    start_at = 0
    while True:
        params = {
            "jql": jql,
            "fields": "key",
            "startAt": start_at,
            "maxResults": 50,
            "expand": "changelog"
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
    return issues

def flatten_status_history(issue):
    issue_key = issue.get("key")
    changelog = issue.get("changelog", {})
    histories = changelog.get("histories", [])
    status_changes = []
    
    for history in histories:
        created = history.get("created")
        author = history.get("author", {}).get("displayName")
        
        for item in history.get("items", []):
            if item.get("field") == "status":
                status_changes.append({
                    "issue_key": issue_key,
                    "change_date": created,
                    "author": author,
                    "field": item.get("field"),
                    "from_string": item.get("fromString"),
                    "to_string": item.get("toString"),
                    "from_id": item.get("from"),
                    "to_id": item.get("to")
                })
    
    return status_changes

def main():
    issues = get_recent_issues()
    all_status_changes = []
    for issue in issues:
        status_changes = flatten_status_history(issue)
        all_status_changes.extend(status_changes)
    
    if not all_status_changes:
        logging.warning("No status changes found.")
        return
    
    df = pd.DataFrame(all_status_changes)
    df.to_csv(OUTPUT_CSV, index=False)
    logging.info(f"Saved {len(df)} status changes to {OUTPUT_CSV}")

if __name__ == "__main__":
    main() 