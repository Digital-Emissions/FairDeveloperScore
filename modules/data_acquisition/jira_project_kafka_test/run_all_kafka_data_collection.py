#!/usr/bin/env python3
"""
Master script to run all Kafka Jira data collection scripts.

This script runs all the individual data collection scripts in sequence
to gather comprehensive Jira data for the Apache Kafka project.
"""

import subprocess
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# List of scripts to run (in order)
SCRIPTS = [
    "kafka_jira_to_csv.py",                    # Main issues data
    "kafka_jira_status_history_to_csv.py",     # Status change history
    "kafka_jira_worklogs_to_csv.py",           # Worklog data (may be empty)
]

def run_script(script_name):
    """Run a single data collection script."""
    logger.info(f"Running {script_name}...")
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, check=True)
        logger.info(f"✅ {script_name} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {script_name} failed with exit code {e.returncode}")
        if e.stdout:
            logger.error(f"STDOUT: {e.stdout}")
        if e.stderr:
            logger.error(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error running {script_name}: {str(e)}")
        return False

def main():
    """Run all data collection scripts."""
    logger.info("🚀 Starting Kafka Jira data collection...")
    logger.info("="*60)
    
    success_count = 0
    total_count = len(SCRIPTS)
    
    for script in SCRIPTS:
        if run_script(script):
            success_count += 1
        logger.info("-" * 40)
    
    # Summary
    logger.info("="*60)
    logger.info(f"📊 Data collection summary:")
    logger.info(f"   ✅ Successful: {success_count}/{total_count}")
    logger.info(f"   ❌ Failed: {total_count - success_count}/{total_count}")
    
    # Check output files
    output_dir = Path("../../../data/jira_project_data")
    if output_dir.exists():
        csv_files = list(output_dir.glob("*.csv"))
        logger.info(f"📁 Output files created: {len(csv_files)}")
        for csv_file in csv_files:
            file_size = csv_file.stat().st_size
            logger.info(f"   📄 {csv_file.name}: {file_size:,} bytes")
    else:
        logger.warning("Output directory not found!")
    
    if success_count == total_count:
        logger.info("🎉 All data collection scripts completed successfully!")
        return 0
    else:
        logger.warning("⚠️  Some scripts failed. Check logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 