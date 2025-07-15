#!/usr/bin/env python3
"""
Main execution script for Apache Kafka Jira data collection.

This script provides a simple interface to collect Jira data from the
Apache Kafka project for developer productivity analysis.

Usage:
    python run_kafka_collection.py --sample
    python run_kafka_collection.py --days 30
    python run_kafka_collection.py --validate
"""

import sys
import os
import logging
from pathlib import Path

# Add the parent directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data_acquisition.jira_project.kafka_collector import KafkaJiraCollector


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('kafka_collection.log')
        ]
    )


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Collect Jira data from Apache Kafka project',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Collect sample data for testing (7 days)
    python run_kafka_collection.py --sample
    
    # Collect data from last 14 days (default)
    python run_kafka_collection.py
    
    # Collect data from last 30 days
    python run_kafka_collection.py --days 30
    
    # Validate field mapping only
    python run_kafka_collection.py --validate
    
    # Specify custom output directory
    python run_kafka_collection.py --output-dir /path/to/data
        """
    )
    
    parser.add_argument(
        '--days', 
        type=int, 
        default=14,
        help='Number of days to look back for issues (default: 14)'
    )
    
    parser.add_argument(
        '--sample',
        action='store_true',
        help='Collect only sample data for testing (max 7 days)'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate field mapping and API access only'
    )
    
    parser.add_argument(
        '--output-dir',
        default='data',
        help='Output directory for CSV files (default: data)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("="*60)
    logger.info("Apache Kafka Jira Data Collection")
    logger.info("="*60)
    
    try:
        # Create output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(exist_ok=True)
        logger.info(f"Output directory: {output_dir.absolute()}")
        
        # Initialize collector
        logger.info("Initializing Kafka Jira collector...")
        collector = KafkaJiraCollector(output_dir=str(output_dir))
        
        if args.validate:
            logger.info("Running field validation...")
            validation_result = collector.validate_field_mapping()
            logger.info("Field validation completed successfully")
            print("\nValidation Summary:")
            print(f"Custom fields found: {len(validation_result['custom_fields_found'])}")
            for field_name, field_id in validation_result['custom_fields_found'].items():
                print(f"  - {field_name}: {field_id}")
            
        elif args.sample:
            logger.info("Collecting sample data...")
            sample_days = min(args.days, 7)
            results = collector.collect_sample_data(days=sample_days)
            
            print("\nSample Data Collection Summary:")
            for name, df in results.items():
                if not df.empty:
                    print(f"  - {name}: {len(df)} records")
            
        else:
            logger.info(f"Collecting full data for {args.days} days...")
            results = collector.collect_kafka_performance_data(days=args.days)
            
            print("\nData Collection Summary:")
            total_records = sum(len(df) for df in results.values())
            print(f"Total records collected: {total_records}")
            
            for name, df in results.items():
                if not df.empty:
                    print(f"  - {name}: {len(df)} records")
                    print(f"    Columns: {', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}")
        
        print(f"\nFiles saved to: {output_dir.absolute()}")
        print("\nCollection completed successfully! 🎉")
        
    except KeyboardInterrupt:
        logger.info("Collection interrupted by user")
        print("\nCollection interrupted by user.")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Collection failed: {str(e)}", exc_info=True)
        print(f"\nError: {str(e)}")
        print("Check kafka_collection.log for detailed error information.")
        sys.exit(1)


if __name__ == "__main__":
    main() 