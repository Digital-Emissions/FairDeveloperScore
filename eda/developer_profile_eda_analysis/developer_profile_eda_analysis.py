#!/usr/bin/env python3
"""
Developer Profile EDA Analysis

Structured analysis of developer behavioral features to explore which behavior patterns 
are more likely to form batch clusters.

EDA Framework:
1. Understand data structure
2. Build behavioral feature analysis
3. Identify key indicators for batch clustering
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set visualization parameters
plt.style.use('default')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

class DeveloperProfileAnalyzer:
    def __init__(self, csv_path):
        """Initialize the analyzer"""
        self.csv_path = csv_path
        self.df = None
        self.load_data()
        
    def load_data(self):
        """Load and preprocess data"""
        print("Loading developer profile data...")
        try:
            self.df = pd.read_csv(self.csv_path)
            
            # Data cleaning and feature engineering
            self.df = self.df.fillna(0)  # Fill missing values
            
            # Create derived features
            self.df['productivity_ratio'] = self.df['commit_count'] / (self.df['active_days'] + 1)  # Avoid division by zero
            self.df['change_efficiency'] = self.df['avg_total_changes'] / (self.df['avg_msg_len'] + 1)
            self.df['pr_activity'] = self.df['total_prs'] > 0
            self.df['weekend_worker'] = self.df['weekend_commit_ratio'] > 0.2
            
            # Developer type classification
            self.df['developer_type'] = self.categorize_developers()
            
            print(f"✓ Data loaded successfully. Shape: {self.df.shape}")
            print(f"✓ Number of developers: {len(self.df)}")
            
        except Exception as e:
            print(f"❌ Data loading error: {e}")
            
    def categorize_developers(self):
        """Categorize developers based on behavioral features"""
        categories = []
        for _, row in self.df.iterrows():
            if row['commit_count'] >= 10 and row['pr_acceptance_rate'] >= 0.8:
                categories.append('Core Contributor')
            elif row['commit_count'] >= 5:
                categories.append('Regular Contributor')
            elif row['total_prs'] > 0:
                categories.append('PR Contributor')
            else:
                categories.append('Occasional Contributor')
        return categories
    
    def understand_data_structure(self):
        """Step 1: Understand data structure"""
        print("\n" + "="*80)
        print("STEP 1: DATA STRUCTURE ANALYSIS")
        print("="*80)
        
        print(f"Data dimensions: {self.df.shape[0]} developers × {self.df.shape[1]} features")
        print(f"\nField list:")
        for i, col in enumerate(self.df.columns, 1):
            print(f"{i:2d}. {col}")
        
        print(f"\nData type distribution:")
        print(self.df.dtypes.value_counts())
        
        print(f"\nBasic statistics:")
        print(self.df.describe())
        
        # Identify behavioral features vs result variables
        behavior_features = {
            'Temporal': ['active_days', 'weekend_commit_ratio'],
            'Content': ['avg_additions', 'avg_deletions', 'avg_total_changes', 'max_total_changes', 'avg_msg_len'],
            'Developer': ['commit_count', 'total_prs', 'merged_prs', 'pr_acceptance_rate'],
            'Productivity': ['productivity_ratio', 'change_efficiency']
        }
        
        print(f"\nBehavioral feature classification:")
        for category, features in behavior_features.items():
            print(f"  {category}: {features}")
    
    def analyze_behavioral_features(self):
        """Step 2: Build behavioral feature analysis"""
        print("\n" + "="*80)
        print("STEP 2: BEHAVIORAL FEATURE ANALYSIS")
        print("="*80)
        
        # Create multiple subplots
        fig, axes = plt.subplots(3, 2, figsize=(15, 18))
        
        # 1. Temporal features
        axes[0, 0].hist(self.df['active_days'], bins=30, alpha=0.7, color='skyblue')
        axes[0, 0].set_title('Distribution of Active Days')
        axes[0, 0].set_xlabel('Active Days')
        axes[0, 0].set_ylabel('Number of Developers')
        
        axes[0, 1].hist(self.df['weekend_commit_ratio'], bins=20, alpha=0.7, color='lightcoral')
        axes[0, 1].set_title('Weekend Commit Ratio Distribution')
        axes[0, 1].set_xlabel('Weekend Commit Ratio')
        axes[0, 1].set_ylabel('Number of Developers')
        
        # 2. Content features
        axes[1, 0].scatter(self.df['avg_total_changes'], self.df['avg_msg_len'], alpha=0.6)
        axes[1, 0].set_title('Code Changes vs Message Length')
        axes[1, 0].set_xlabel('Average Total Changes')
        axes[1, 0].set_ylabel('Average Message Length')
        axes[1, 0].set_xscale('log')
        axes[1, 0].set_yscale('log')
        
        # 3. Developer activity
        commit_bins = [0, 1, 5, 10, 50, float('inf')]
        commit_labels = ['1', '2-5', '6-10', '11-50', '50+']
        self.df['commit_category'] = pd.cut(self.df['commit_count'], bins=commit_bins, labels=commit_labels)
        
        commit_dist = self.df['commit_category'].value_counts()
        axes[1, 1].pie(commit_dist.values, labels=commit_dist.index, autopct='%1.1f%%')
        axes[1, 1].set_title('Developer Activity Distribution')
        
        # 4. PR features
        pr_active = self.df[self.df['total_prs'] > 0]
        if len(pr_active) > 0:
            axes[2, 0].scatter(pr_active['total_prs'], pr_active['pr_acceptance_rate'], alpha=0.6)
            axes[2, 0].set_title('PR Volume vs Acceptance Rate')
            axes[2, 0].set_xlabel('Total PRs')
            axes[2, 0].set_ylabel('PR Acceptance Rate')
        
        # 5. Developer type distribution
        dev_type_counts = self.df['developer_type'].value_counts()
        axes[2, 1].barh(range(len(dev_type_counts)), dev_type_counts.values)
        axes[2, 1].set_yticks(range(len(dev_type_counts)))
        axes[2, 1].set_yticklabels(dev_type_counts.index)
        axes[2, 1].set_title('Developer Type Distribution')
        axes[2, 1].set_xlabel('Number of Developers')
        
        plt.tight_layout()
        plt.savefig('developer_profile_behavioral_features.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✓ Behavioral feature analysis completed - developer_profile_behavioral_features.png saved")
    
    def analyze_batch_potential_indicators(self):
        """Analyze potential batch clustering indicators"""
        print("\n" + "="*80)
        print("STEP 3: BATCH CLUSTERING POTENTIAL ANALYSIS")
        print("="*80)
        
        # Define key indicators that might influence batch clustering
        
        # 1. High-frequency contributors (more likely to have consecutive batches)
        high_frequency = self.df['productivity_ratio'] > self.df['productivity_ratio'].quantile(0.75)
        
        # 2. Small-granularity contributors (more likely to have related small commits)
        small_changes = self.df['avg_total_changes'] < self.df['avg_total_changes'].quantile(0.5)
        
        # 3. Active PR users (more likely to have collaborative batches)
        active_pr_users = (self.df['total_prs'] > 0) & (self.df['pr_acceptance_rate'] > 0.5)
        
        # 4. Weekend workers (may have different work patterns)
        weekend_workers = self.df['weekend_commit_ratio'] > 0.1
        
        print(f"High-frequency contributors: {high_frequency.sum()} ({high_frequency.mean()*100:.1f}%)")
        print(f"Small-granularity contributors: {small_changes.sum()} ({small_changes.mean()*100:.1f}%)")
        print(f"Active PR users: {active_pr_users.sum()} ({active_pr_users.mean()*100:.1f}%)")
        print(f"Weekend workers: {weekend_workers.sum()} ({weekend_workers.mean()*100:.1f}%)")
        
        # Create batch potential score
        batch_score = (
            high_frequency.astype(int) * 2 +  # Higher weight for high frequency
            small_changes.astype(int) +
            active_pr_users.astype(int) +
            weekend_workers.astype(int)
        )
        
        self.df['batch_potential_score'] = batch_score
        
        # Visualize batch potential analysis
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Batch potential score distribution
        axes[0, 0].hist(batch_score, bins=range(6), alpha=0.7, align='left')
        axes[0, 0].set_title('Batch Potential Score Distribution')
        axes[0, 0].set_xlabel('Batch Score (0-5)')
        axes[0, 0].set_ylabel('Number of Developers')
        axes[0, 0].set_xticks(range(5))
        
        # Productivity vs change size
        scatter = axes[0, 1].scatter(self.df['productivity_ratio'], self.df['avg_total_changes'], 
                                   c=batch_score, cmap='viridis', alpha=0.6)
        axes[0, 1].set_title('Productivity vs Change Size (colored by batch score)')
        axes[0, 1].set_xlabel('Productivity Ratio')
        axes[0, 1].set_ylabel('Average Total Changes')
        axes[0, 1].set_yscale('log')
        plt.colorbar(scatter, ax=axes[0, 1])
        
        # Batch potential by developer type
        batch_by_type = self.df.groupby('developer_type')['batch_potential_score'].mean()
        axes[1, 0].bar(range(len(batch_by_type)), batch_by_type.values)
        axes[1, 0].set_xticks(range(len(batch_by_type)))
        axes[1, 0].set_xticklabels(batch_by_type.index, rotation=45)
        axes[1, 0].set_title('Average Batch Score by Developer Type')
        axes[1, 0].set_ylabel('Average Batch Score')
        
        # Activity vs PR success
        pr_users = self.df[self.df['total_prs'] > 0]
        if len(pr_users) > 0:
            axes[1, 1].scatter(pr_users['commit_count'], pr_users['pr_acceptance_rate'], 
                             c=pr_users['batch_potential_score'], cmap='plasma', alpha=0.6)
            axes[1, 1].set_title('Commit Activity vs PR Success (colored by batch score)')
            axes[1, 1].set_xlabel('Commit Count')
            axes[1, 1].set_ylabel('PR Acceptance Rate')
        
        plt.tight_layout()
        plt.savefig('developer_profile_batch_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✓ Batch clustering analysis completed - developer_profile_batch_analysis.png saved")
        
        # Analyze high-potential developers
        high_potential = self.df[batch_score >= 3]
        print(f"\nHigh batch potential developers (score ≥3): {len(high_potential)} ({len(high_potential)/len(self.df)*100:.1f}%)")
        
        if len(high_potential) > 0:
            print("\nHigh-potential developer characteristics:")
            print(high_potential[['author_login', 'developer_type', 'commit_count', 
                                'avg_total_changes', 'pr_acceptance_rate', 'batch_potential_score']].head(10))
    
    def correlation_and_feature_importance(self):
        """Correlation analysis and feature importance"""
        print("\n" + "="*80)
        print("STEP 4: FEATURE CORRELATION ANALYSIS")
        print("="*80)
        
        # Select numerical features for correlation analysis
        numerical_features = [
            'commit_count', 'active_days', 'avg_additions', 'avg_deletions', 
            'avg_total_changes', 'max_total_changes', 'avg_msg_len',
            'weekend_commit_ratio', 'total_prs', 'pr_acceptance_rate',
            'productivity_ratio', 'change_efficiency', 'batch_potential_score'
        ]
        
        correlation_matrix = self.df[numerical_features].corr()
        
        # Create correlation heatmap
        plt.figure(figsize=(14, 12))
        mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
        sns.heatmap(correlation_matrix, mask=mask, annot=True, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5, cbar_kws={"shrink": .8})
        plt.title('Developer Profile Feature Correlation Matrix')
        plt.tight_layout()
        plt.savefig('developer_profile_correlation_matrix.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # Find features most correlated with batch potential
        batch_correlations = correlation_matrix['batch_potential_score'].abs().sort_values(ascending=False)
        print("\nFeatures most correlated with batch potential:")
        for feature, corr in batch_correlations.head(8).items():
            if feature != 'batch_potential_score':
                print(f"  {feature}: {corr:.3f}")
        
        print("✓ Correlation analysis completed - developer_profile_correlation_matrix.png saved")
    
    def generate_insights_and_recommendations(self):
        """Generate insights and recommendations"""
        print("\n" + "="*80)
        print("STEP 5: INSIGHTS SUMMARY AND TORQUE CLUSTERING RECOMMENDATIONS")
        print("="*80)
        
        # Calculate key statistics
        high_productivity = self.df['productivity_ratio'].quantile(0.8)
        avg_batch_score = self.df['batch_potential_score'].mean()
        
        print("Key findings:")
        print(f"1. Developer type distribution:")
        for dev_type, count in self.df['developer_type'].value_counts().items():
            pct = count / len(self.df) * 100
            print(f"   - {dev_type}: {count} ({pct:.1f}%)")
        
        print(f"\n2. Behavioral feature insights:")
        print(f"   - High productivity threshold (80th percentile): {high_productivity:.2f} commits/day")
        print(f"   - Average batch potential score: {avg_batch_score:.2f}")
        print(f"   - Weekend worker ratio: {(self.df['weekend_commit_ratio'] > 0.1).mean()*100:.1f}%")
        print(f"   - Developers with PR activity: {(self.df['total_prs'] > 0).mean()*100:.1f}%")
        
        print(f"\n3. Torque Clustering optimization recommendations:")
        
        # Recommendations based on developer type
        core_contributors = self.df[self.df['developer_type'] == 'Core Contributor']
        if len(core_contributors) > 0:
            print(f"   - Core Contributor characteristics: avg {core_contributors['commit_count'].mean():.1f} commits, "
                  f"{core_contributors['avg_total_changes'].mean():.1f} lines/commit")
            print(f"     Recommendation: Use shorter time windows (15-30 minutes) for core contributors")
        
        occasional = self.df[self.df['developer_type'] == 'Occasional Contributor']
        if len(occasional) > 0:
            print(f"   - Occasional Contributor characteristics: avg {occasional['commit_count'].mean():.1f} commits")
            print(f"     Recommendation: Use longer time windows (2-4 hours) for occasional contributors")
        
        # Recommendations based on batch potential
        high_batch_potential = self.df[self.df['batch_potential_score'] >= 3]
        if len(high_batch_potential) > 0:
            avg_changes = high_batch_potential['avg_total_changes'].mean()
            avg_productivity = high_batch_potential['productivity_ratio'].mean()
            print(f"   - High batch potential developers: avg {avg_changes:.1f} lines/commit, "
                  f"productivity {avg_productivity:.2f}")
            print(f"     Recommendation: Use tight clustering for small changes (<{avg_changes:.0f} lines) from these developers")
        
        print(f"\n4. Feature weight recommendations:")
        # Only select numerical columns for correlation analysis
        numerical_cols = self.df.select_dtypes(include=[np.number]).columns
        batch_corr = self.df[numerical_cols].corr()['batch_potential_score'].abs().sort_values(ascending=False)
        top_features = batch_corr.head(4).index.tolist()
        if 'batch_potential_score' in top_features:
            top_features.remove('batch_potential_score')
        print(f"   - Key features: {', '.join(top_features[:3])}")
        print(f"   - Recommendation: Increase weights for these features in Torque algorithm")
    
    def run_full_analysis(self):
        """Run complete EDA analysis"""
        print("🚀 Starting Developer Profile EDA Analysis...")
        print("Exploring key behavioral features for batch clustering using structured approach\n")
        
        try:
            # Step 1: Understand data structure
            self.understand_data_structure()
            
            # Step 2: Behavioral feature analysis
            self.analyze_behavioral_features()
            
            # Step 3: Batch clustering potential analysis
            self.analyze_batch_potential_indicators()
            
            # Step 4: Correlation analysis
            self.correlation_and_feature_importance()
            
            # Step 5: Insights and recommendations
            self.generate_insights_and_recommendations()
            
            print("\n" + "="*80)
            print("🎉 ANALYSIS COMPLETE!")
            print("="*80)
            print("Generated visualization files:")
            print("✓ developer_profile_behavioral_features.png")
            print("✓ developer_profile_batch_analysis.png")
            print("✓ developer_profile_correlation_matrix.png")
            
        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            import traceback
            traceback.print_exc()

# Main execution
if __name__ == "__main__":
    # Initialize analyzer
    analyzer = DeveloperProfileAnalyzer('data/developer_profile_final/merged_developer_profile_cleaned.csv')
    
    # Run complete analysis
    analyzer.run_full_analysis() 