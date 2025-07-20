#!/usr/bin/env python3
"""
Developer Profile EDA Analysis

基于结构化思路分析开发者行为特征，探索哪些行为模式更容易形成batch聚类。

EDA思路：
1. 了解数据结构
2. 构建行为特征分析
3. 识别batch聚类的关键指标
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# 设置可视化参数
plt.style.use('default')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

class DeveloperProfileAnalyzer:
    def __init__(self, csv_path):
        """初始化分析器"""
        self.csv_path = csv_path
        self.df = None
        self.load_data()
        
    def load_data(self):
        """加载和预处理数据"""
        print("正在加载开发者档案数据...")
        try:
            self.df = pd.read_csv(self.csv_path)
            
            # 数据清洗和特征工程
            self.df = self.df.fillna(0)  # 填充缺失值
            
            # 创建派生特征
            self.df['productivity_ratio'] = self.df['commit_count'] / (self.df['active_days'] + 1)  # 避免除零
            self.df['change_efficiency'] = self.df['avg_total_changes'] / (self.df['avg_msg_len'] + 1)
            self.df['pr_activity'] = self.df['total_prs'] > 0
            self.df['weekend_worker'] = self.df['weekend_commit_ratio'] > 0.2
            
            # 开发者类型分类
            self.df['developer_type'] = self.categorize_developers()
            
            print(f"✓ 数据加载成功。形状: {self.df.shape}")
            print(f"✓ 开发者数量: {len(self.df)}")
            
        except Exception as e:
            print(f"❌ 数据加载错误: {e}")
            
    def categorize_developers(self):
        """基于行为特征对开发者进行分类"""
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
        """第一步：了解数据结构"""
        print("\n" + "="*80)
        print("第一步：数据结构分析")
        print("="*80)
        
        print(f"数据维度: {self.df.shape[0]} 开发者 × {self.df.shape[1]} 特征")
        print(f"\n字段列表:")
        for i, col in enumerate(self.df.columns, 1):
            print(f"{i:2d}. {col}")
        
        print(f"\n数据类型分布:")
        print(self.df.dtypes.value_counts())
        
        print(f"\n基础统计信息:")
        print(self.df.describe())
        
        # 识别行为特征 vs 结果变量
        behavior_features = {
            '时间相关': ['active_days', 'weekend_commit_ratio'],
            '内容相关': ['avg_additions', 'avg_deletions', 'avg_total_changes', 'max_total_changes', 'avg_msg_len'],
            '开发者相关': ['commit_count', 'total_prs', 'merged_prs', 'pr_acceptance_rate'],
            '生产力指标': ['productivity_ratio', 'change_efficiency']
        }
        
        print(f"\n行为特征分类:")
        for category, features in behavior_features.items():
            print(f"  {category}: {features}")
    
    def analyze_behavioral_features(self):
        """第二步：构建行为特征分析"""
        print("\n" + "="*80)
        print("第二步：行为特征分析")
        print("="*80)
        
        # 创建多个子图
        fig, axes = plt.subplots(3, 2, figsize=(15, 18))
        
        # 1. 时间相关特征
        axes[0, 0].hist(self.df['active_days'], bins=30, alpha=0.7, color='skyblue')
        axes[0, 0].set_title('Distribution of Active Days')
        axes[0, 0].set_xlabel('Active Days')
        axes[0, 0].set_ylabel('Number of Developers')
        
        axes[0, 1].hist(self.df['weekend_commit_ratio'], bins=20, alpha=0.7, color='lightcoral')
        axes[0, 1].set_title('Weekend Commit Ratio Distribution')
        axes[0, 1].set_xlabel('Weekend Commit Ratio')
        axes[0, 1].set_ylabel('Number of Developers')
        
        # 2. 内容相关特征
        axes[1, 0].scatter(self.df['avg_total_changes'], self.df['avg_msg_len'], alpha=0.6)
        axes[1, 0].set_title('Code Changes vs Message Length')
        axes[1, 0].set_xlabel('Average Total Changes')
        axes[1, 0].set_ylabel('Average Message Length')
        axes[1, 0].set_xscale('log')
        axes[1, 0].set_yscale('log')
        
        # 3. 开发者活跃度
        commit_bins = [0, 1, 5, 10, 50, float('inf')]
        commit_labels = ['1', '2-5', '6-10', '11-50', '50+']
        self.df['commit_category'] = pd.cut(self.df['commit_count'], bins=commit_bins, labels=commit_labels)
        
        commit_dist = self.df['commit_category'].value_counts()
        axes[1, 1].pie(commit_dist.values, labels=commit_dist.index, autopct='%1.1f%%')
        axes[1, 1].set_title('Developer Activity Distribution')
        
        # 4. PR相关特征
        pr_active = self.df[self.df['total_prs'] > 0]
        if len(pr_active) > 0:
            axes[2, 0].scatter(pr_active['total_prs'], pr_active['pr_acceptance_rate'], alpha=0.6)
            axes[2, 0].set_title('PR Volume vs Acceptance Rate')
            axes[2, 0].set_xlabel('Total PRs')
            axes[2, 0].set_ylabel('PR Acceptance Rate')
        
        # 5. 开发者类型分布
        dev_type_counts = self.df['developer_type'].value_counts()
        axes[2, 1].barh(range(len(dev_type_counts)), dev_type_counts.values)
        axes[2, 1].set_yticks(range(len(dev_type_counts)))
        axes[2, 1].set_yticklabels(dev_type_counts.index)
        axes[2, 1].set_title('Developer Type Distribution')
        axes[2, 1].set_xlabel('Number of Developers')
        
        plt.tight_layout()
        plt.savefig('developer_profile_behavioral_features.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print("✓ 行为特征分析完成 - developer_profile_behavioral_features.png 已保存")
    
    def analyze_batch_potential_indicators(self):
        """分析潜在的batch聚类指标"""
        print("\n" + "="*80)
        print("第三步：Batch聚类潜力分析")
        print("="*80)
        
        # 定义可能影响batch聚类的关键指标
        
        # 1. 高频率提交者（更可能有连续的batch）
        high_frequency = self.df['productivity_ratio'] > self.df['productivity_ratio'].quantile(0.75)
        
        # 2. 小粒度提交者（更可能有相关的小commits）
        small_changes = self.df['avg_total_changes'] < self.df['avg_total_changes'].quantile(0.5)
        
        # 3. 活跃PR用户（更可能有协作batch）
        active_pr_users = (self.df['total_prs'] > 0) & (self.df['pr_acceptance_rate'] > 0.5)
        
        # 4. 周末工作者（可能有不同的工作模式）
        weekend_workers = self.df['weekend_commit_ratio'] > 0.1
        
        print(f"高频率提交者: {high_frequency.sum()} ({high_frequency.mean()*100:.1f}%)")
        print(f"小粒度提交者: {small_changes.sum()} ({small_changes.mean()*100:.1f}%)")
        print(f"活跃PR用户: {active_pr_users.sum()} ({active_pr_users.mean()*100:.1f}%)")
        print(f"周末工作者: {weekend_workers.sum()} ({weekend_workers.mean()*100:.1f}%)")
        
        # 创建batch潜力评分
        batch_score = (
            high_frequency.astype(int) * 2 +  # 高频率权重更高
            small_changes.astype(int) +
            active_pr_users.astype(int) +
            weekend_workers.astype(int)
        )
        
        self.df['batch_potential_score'] = batch_score
        
        # 可视化batch潜力分析
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Batch潜力评分分布
        axes[0, 0].hist(batch_score, bins=range(6), alpha=0.7, align='left')
        axes[0, 0].set_title('Batch Potential Score Distribution')
        axes[0, 0].set_xlabel('Batch Score (0-5)')
        axes[0, 0].set_ylabel('Number of Developers')
        axes[0, 0].set_xticks(range(5))
        
        # 生产力 vs 变更大小
        scatter = axes[0, 1].scatter(self.df['productivity_ratio'], self.df['avg_total_changes'], 
                                   c=batch_score, cmap='viridis', alpha=0.6)
        axes[0, 1].set_title('Productivity vs Change Size (colored by batch score)')
        axes[0, 1].set_xlabel('Productivity Ratio')
        axes[0, 1].set_ylabel('Average Total Changes')
        axes[0, 1].set_yscale('log')
        plt.colorbar(scatter, ax=axes[0, 1])
        
        # 开发者类型的batch潜力
        batch_by_type = self.df.groupby('developer_type')['batch_potential_score'].mean()
        axes[1, 0].bar(range(len(batch_by_type)), batch_by_type.values)
        axes[1, 0].set_xticks(range(len(batch_by_type)))
        axes[1, 0].set_xticklabels(batch_by_type.index, rotation=45)
        axes[1, 0].set_title('Average Batch Score by Developer Type')
        axes[1, 0].set_ylabel('Average Batch Score')
        
        # 活跃度 vs PR成功率
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
        
        print("✓ Batch聚类分析完成 - developer_profile_batch_analysis.png 已保存")
        
        # 分析高潜力开发者
        high_potential = self.df[batch_score >= 3]
        print(f"\n高batch潜力开发者 (score ≥3): {len(high_potential)} ({len(high_potential)/len(self.df)*100:.1f}%)")
        
        if len(high_potential) > 0:
            print("\n高潜力开发者特征:")
            print(high_potential[['author_login', 'developer_type', 'commit_count', 
                                'avg_total_changes', 'pr_acceptance_rate', 'batch_potential_score']].head(10))
    
    def correlation_and_feature_importance(self):
        """相关性分析和特征重要性"""
        print("\n" + "="*80)
        print("第四步：特征相关性分析")
        print("="*80)
        
        # 选择数值特征进行相关性分析
        numerical_features = [
            'commit_count', 'active_days', 'avg_additions', 'avg_deletions', 
            'avg_total_changes', 'max_total_changes', 'avg_msg_len',
            'weekend_commit_ratio', 'total_prs', 'pr_acceptance_rate',
            'productivity_ratio', 'change_efficiency', 'batch_potential_score'
        ]
        
        correlation_matrix = self.df[numerical_features].corr()
        
        # 创建相关性热力图
        plt.figure(figsize=(14, 12))
        mask = np.triu(np.ones_like(correlation_matrix, dtype=bool))
        sns.heatmap(correlation_matrix, mask=mask, annot=True, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5, cbar_kws={"shrink": .8})
        plt.title('Developer Profile Feature Correlation Matrix')
        plt.tight_layout()
        plt.savefig('developer_profile_correlation_matrix.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 寻找与batch潜力相关性最强的特征
        batch_correlations = correlation_matrix['batch_potential_score'].abs().sort_values(ascending=False)
        print("\n与Batch潜力相关性最强的特征:")
        for feature, corr in batch_correlations.head(8).items():
            if feature != 'batch_potential_score':
                print(f"  {feature}: {corr:.3f}")
        
        print("✓ 相关性分析完成 - developer_profile_correlation_matrix.png 已保存")
    
    def generate_insights_and_recommendations(self):
        """生成洞察和建议"""
        print("\n" + "="*80)
        print("第五步：洞察总结和Torque Clustering建议")
        print("="*80)
        
        # 计算关键统计数据
        high_productivity = self.df['productivity_ratio'].quantile(0.8)
        avg_batch_score = self.df['batch_potential_score'].mean()
        
        print("关键发现:")
        print(f"1. 开发者类型分布:")
        for dev_type, count in self.df['developer_type'].value_counts().items():
            pct = count / len(self.df) * 100
            print(f"   - {dev_type}: {count} ({pct:.1f}%)")
        
        print(f"\n2. 行为特征洞察:")
        print(f"   - 高生产力阈值 (80th percentile): {high_productivity:.2f} commits/day")
        print(f"   - 平均batch潜力评分: {avg_batch_score:.2f}")
        print(f"   - 周末工作者比例: {(self.df['weekend_commit_ratio'] > 0.1).mean()*100:.1f}%")
        print(f"   - 有PR活动的开发者: {(self.df['total_prs'] > 0).mean()*100:.1f}%")
        
        print(f"\n3. Torque Clustering优化建议:")
        
        # 基于开发者类型的建议
        core_contributors = self.df[self.df['developer_type'] == 'Core Contributor']
        if len(core_contributors) > 0:
            print(f"   - Core Contributor特征: 平均 {core_contributors['commit_count'].mean():.1f} commits, "
                  f"{core_contributors['avg_total_changes'].mean():.1f} lines/commit")
            print(f"     建议: 对核心贡献者使用更短的时间窗口 (15-30分钟)")
        
        occasional = self.df[self.df['developer_type'] == 'Occasional Contributor']
        if len(occasional) > 0:
            print(f"   - Occasional Contributor特征: 平均 {occasional['commit_count'].mean():.1f} commits")
            print(f"     建议: 对偶发贡献者使用更长的时间窗口 (2-4小时)")
        
        # 基于batch潜力的建议
        high_batch_potential = self.df[self.df['batch_potential_score'] >= 3]
        if len(high_batch_potential) > 0:
            avg_changes = high_batch_potential['avg_total_changes'].mean()
            avg_productivity = high_batch_potential['productivity_ratio'].mean()
            print(f"   - 高batch潜力开发者: 平均 {avg_changes:.1f} lines/commit, "
                  f"生产力 {avg_productivity:.2f}")
            print(f"     建议: 对这类开发者的小变更 (<{avg_changes:.0f} lines) 使用紧密聚类")
        
        print(f"\n4. 特征权重建议:")
        # 只选择数值列进行相关性分析
        numerical_cols = self.df.select_dtypes(include=[np.number]).columns
        batch_corr = self.df[numerical_cols].corr()['batch_potential_score'].abs().sort_values(ascending=False)
        top_features = batch_corr.head(4).index.tolist()
        if 'batch_potential_score' in top_features:
            top_features.remove('batch_potential_score')
        print(f"   - 关键特征: {', '.join(top_features[:3])}")
        print(f"   - 建议在Torque算法中增加这些特征的权重")
    
    def run_full_analysis(self):
        """运行完整的EDA分析"""
        print("🚀 开始开发者档案EDA分析...")
        print("基于结构化思路探索batch聚类的关键行为特征\n")
        
        try:
            # 第一步：了解数据结构
            self.understand_data_structure()
            
            # 第二步：行为特征分析
            self.analyze_behavioral_features()
            
            # 第三步：batch聚类潜力分析
            self.analyze_batch_potential_indicators()
            
            # 第四步：相关性分析
            self.correlation_and_feature_importance()
            
            # 第五步：洞察和建议
            self.generate_insights_and_recommendations()
            
            print("\n" + "="*80)
            print("🎉 分析完成!")
            print("="*80)
            print("生成的可视化文件:")
            print("✓ developer_profile_behavioral_features.png")
            print("✓ developer_profile_batch_analysis.png")
            print("✓ developer_profile_correlation_matrix.png")
            
        except Exception as e:
            print(f"❌ 分析过程中出现错误: {e}")
            import traceback
            traceback.print_exc()

# 主程序执行
if __name__ == "__main__":
    # 初始化分析器
    analyzer = DeveloperProfileAnalyzer('data/developer_profile_final/merged_developer_profile_cleaned.csv')
    
    # 运行完整分析
    analyzer.run_full_analysis() 