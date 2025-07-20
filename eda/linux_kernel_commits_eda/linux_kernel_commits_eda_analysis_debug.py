#!/usr/bin/env python3
"""
Linux Kernel Commits EDA Analysis 
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
import traceback
warnings.filterwarnings('ignore')

# Set up plotting parameters
plt.style.use('default')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

class LinuxKernelCommitsAnalyzer:
    def __init__(self, csv_path):
        """Initialize the analyzer with the CSV file path"""
        self.csv_path = csv_path
        self.df = None
        self.load_data()
        
    def load_data(self):
        """Load and preprocess the data"""
        try:
            print("Loading Linux kernel commits data...")
            self.df = pd.read_csv(self.csv_path)
            
            # Convert timestamp to datetime
            self.df['commit_datetime'] = pd.to_datetime(self.df['commit_ts_utc'], unit='s')
            
            # Extract time features
            self.df['hour'] = self.df['commit_datetime'].dt.hour
            self.df['day_of_week'] = self.df['commit_datetime'].dt.dayofweek  # 0=Monday
            self.df['day_of_month'] = self.df['commit_datetime'].dt.day
            self.df['month'] = self.df['commit_datetime'].dt.month
            
            # Calculate total lines changed
            self.df['total_lines_changed'] = self.df['insertions'] + self.df['deletions']
            
            # Fill missing values for time differences
            self.df['dt_prev_commit_sec'] = self.df['dt_prev_commit_sec'].fillna(0)
            self.df['dt_prev_author_sec'] = self.df['dt_prev_author_sec'].fillna(0)
            
            # Create categorical features
            self.df['commit_size_category'] = pd.cut(
                self.df['total_lines_changed'], 
                bins=[0, 10, 50, 200, 1000, float('inf')], 
                labels=['tiny', 'small', 'medium', 'large', 'huge']
            )
            
            # Working hours indicator (assuming 9-17 UTC as working hours)
            self.df['is_working_hours'] = (self.df['hour'] >= 9) & (self.df['hour'] <= 17)
            
            print(f"✓ Data loaded successfully. Shape: {self.df.shape}")
            print(f"✓ Date range: {self.df['commit_datetime'].min()} to {self.df['commit_datetime'].max()}")
            
        except Exception as e:
            print(f"❌ Error in load_data: {e}")
            traceback.print_exc()
            
    def basic_statistics(self):
        """Display basic statistics about the dataset"""
        try:
            print("\n" + "="*60)
            print("BASIC STATISTICS")
            print("="*60)
            
            print(f"Total commits: {len(self.df)}")
            print(f"Unique authors: {self.df['author_name'].nunique()}")
            print(f"Date range: {self.df['commit_datetime'].min().date()} to {self.df['commit_datetime'].max().date()}")
            print(f"Merge commits: {self.df['is_merge'].sum()} ({self.df['is_merge'].mean()*100:.1f}%)")
            
            print("\nCommit statistics:")
            print(self.df[['files_changed', 'insertions', 'deletions', 'total_lines_changed']].describe())
            
            print("\nTime interval statistics (seconds):")
            print(self.df[['dt_prev_commit_sec', 'dt_prev_author_sec']].describe())
            print("✓ Basic statistics completed")
            
        except Exception as e:
            print(f"❌ Error in basic_statistics: {e}")
            traceback.print_exc()
        
    def temporal_analysis(self):
        """Analyze temporal patterns in commits"""
        try:
            print("\n" + "="*60)
            print("TEMPORAL ANALYSIS")
            print("="*60)
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # Commits by hour of day
            hourly_commits = self.df['hour'].value_counts().sort_index()
            axes[0, 0].bar(hourly_commits.index, hourly_commits.values)
            axes[0, 0].set_title('Commits by Hour of Day')
            axes[0, 0].set_xlabel('Hour (UTC)')
            axes[0, 0].set_ylabel('Number of Commits')
            axes[0, 0].axvspan(9, 17, alpha=0.3, color='yellow', label='Working Hours')
            axes[0, 0].legend()
            
            # Commits by day of week
            days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            daily_commits = self.df['day_of_week'].value_counts().sort_index()
            axes[0, 1].bar(range(7), daily_commits.values)
            axes[0, 1].set_title('Commits by Day of Week')
            axes[0, 1].set_xlabel('Day of Week')
            axes[0, 1].set_ylabel('Number of Commits')
            axes[0, 1].set_xticks(range(7))
            axes[0, 1].set_xticklabels(days)
            
            # Time interval between commits (log scale)
            time_intervals = self.df['dt_prev_commit_sec'][self.df['dt_prev_commit_sec'] > 0]
            axes[1, 0].hist(np.log10(time_intervals + 1), bins=50, alpha=0.7)
            axes[1, 0].set_title('Distribution of Time Intervals Between Commits')
            axes[1, 0].set_xlabel('Log10(Seconds + 1)')
            axes[1, 0].set_ylabel('Frequency')
            
            # Author-specific time intervals
            author_intervals = self.df['dt_prev_author_sec'][self.df['dt_prev_author_sec'] > 0]
            axes[1, 1].hist(np.log10(author_intervals + 1), bins=50, alpha=0.7, color='orange')
            axes[1, 1].set_title('Distribution of Time Intervals Between Author Commits')
            axes[1, 1].set_xlabel('Log10(Seconds + 1)')
            axes[1, 1].set_ylabel('Frequency')
            
            plt.tight_layout()
            plt.savefig('linux_commits_temporal_analysis.png', dpi=300, bbox_inches='tight')
            plt.close()  # Close the figure to free memory
            
            # Print insights about working hours
            working_hours_pct = self.df['is_working_hours'].mean() * 100
            print(f"Commits during working hours (9-17 UTC): {working_hours_pct:.1f}%")
            print("✓ Temporal analysis completed - linux_commits_temporal_analysis.png saved")
            
        except Exception as e:
            print(f"❌ Error in temporal_analysis: {e}")
            traceback.print_exc()
         
    def commit_behavior_analysis(self):
        """Analyze commit behavior patterns"""
        try:
            print("\n" + "="*60)
            print("COMMIT BEHAVIOR ANALYSIS")
            print("="*60)
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # Commit size distribution
            size_counts = self.df['commit_size_category'].value_counts()
            axes[0, 0].pie(size_counts.values, labels=size_counts.index, autopct='%1.1f%%')
            axes[0, 0].set_title('Distribution of Commit Sizes')
            
            # Files changed vs lines changed
            axes[0, 1].scatter(self.df['files_changed'], self.df['total_lines_changed'], alpha=0.6)
            axes[0, 1].set_xlabel('Files Changed')
            axes[0, 1].set_ylabel('Total Lines Changed')
            axes[0, 1].set_title('Files Changed vs Lines Changed')
            axes[0, 1].set_yscale('log')
            
            # Merge vs non-merge commits
            merge_comparison = self.df.groupby('is_merge')[['files_changed', 'total_lines_changed']].mean()
            x = np.arange(len(merge_comparison.columns))
            width = 0.35
            axes[1, 0].bar(x - width/2, merge_comparison.loc[0], width, label='Non-merge')
            axes[1, 0].bar(x + width/2, merge_comparison.loc[1], width, label='Merge')
            axes[1, 0].set_title('Average Changes: Merge vs Non-merge Commits')
            axes[1, 0].set_xticks(x)
            axes[1, 0].set_xticklabels(['Files Changed', 'Lines Changed'])
            axes[1, 0].legend()
            
            # File types distribution
            file_types_list = []
            for types in self.df['file_types'].dropna():
                if pd.notna(types):
                    file_types_list.extend(types.split(';'))
            
            if file_types_list:
                file_types_count = pd.Series(file_types_list).value_counts().head(10)
                axes[1, 1].barh(range(len(file_types_count)), file_types_count.values)
                axes[1, 1].set_yticks(range(len(file_types_count)))
                axes[1, 1].set_yticklabels(file_types_count.index)
                axes[1, 1].set_title('Top 10 File Types')
                axes[1, 1].set_xlabel('Number of Commits')
            else:
                axes[1, 1].text(0.5, 0.5, 'No file type data available', 
                               ha='center', va='center', transform=axes[1, 1].transAxes)
                axes[1, 1].set_title('File Types - No Data')
            
            plt.tight_layout()
            plt.savefig('linux_commits_behavior_analysis.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("✓ Behavior analysis completed - linux_commits_behavior_analysis.png saved")
            
        except Exception as e:
            print(f"❌ Error in commit_behavior_analysis: {e}")
            traceback.print_exc()
         
    def developer_productivity_analysis(self):
        """Analyze developer productivity patterns"""
        try:
            print("\n" + "="*60)
            print("DEVELOPER PRODUCTIVITY ANALYSIS") 
            print("="*60)
            
            # Calculate per-author statistics
            author_stats = self.df.groupby('author_name').agg({
                'hash': 'count',  # total commits
                'total_lines_changed': ['mean', 'sum'],
                'files_changed': 'mean',
                'is_merge': 'sum',
                'dt_prev_author_sec': 'mean'
            }).round(2)
            
            author_stats.columns = ['total_commits', 'avg_lines_changed', 'total_lines_changed', 
                                   'avg_files_changed', 'merge_commits', 'avg_time_between_commits']
            
            # Filter authors with at least 5 commits for meaningful analysis
            active_authors = author_stats[author_stats['total_commits'] >= 5].copy()
            
            print(f"Total authors: {len(author_stats)}")
            print(f"Active authors (>=5 commits): {len(active_authors)}")
            
            # Top contributors
            top_contributors = active_authors.nlargest(10, 'total_commits')
            print("\nTop 10 Contributors (by commit count):")
            print(top_contributors[['total_commits', 'avg_lines_changed', 'avg_files_changed']])
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # Distribution of commits per author
            axes[0, 0].hist(author_stats['total_commits'], bins=30, alpha=0.7)
            axes[0, 0].set_title('Distribution of Commits per Author')
            axes[0, 0].set_xlabel('Number of Commits')
            axes[0, 0].set_ylabel('Number of Authors')
            axes[0, 0].set_yscale('log')
            
            # Relationship between commits and average change size
            if len(active_authors) > 0:
                axes[0, 1].scatter(active_authors['total_commits'], active_authors['avg_lines_changed'], alpha=0.6)
                axes[0, 1].set_xlabel('Total Commits')
                axes[0, 1].set_ylabel('Average Lines Changed per Commit')
                axes[0, 1].set_title('Commits vs Average Change Size')
            
            # Top contributors visualization
            if len(top_contributors) > 0:
                top_contributors_sorted = top_contributors.sort_values('total_commits')
                axes[1, 0].barh(range(len(top_contributors_sorted)), top_contributors_sorted['total_commits'])
                axes[1, 0].set_yticks(range(len(top_contributors_sorted)))
                axes[1, 0].set_yticklabels(top_contributors_sorted.index)
                axes[1, 0].set_title('Top 10 Contributors by Commit Count')
                axes[1, 0].set_xlabel('Number of Commits')
            
            # Average time between commits for active authors
            if len(active_authors) > 0:
                time_between = active_authors['avg_time_between_commits'][active_authors['avg_time_between_commits'] > 0]
                if len(time_between) > 0:
                    axes[1, 1].hist(np.log10(time_between + 1), bins=30, alpha=0.7)
                    axes[1, 1].set_title('Distribution of Average Time Between Author Commits')
                    axes[1, 1].set_xlabel('Log10(Average Seconds + 1)')
                    axes[1, 1].set_ylabel('Number of Authors')
            
            plt.tight_layout()
            plt.savefig('linux_commits_developer_productivity.png', dpi=300, bbox_inches='tight')
            plt.close()
            print("✓ Developer productivity analysis completed - linux_commits_developer_productivity.png saved")
            
        except Exception as e:
            print(f"❌ Error in developer_productivity_analysis: {e}")
            traceback.print_exc()
         
    def batch_behavior_analysis(self):
        """Analyze potential batch behaviors - patterns that might group commits together"""
        try:
            print("\n" + "="*60)
            print("BATCH BEHAVIOR ANALYSIS")
            print("="*60)
            
            # Define potential batch indicators
            # 1. Short time intervals (< 1 hour)
            short_intervals = self.df['dt_prev_commit_sec'] < 3600
            
            # 2. Same author consecutive commits
            same_author_quick = (self.df['dt_prev_author_sec'] < 3600) & (self.df['dt_prev_author_sec'] > 0)
            
            # 3. Small commits that might be related
            small_commits = self.df['total_lines_changed'] < 50
            
            print(f"Commits with short intervals (<1 hour): {short_intervals.sum()} ({short_intervals.mean()*100:.1f}%)")
            print(f"Same author quick commits (<1 hour): {same_author_quick.sum()} ({same_author_quick.mean()*100:.1f}%)")
            print(f"Small commits (<50 lines): {small_commits.sum()} ({small_commits.mean()*100:.1f}%)")
            
            # Analyze commit message patterns for potential batches
            self.df['msg_length'] = self.df['msg_subject'].str.len()
            
            # Look for common patterns in commit messages
            merge_commits = self.df['msg_subject'].str.contains('Merge', case=False, na=False)
            fix_commits = self.df['msg_subject'].str.contains('fix|Fix', case=False, na=False)
            refactor_commits = self.df['msg_subject'].str.contains('refactor|Refactor', case=False, na=False)
            
            print(f"Merge-related commits: {merge_commits.sum()} ({merge_commits.mean()*100:.1f}%)")
            print(f"Fix-related commits: {fix_commits.sum()} ({fix_commits.mean()*100:.1f}%)")
            print(f"Refactor-related commits: {refactor_commits.sum()} ({refactor_commits.mean()*100:.1f}%)")
            
            # Analyze directory patterns
            dirs_list = []
            for dirs in self.df['dirs_touched'].dropna():
                if pd.notna(dirs):
                    dirs_list.extend(dirs.split(';'))
            
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            
            # Time interval distribution with batch threshold
            intervals = self.df['dt_prev_commit_sec'][self.df['dt_prev_commit_sec'] > 0]
            if len(intervals) > 0:
                axes[0, 0].hist(intervals, bins=50, alpha=0.7)
                axes[0, 0].axvline(x=3600, color='red', linestyle='--', label='1 hour threshold')
                axes[0, 0].set_title('Commit Time Intervals (Potential Batch Indicator)')
                axes[0, 0].set_xlabel('Seconds')
                axes[0, 0].set_ylabel('Frequency')
                axes[0, 0].set_xlim(0, 7200)  # Focus on first 2 hours
                axes[0, 0].legend()
            
            # Commit message length distribution
            msg_lengths = self.df['msg_length'].dropna()
            if len(msg_lengths) > 0:
                axes[0, 1].hist(msg_lengths, bins=50, alpha=0.7)
                axes[0, 1].set_title('Commit Message Length Distribution')
                axes[0, 1].set_xlabel('Message Length (characters)')
                axes[0, 1].set_ylabel('Frequency')
            
            # Top directories
            if dirs_list:
                dirs_count = pd.Series(dirs_list).value_counts().head(15)
                axes[1, 0].barh(range(len(dirs_count)), dirs_count.values)
                axes[1, 0].set_yticks(range(len(dirs_count)))
                axes[1, 0].set_yticklabels(dirs_count.index)
                axes[1, 0].set_title('Top 15 Directories by Commit Count')
                axes[1, 0].set_xlabel('Number of Commits')
            else:
                axes[1, 0].text(0.5, 0.5, 'No directory data available', 
                               ha='center', va='center', transform=axes[1, 0].transAxes)
            
            # Batch potential score visualization
            # Create a simple batch score based on multiple factors
            batch_score = (
                (self.df['dt_prev_commit_sec'] < 3600).astype(int) * 2 +  # Short interval
                (self.df['dt_prev_author_sec'] < 3600).astype(int) +       # Same author quick
                (self.df['total_lines_changed'] < 50).astype(int) +        # Small commit
                merge_commits.astype(int)                                   # Merge commit
            )
            
            axes[1, 1].hist(batch_score, bins=range(6), alpha=0.7, align='left')
            axes[1, 1].set_title('Batch Potential Score Distribution')
            axes[1, 1].set_xlabel('Batch Score (0-5)')
            axes[1, 1].set_ylabel('Number of Commits')
            axes[1, 1].set_xticks(range(5))
            
            plt.tight_layout()
            plt.savefig('linux_commits_batch_analysis.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # Analyze high-potential batch commits
            high_batch_potential = self.df[batch_score >= 3]
            print(f"\nHigh batch potential commits (score >=3): {len(high_batch_potential)} ({len(high_batch_potential)/len(self.df)*100:.1f}%)")
            
            if len(high_batch_potential) > 0:
                print("\nCharacteristics of high batch potential commits:")
                print(high_batch_potential[['author_name', 'dt_prev_commit_sec', 'total_lines_changed', 'msg_subject']].head(10))
            
            print("✓ Batch behavior analysis completed - linux_commits_batch_analysis.png saved")
            
        except Exception as e:
            print(f"❌ Error in batch_behavior_analysis: {e}")
            traceback.print_exc()
    
    def correlation_analysis(self):
        """Analyze correlations between different features"""
        try:
            print("\n" + "="*60)
            print("CORRELATION ANALYSIS")
            print("="*60)
            
            # Select numerical features for correlation analysis
            numerical_features = [
                'files_changed', 'insertions', 'deletions', 'total_lines_changed',
                'dt_prev_commit_sec', 'dt_prev_author_sec', 'is_merge',
                'hour', 'day_of_week', 'is_working_hours'
            ]
            
            # Add message length if not already present
            if 'msg_length' not in self.df.columns:
                self.df['msg_length'] = self.df['msg_subject'].str.len()
            
            numerical_features.append('msg_length')
            
            correlation_matrix = self.df[numerical_features].corr()
            
            plt.figure(figsize=(12, 10))
            sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                       square=True, linewidths=0.5)
            plt.title('Feature Correlation Matrix')
            plt.tight_layout()
            plt.savefig('linux_commits_correlation_matrix.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # Print strongest correlations
            print("\nStrongest positive correlations (>0.3):")
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_val = correlation_matrix.iloc[i, j]
                    if corr_val > 0.3:
                        print(f"{correlation_matrix.columns[i]} - {correlation_matrix.columns[j]}: {corr_val:.3f}")
            
            print("\nStrongest negative correlations (<-0.3):")
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_val = correlation_matrix.iloc[i, j]
                    if corr_val < -0.3:
                        print(f"{correlation_matrix.columns[i]} - {correlation_matrix.columns[j]}: {corr_val:.3f}")
            
            print("✓ Correlation analysis completed - linux_commits_correlation_matrix.png saved")
            
        except Exception as e:
            print(f"❌ Error in correlation_analysis: {e}")
            traceback.print_exc()
    
    def generate_insights(self):
        """Generate insights about potential batch behaviors"""
        try:
            print("\n" + "="*80)
            print("KEY INSIGHTS FOR TORQUE CLUSTERING BATCH BEHAVIOR")
            print("="*80)
            
            # Quick commits analysis
            quick_commits = self.df['dt_prev_commit_sec'] < 1800  # 30 minutes
            same_author_quick = (self.df['dt_prev_author_sec'] < 1800) & (self.df['dt_prev_author_sec'] > 0)
            
            print("1. TEMPORAL PATTERNS:")
            print(f"   - {quick_commits.sum()} commits ({quick_commits.mean()*100:.1f}%) happen within 30 minutes of previous commit")
            print(f"   - {same_author_quick.sum()} commits ({same_author_quick.mean()*100:.1f}%) by same author within 30 minutes")
            print(f"   - Working hours commits: {self.df['is_working_hours'].mean()*100:.1f}%")
            
            print("\n2. COMMIT SIZE PATTERNS:")
            small_commits = self.df['total_lines_changed'] < 20
            medium_commits = (self.df['total_lines_changed'] >= 20) & (self.df['total_lines_changed'] < 100)
            large_commits = self.df['total_lines_changed'] >= 100
            print(f"   - Small commits (<20 lines): {small_commits.sum()} ({small_commits.mean()*100:.1f}%)")
            print(f"   - Medium commits (20-100 lines): {medium_commits.sum()} ({medium_commits.mean()*100:.1f}%)")
            print(f"   - Large commits (>100 lines): {large_commits.sum()} ({large_commits.mean()*100:.1f}%)")
            
            print("\n3. DEVELOPER BEHAVIOR:")
            active_developers = self.df['author_name'].value_counts()
            print(f"   - Top developer: {active_developers.index[0]} with {active_developers.iloc[0]} commits")
            print(f"   - Developers with >10 commits: {(active_developers > 10).sum()}")
            print(f"   - Single-commit developers: {(active_developers == 1).sum()}")
            
            print("\n4. CONTENT PATTERNS:")
            merge_pct = self.df['is_merge'].mean() * 100
            avg_files = self.df['files_changed'].mean()
            print(f"   - Merge commits: {merge_pct:.1f}%")
            print(f"   - Average files per commit: {avg_files:.1f}")
            
            # File type analysis
            file_types_list = []
            for types in self.df['file_types'].dropna():
                if pd.notna(types):
                    file_types_list.extend(types.split(';'))
            
            if file_types_list:
                top_file_type = pd.Series(file_types_list).value_counts().index[0]
                print(f"   - Most common file type: {top_file_type}")
            
            print("\n5. RECOMMENDATIONS FOR BATCH IDENTIFICATION:")
            print("   - Consider time intervals <30 minutes as potential batch indicators")
            print("   - Group commits by same author within short time windows")
            print("   - Small commits (<20 lines) often part of larger development sessions")
            print("   - Merge commits might represent completion of development batches")
            print("   - Consider file types and directories for domain-specific batching")
            
            print("✓ Insights generation completed")
            
        except Exception as e:
            print(f"❌ Error in generate_insights: {e}")
            traceback.print_exc()
        
    def run_full_analysis(self):
        """Run the complete EDA analysis with error handling"""
        print("🚀 Starting Linux Kernel Commits EDA Analysis...")
        print("This analysis will help identify patterns for Torque Clustering batch behavior\n")
        
        try:
            print("Step 1/6: Running basic statistics...")
            self.basic_statistics()
            
            print("\nStep 2/6: Running temporal analysis...")
            self.temporal_analysis()
            
            print("\nStep 3/6: Running commit behavior analysis...")
            self.commit_behavior_analysis()
            
            print("\nStep 4/6: Running developer productivity analysis...")
            self.developer_productivity_analysis()
            
            print("\nStep 5/6: Running batch behavior analysis...")
            self.batch_behavior_analysis()
            
            print("\nStep 6/6: Running correlation analysis...")
            self.correlation_analysis()
            
            print("\nGenerating final insights...")
            self.generate_insights()
            
            print("\n" + "="*80)
            print("🎉 ANALYSIS COMPLETE!")
            print("="*80)
            print("Generated visualizations:")
            print("✓ linux_commits_temporal_analysis.png")
            print("✓ linux_commits_behavior_analysis.png") 
            print("✓ linux_commits_developer_productivity.png")
            print("✓ linux_commits_batch_analysis.png")
            print("✓ linux_commits_correlation_matrix.png")
            
        except Exception as e:
            print(f"\n❌ Critical error in run_full_analysis: {e}")
            traceback.print_exc()

# Main execution
if __name__ == "__main__":
    try:
        # Initialize analyzer
        print("Initializing analyzer...")
        analyzer = LinuxKernelCommitsAnalyzer('data/github_commit_data_test/linux_kernel_commits.csv')
        
        # Run complete analysis
        analyzer.run_full_analysis()
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc() 