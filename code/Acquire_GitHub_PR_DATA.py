from github import Github
import csv
import time


TOKEN = "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" 
with open("top_500_repos.txt", "r") as f:
    REPO_LIST = [line.strip() for line in f if line.strip()]

MAX_PR_PER_REPO = 100  # limit the number of PRs to process, avoid API limit

g = Github(TOKEN)
results = []


for full_repo_name in REPO_LIST:
    print(f" Processing {full_repo_name}")
    try:
        repo = g.get_repo(full_repo_name)
        total = 0
        passed = 0
        pr_count = 0

        for pr in repo.get_pulls(state='closed'):
            if not pr.is_merged():
                continue

            total += 1
            pr_count += 1
            reviews = pr.get_reviews()

            # check if there is any review that requires changes
            if all(r.state != "CHANGES_REQUESTED" for r in reviews):
                passed += 1

            if pr_count >= MAX_PR_PER_REPO:
                break

            time.sleep(0.5)  # avoid rate limit

        rate = passed / total if total > 0 else 0
        results.append({
            "repo": full_repo_name,
            "total_merged_prs": total,
            "passed_first_try": passed,
            "pass_rate": round(rate * 100, 2)
        })

    except Exception as e:
        print(f"❌ Error processing {full_repo_name}: {e}")
        results.append({
            "repo": full_repo_name,
            "total_merged_prs": 0,
            "passed_first_try": 0,
            "pass_rate": 0.0,
            "error": str(e)
        })

# save to csv file
output_file = "data/pr_data/pr_pass_rate_results_top_500.csv"
with open(output_file, mode='w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)

print(f"\n✅ Finished. Results saved to {output_file}")
