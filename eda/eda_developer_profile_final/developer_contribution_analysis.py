import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

# Set font for plots
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class DeveloperContributionAnalyzer:
    def __init__(self, data_path):
        """Initialize the analyzer"""
        self.df = pd.read_csv(data_path)
        self.scaler = StandardScaler()
        
    def create_contribution_metrics(self):
        """Create contribution assessment metrics"""
        # 1. Basic contribution metrics
        self.df['total_contributions'] = self.df['commit_count'] + self.df['total_prs']
        self.df['code_impact'] = self.df['avg_total_changes'] * self.df['commit_count']
        self.df['pr_impact'] = self.df['total_prs'] * self.df['pr_acceptance_rate']
        
        # 2. Efficiency metrics
        self.df['efficiency_score'] = (self.df['avg_total_changes'] * self.df['pr_acceptance_rate']) / (self.df['active_days'] + 1)
        
        # 3. Quality metrics
        self.df['quality_score'] = self.df['pr_acceptance_rate'] * (self.df['avg_msg_len'] / 100)  # Normalize message length
        
        # 4. Comprehensive contribution score
        metrics_for_score = [
            'commit_count', 'total_prs', 'avg_total_changes', 
            'pr_acceptance_rate', 'active_days', 'avg_msg_len'
        ]
        
        # Standardize metrics
        scaled_metrics = self.scaler.fit_transform(self.df[metrics_for_score])
        self.df_scaled = pd.DataFrame(scaled_metrics, columns=metrics_for_score, index=self.df.index)
        
        # Calculate comprehensive score (weighted average)
        weights = [0.2, 0.2, 0.15, 0.2, 0.15, 0.1]  # Weight distribution
        self.df['comprehensive_score'] = np.average(scaled_metrics, axis=1, weights=weights)
        
        return self.df
    
    def classify_developers(self):
        """Classify developers into different types"""
        # Classification based on comprehensive score
        self.df['contribution_level'] = pd.cut(
            self.df['comprehensive_score'], 
            bins=5, 
            labels=['Very Low', 'Low', 'Medium', 'High', 'Very High']
        )
        
        # Classification based on K-means clustering
        features_for_clustering = ['commit_count', 'total_prs', 'avg_total_changes', 'pr_acceptance_rate']
        X = self.df[features_for_clustering].values
        X_scaled = self.scaler.fit_transform(X)
        
        kmeans = KMeans(n_clusters=4, random_state=42)
        self.df['cluster'] = kmeans.fit_predict(X_scaled)
        
        # Add labels for clusters
        cluster_centers = kmeans.cluster_centers_
        cluster_scores = np.mean(cluster_centers, axis=1)
        cluster_labels = ['Core Contributor', 'Active Contributor', 'Occasional Contributor', 'New Contributor']
        
        # Sort clusters by average score
        sorted_clusters = np.argsort(cluster_scores)[::-1]
        cluster_mapping = {sorted_clusters[i]: cluster_labels[i] for i in range(len(cluster_labels))}
        self.df['developer_type'] = self.df['cluster'].map(cluster_mapping)
        
        return self.df
    
    def generate_contribution_report(self):
        """Generate contribution assessment report"""
        report = {
            'total_developers': len(self.df),
            'contribution_levels': self.df['contribution_level'].value_counts().to_dict(),
            'developer_types': self.df['developer_type'].value_counts().to_dict(),
            'top_contributors': self.df.nlargest(10, 'comprehensive_score')[['author_login', 'comprehensive_score', 'commit_count', 'total_prs', 'developer_type']].to_dict('records'),
            'metrics_summary': {
                'avg_commit_count': self.df['commit_count'].mean(),
                'avg_pr_count': self.df['total_prs'].mean(),
                'avg_acceptance_rate': self.df['pr_acceptance_rate'].mean(),
                'avg_active_days': self.df['active_days'].mean()
            }
        }
        return report
    
    def plot_contribution_analysis(self):
        """Plot contribution analysis charts"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle('Developer Contribution Analysis', fontsize=16, fontweight='bold')
        
        # 1. Contribution score distribution
        axes[0, 0].hist(self.df['comprehensive_score'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0, 0].set_title('Comprehensive Contribution Score Distribution')
        axes[0, 0].set_xlabel('Comprehensive Score')
        axes[0, 0].set_ylabel('Number of Developers')
        
        # 2. Commit count vs PR count
        axes[0, 1].scatter(self.df['commit_count'], self.df['total_prs'], alpha=0.6, c=self.df['comprehensive_score'], cmap='viridis')
        axes[0, 1].set_title('Commit Count vs PR Count')
        axes[0, 1].set_xlabel('Commit Count')
        axes[0, 1].set_ylabel('PR Count')
        
        # 3. Developer type distribution
        developer_type_counts = self.df['developer_type'].value_counts()
        axes[0, 2].pie(developer_type_counts.values, labels=developer_type_counts.index, autopct='%1.1f%%')
        axes[0, 2].set_title('Developer Type Distribution')
        
        # 4. Contribution level distribution
        contribution_level_counts = self.df['contribution_level'].value_counts()
        axes[1, 0].bar(contribution_level_counts.index, contribution_level_counts.values, color='lightcoral')
        axes[1, 0].set_title('Contribution Level Distribution')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # 5. PR acceptance rate distribution
        axes[1, 1].hist(self.df['pr_acceptance_rate'], bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
        axes[1, 1].set_title('PR Acceptance Rate Distribution')
        axes[1, 1].set_xlabel('PR Acceptance Rate')
        axes[1, 1].set_ylabel('Number of Developers')
        
        # 6. Active days vs comprehensive score
        axes[1, 2].scatter(self.df['active_days'], self.df['comprehensive_score'], alpha=0.6, color='orange')
        axes[1, 2].set_title('Active Days vs Comprehensive Score')
        axes[1, 2].set_xlabel('Active Days')
        axes[1, 2].set_ylabel('Comprehensive Score')
        
        plt.tight_layout()
        plt.savefig('developer_contribution_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def get_top_contributors(self, n=20):
        """Get top contributors"""
        return self.df.nlargest(n, 'comprehensive_score')[
            ['author_login', 'comprehensive_score', 'commit_count', 'total_prs', 
             'pr_acceptance_rate', 'active_days', 'developer_type']
        ]
    
    def get_contribution_insights(self):
        """Get contribution insights"""
        insights = {
            'high_contributors': len(self.df[self.df['comprehensive_score'] > self.df['comprehensive_score'].quantile(0.8)]),
            'low_contributors': len(self.df[self.df['comprehensive_score'] < self.df['comprehensive_score'].quantile(0.2)]),
            'avg_score': self.df['comprehensive_score'].mean(),
            'score_std': self.df['comprehensive_score'].std(),
            'most_productive_type': self.df.groupby('developer_type')['comprehensive_score'].mean().idxmax(),
            'quality_focus': len(self.df[self.df['pr_acceptance_rate'] > 0.9]),
            'quantity_focus': len(self.df[self.df['commit_count'] > self.df['commit_count'].quantile(0.9)])
        }
        return insights

def main():
    """Main function"""
    # Initialize analyzer
    analyzer = DeveloperContributionAnalyzer('data/developer_profile_final/merged_developer_profile_cleaned.csv')
    
    # Create contribution metrics
    df = analyzer.create_contribution_metrics()
    
    # Classify developers
    df = analyzer.classify_developers()
    
    # Generate report
    report = analyzer.generate_contribution_report()
    
    # Print report
    print("=" * 60)
    print("Developer Contribution Assessment Report")
    print("=" * 60)
    
    print(f"\n📊 Basic Statistics:")
    print(f"Total Developers: {report['total_developers']}")
    print(f"Average Commit Count: {report['metrics_summary']['avg_commit_count']:.2f}")
    print(f"Average PR Count: {report['metrics_summary']['avg_pr_count']:.2f}")
    print(f"Average PR Acceptance Rate: {report['metrics_summary']['avg_acceptance_rate']:.2%}")
    print(f"Average Active Days: {report['metrics_summary']['avg_active_days']:.2f}")
    
    print(f"\n🏆 Top Contributors (Top 10):")
    for i, contributor in enumerate(report['top_contributors'][:10], 1):
        print(f"{i:2d}. {contributor['author_login']:<20} "
              f"Score: {contributor['comprehensive_score']:.3f} "
              f"Commits: {contributor['commit_count']} "
              f"PRs: {contributor['total_prs']} "
              f"Type: {contributor['developer_type']}")
    
    print(f"\n📈 Contribution Level Distribution:")
    for level, count in report['contribution_levels'].items():
        percentage = (count / report['total_developers']) * 100
        print(f"{level}: {count} developers ({percentage:.1f}%)")
    
    print(f"\n👥 Developer Type Distribution:")
    for dev_type, count in report['developer_types'].items():
        percentage = (count / report['total_developers']) * 100
        print(f"{dev_type}: {count} developers ({percentage:.1f}%)")
    
    # Get insights
    insights = analyzer.get_contribution_insights()
    print(f"\n💡 Key Insights:")
    print(f"High Contributors (>80% percentile): {insights['high_contributors']} developers")
    print(f"Low Contributors (<20% percentile): {insights['low_contributors']} developers")
    print(f"Average Comprehensive Score: {insights['avg_score']:.3f} (±{insights['score_std']:.3f})")
    print(f"Most Productive Type: {insights['most_productive_type']}")
    print(f"Quality-Focused Contributors (PR acceptance rate >90%): {insights['quality_focus']} developers")
    print(f"Quantity-Focused Contributors (commit count >90% percentile): {insights['quantity_focus']} developers")
    
    # Plot analysis charts
    analyzer.plot_contribution_analysis()
    
    # Save detailed results
    top_contributors = analyzer.get_top_contributors(50)
    top_contributors.to_csv('top_contributors_analysis.csv', index=False)
    print(f"\n💾 Analysis Results Saved:")
    print(f"- Charts: developer_contribution_analysis.png")
    print(f"- Data: top_contributors_analysis.csv")

if __name__ == "__main__":
    main() 