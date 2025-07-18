import pandas as pd

df = pd.read_csv("data/developer_profile_total/merged_developer_profile.csv")

print(df.describe())

mean_val = df['pr_acceptance_rate'].mean()
df['pr_acceptance_rate'] = df.apply(
    lambda x: 0 if x['total_prs'] == 0 else (x['pr_acceptance_rate'] if pd.notna(x['pr_acceptance_rate']) else mean_val),
    axis=1
)

df.to_csv("data/developer_profile_total/merged_developer_profile_cleaned.csv", index=False)