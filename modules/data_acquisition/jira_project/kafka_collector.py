"""
Kafka Project Jira Data Collector

Specific implementation for collecting data from Apache Kafka Jira project
at https://issues.apache.org/jira/projects/KAFKA
"""

import os
import logging
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime

from .jira_client import JiraClient, JiraConfig
from .data_collector import JiraDataCollector

logger = logging.getLogger(__name__)


class KafkaJiraCollector:
    """
    Specialized collector for Apache Kafka Jira project.
    
    Configured for public Apache Kafka Jira instance with project-specific
    optimizations and field mappings.
    """
    
    # Apache Kafka Jira configuration
    KAFKA_BASE_URL = "https://issues.apache.org/jira"
    KAFKA_PROJECT_KEY = "KAFKA"
    
    def __init__(self, output_dir: str = "data"):
        """
        Initialize Kafka Jira collector.
        
        Args:
            output_dir: Directory to save CSV files
        """
        self.output_dir = output_dir
        
        # Create Jira configuration for Apache Kafka (anonymous access)
        self.config = JiraConfig(
            base_url=self.KAFKA_BASE_URL,
            username=os.getenv("JIRA_USER"),  # Optional for public access
            token=os.getenv("JIRA_TOKEN"),    # Optional for public access
            rate_limit_delay=0.5,  # Be respectful to Apache infrastructure
            max_results=50,        # Smaller batches for public API
            timeout=60             # Longer timeout for external API
        )
        
        # Initialize client and collector
        self.client = JiraClient(self.config)
        self.collector = JiraDataCollector(self.client, output_dir)
        
        logger.info(f"Initialized Kafka Jira collector for {self.KAFKA_BASE_URL}")
    
    def collect_recent_kafka_issues(self, days: int = 14) -> pd.DataFrame:
        """
        Collect recent Kafka issues with project-specific filtering.
        
        Args:
            days: Number of days to look back
            
        Returns:
            DataFrame with Kafka issue data
        """
        logger.info(f"Collecting Kafka issues from last {days} days")
        
        # Kafka-specific JQL filters
        additional_jql = 'issuetype != "Dependency upgrade"'  # Filter out dependency updates
        
        return self.collector.collect_recent_issues(
            project_key=self.KAFKA_PROJECT_KEY,
            days=days,
            additional_jql=additional_jql
        )
    
    def collect_kafka_bugs_and_improvements(self, days: int = 30) -> pd.DataFrame:
        """
        Collect bugs and improvements specifically for quality metrics.
        
        Args:
            days: Number of days to look back
            
        Returns:
            DataFrame with bug and improvement data
        """
        logger.info("Collecting Kafka bugs and improvements")
        
        additional_jql = 'issuetype in ("Bug", "Improvement", "New Feature")'
        
        return self.collector.collect_recent_issues(
            project_key=self.KAFKA_PROJECT_KEY,
            days=days,
            additional_jql=additional_jql
        )
    
    def collect_kafka_performance_data(self, days: int = 30) -> Dict[str, pd.DataFrame]:
        """
        Collect comprehensive data for Kafka performance analysis.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary containing all performance-related DataFrames
        """
        logger.info("Starting comprehensive Kafka data collection for performance analysis")
        
        results = {}
        
        try:
            # 1. Recent issues for CTL calculation
            logger.info("Collecting recent issues...")
            results['recent_issues'] = self.collect_recent_kafka_issues(days)
            
            # 2. Bugs and improvements for quality metrics
            logger.info("Collecting bugs and improvements...")
            results['bugs_improvements'] = self.collect_kafka_bugs_and_improvements(days)
            
            # 3. Worklog data for CSI calculation
            logger.info("Collecting worklog data...")
            results['worklogs'] = self.collector.collect_worklog_data(self.KAFKA_PROJECT_KEY, days)
            
            # 4. Status history for reopening analysis
            logger.info("Collecting status change history...")
            results['status_history'] = self.collector.collect_status_history(self.KAFKA_PROJECT_KEY, days)
            
            # 5. Board and sprint data for PS calculation
            logger.info("Collecting board and sprint data...")
            try:
                boards_df, sprints_df, sprint_issues_df = self.collector.collect_board_and_sprint_data(self.KAFKA_PROJECT_KEY)
                results['boards'] = boards_df
                results['sprints'] = sprints_df
                results['sprint_issues'] = sprint_issues_df
            except Exception as e:
                logger.warning(f"Could not collect sprint data (may not be available for this project): {str(e)}")
                results['boards'] = pd.DataFrame()
                results['sprints'] = pd.DataFrame()
                results['sprint_issues'] = pd.DataFrame()
            
            # 6. Export all data
            logger.info("Exporting data to CSV files...")
            self.collector.export_to_csv(results, prefix="kafka")
            
            # 7. Generate summary report
            self._generate_summary_report(results)
            
            logger.info("Kafka data collection completed successfully")
            
        except Exception as e:
            logger.error(f"Error during Kafka data collection: {str(e)}")
            raise
        
        return results
    
    def _generate_summary_report(self, results: Dict[str, pd.DataFrame]):
        """
        Generate a summary report of collected data.
        
        Args:
            results: Dictionary of DataFrames
        """
        summary = {
            'collection_timestamp': datetime.now().isoformat(),
            'project_key': self.KAFKA_PROJECT_KEY,
            'base_url': self.KAFKA_BASE_URL,
            'data_summary': {}
        }
        
        for name, df in results.items():
            summary['data_summary'][name] = {
                'record_count': len(df),
                'columns': list(df.columns) if not df.empty else [],
                'memory_usage_mb': round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2)
            }
        
        # Save summary to JSON
        import json
        summary_path = os.path.join(self.output_dir, 'kafka_collection_summary.json')
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Summary report saved to {summary_path}")
        
        # Log key metrics
        total_records = sum(len(df) for df in results.values())
        logger.info(f"Total records collected: {total_records}")
        
        for name, df in results.items():
            if not df.empty:
                logger.info(f"  - {name}: {len(df)} records")
    
    def collect_sample_data(self, days: int = 7) -> Dict[str, pd.DataFrame]:
        """
        Collect a smaller sample of data for testing purposes.
        
        Args:
            days: Number of days to look back (smaller sample)
            
        Returns:
            Dictionary containing sample DataFrames
        """
        logger.info(f"Collecting sample Kafka data from last {days} days")
        
        results = {}
        
        try:
            # Sample recent issues
            results['sample_issues'] = self.collect_recent_kafka_issues(days)
            
            # Sample worklogs
            if not results['sample_issues'].empty:
                results['sample_worklogs'] = self.collector.collect_worklog_data(self.KAFKA_PROJECT_KEY, days)
                results['sample_status_history'] = self.collector.collect_status_history(self.KAFKA_PROJECT_KEY, days)
            
            # Export sample data
            self.collector.export_to_csv(results, prefix="kafka_sample")
            
            logger.info("Sample data collection completed")
            
        except Exception as e:
            logger.error(f"Error during sample data collection: {str(e)}")
            raise
        
        return results
    
    def validate_field_mapping(self) -> Dict[str, Any]:
        """
        Validate and report on available fields in Kafka Jira.
        
        Returns:
            Dictionary with field validation results
        """
        logger.info("Validating Kafka Jira field mapping")
        
        try:
            # Get custom field mapping
            custom_fields = self.collector.custom_fields
            
            # Get sample of fields from a few issues
            sample_jql = f'project = {self.KAFKA_PROJECT_KEY} ORDER BY updated DESC'
            sample_issues = self.client.search_issues(sample_jql, None, None)[:5]  # Get 5 issues
            
            # Analyze available fields
            available_fields = set()
            for issue in sample_issues:
                available_fields.update(issue.get('fields', {}).keys())
            
            validation_result = {
                'custom_fields_found': custom_fields,
                'total_available_fields': len(available_fields),
                'sample_field_names': list(available_fields)[:20],  # First 20 field names
                'validation_timestamp': datetime.now().isoformat()
            }
            
            # Save validation results
            import json
            validation_path = os.path.join(self.output_dir, 'kafka_field_validation.json')
            with open(validation_path, 'w', encoding='utf-8') as f:
                json.dump(validation_result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Field validation completed. Found {len(custom_fields)} custom fields.")
            logger.info(f"Validation results saved to {validation_path}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error during field validation: {str(e)}")
            raise


def main():
    """
    Main execution function for Kafka data collection.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Collect Jira data from Apache Kafka project')
    parser.add_argument('--days', type=int, default=14, 
                       help='Number of days to look back for issues (default: 14)')
    parser.add_argument('--sample', action='store_true',
                       help='Collect only sample data for testing')
    parser.add_argument('--validate', action='store_true',
                       help='Validate field mapping only')
    parser.add_argument('--output-dir', default='data',
                       help='Output directory for CSV files (default: data)')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize collector
        collector = KafkaJiraCollector(output_dir=args.output_dir)
        
        if args.validate:
            # Field validation only
            collector.validate_field_mapping()
        elif args.sample:
            # Sample data collection
            collector.collect_sample_data(days=min(args.days, 7))
        else:
            # Full data collection
            collector.collect_kafka_performance_data(days=args.days)
        
        logger.info("Kafka Jira data collection completed successfully!")
        
    except Exception as e:
        logger.error(f"Failed to collect Kafka data: {str(e)}")
        raise


if __name__ == "__main__":
    main() 