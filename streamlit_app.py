import streamlit as st
import pandas as pd
import datetime
from github import Github
import matplotlib.pyplot as plt

st.set_page_config(page_title="GitHub Productivity Dashboard", layout="wide")
st.title("GitHub Programmer Productivity Dashboard")

# ----------------- FUNCTION: Fetch Commits -----------------
def fetch_commits(repo_full_name, token=None, days=30, output_file='commits.csv'):
    g = Github(token) if token else Github()
    repo = g.get_repo(repo_full_name)
    since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
    commits = repo.get_commits(since=since)

    data = []
    for commit in commits:
        try:
            stats = commit.stats
            data.append({
                'sha': commit.sha,
                'author': commit.author.login if commit.author else 'unknown',
                'time': commit.commit.author.date,
                'add': stats.additions,
                'del': stats.deletions,
                'total': stats.total,
                'msg': commit.commit.message.splitlines()[0] if commit.commit.message else ''
            })
        except Exception as e:
            print(f"Error processing commit {commit.sha}: {e}")

    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)
    return df

# ----------------- FUNCTION: Fetch PRs -----------------
def fetch_pull_requests(repo_full_name, token=None, output_file='pull_requests.csv'):
    g = Github(token) if token else Github()
    repo = g.get_repo(repo_full_name)
    prs = repo.get_pulls(state='all')

    data = []
    for pr in prs:
        try:
            data.append({
                'id': pr.id,
                'title': pr.title,
                'user': pr.user.login,
                'state': pr.state,
                'created_at': pr.created_at,
                'merged_at': pr.merged_at
            })
        except Exception as e:
            print(f"Error processing PR {pr.number}: {e}")

    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)
    return df

# ----------------- UI INPUT -----------------
repo = st.text_input("Enter GitHub repository (e.g., torvalds/linux):")
token = st.text_input("Enter GitHub token (optional):", type="password")

if st.button("Analyze"):
    with st.spinner("Fetching data from GitHub..."):
        df_commits = fetch_commits(repo, token, output_file="temp_commits.csv")
        df_prs = fetch_pull_requests(repo, token, output_file="temp_prs.csv")

    st.success(f" Data fetched! Total commits: {len(df_commits)}")

    # ===== Commit Analysis =====
    st.subheader(" Daily Commit Frequency")
    df_commits['date'] = pd.to_datetime(df_commits['time']).dt.date
    daily_commits = df_commits.groupby('date').size()
    st.line_chart(daily_commits)

    st.subheader(" Top Contributors")
    top_authors = df_commits['author'].value_counts().head(10)
    st.bar_chart(top_authors)

    unique_days = df_commits['date'].nunique()
    deploy_freq = round(unique_days / 30 * 100, 2)
    st.metric(" Deployment Frequency", f"{deploy_freq}%")

    # ===== PR Analysis =====
    if len(df_prs) > 0:
        st.subheader(" Pull Request Overview")
        merged_prs = df_prs[df_prs['merged_at'].notna()]
        pr_merge_rate = round(len(merged_prs) / len(df_prs) * 100, 1)
        st.metric(" PR Merge Rate", f"{pr_merge_rate}%")

        st.dataframe(df_prs.head(), use_container_width=True)

    # ===== Download Links =====
    st.download_button("Download Commit Data CSV", df_commits.to_csv(index=False), file_name="commits.csv")
    st.download_button("Download PR Data CSV", df_prs.to_csv(index=False), file_name="pull_requests.csv")
