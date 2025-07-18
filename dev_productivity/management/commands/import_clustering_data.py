import csv
import os
from datetime import datetime, timezone
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone as django_timezone

from dev_productivity.models import LinuxKernelCommit, BatchStatistics


class Command(BaseCommand):
    help = 'Import Linux kernel commits clustering data from CSV file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='data/github_commit_data_test/linux_kernel_commits_clustered.csv',
            help='Path to the CSV file containing clustering data'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing data before importing'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        clear_existing = options['clear_existing']

        # Check if file exists
        if not os.path.exists(csv_file):
            raise CommandError(f'CSV file not found: {csv_file}')

        # Clear existing data if requested
        if clear_existing:
            self.stdout.write('Clearing existing data...')
            LinuxKernelCommit.objects.all().delete()
            BatchStatistics.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        # Import data
        self.stdout.write(f'Importing data from {csv_file}...')
        
        commits_imported = 0
        batch_stats = {}

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                with transaction.atomic():
                    for row in reader:
                        # Convert timestamp
                        commit_timestamp = datetime.fromtimestamp(
                            int(row['commit_ts_utc']), 
                            tz=timezone.utc
                        )
                        
                        # Handle time deltas
                        dt_prev_commit_sec = None
                        if row['dt_prev_commit_sec'] and row['dt_prev_commit_sec'].strip():
                            try:
                                dt_prev_commit_sec = float(row['dt_prev_commit_sec'])
                            except ValueError:
                                dt_prev_commit_sec = None
                        
                        dt_prev_author_sec = None
                        if row['dt_prev_author_sec'] and row['dt_prev_author_sec'].strip():
                            try:
                                dt_prev_author_sec = float(row['dt_prev_author_sec'])
                            except ValueError:
                                dt_prev_author_sec = None

                        # Create commit object
                        commit = LinuxKernelCommit(
                            hash=row['hash'],
                            author_name=row['author_name'],
                            author_email=row['author_email'],
                            commit_timestamp=commit_timestamp,
                            dt_prev_commit_sec=dt_prev_commit_sec,
                            dt_prev_author_sec=dt_prev_author_sec,
                            files_changed=int(row['files_changed']) if row['files_changed'] else 0,
                            insertions=int(row['insertions']) if row['insertions'] else 0,
                            deletions=int(row['deletions']) if row['deletions'] else 0,
                            is_merge=bool(int(row['is_merge'])) if row['is_merge'] else False,
                            dirs_touched=row['dirs_touched'] or '',
                            file_types=row['file_types'] or '',
                            msg_subject=row['msg_subject'] or '',
                            batch_id=int(row['batch_id'])
                        )
                        
                        commit.save()
                        commits_imported += 1
                        
                        # Collect batch statistics
                        batch_id = int(row['batch_id'])
                        if batch_id not in batch_stats:
                            batch_stats[batch_id] = {
                                'commits': [],
                                'total_insertions': 0,
                                'total_deletions': 0,
                                'total_files': 0,
                                'author_name': row['author_name'],
                                'author_email': row['author_email']
                            }
                        
                        batch_stats[batch_id]['commits'].append(commit_timestamp)
                        batch_stats[batch_id]['total_insertions'] += commit.insertions
                        batch_stats[batch_id]['total_deletions'] += commit.deletions
                        batch_stats[batch_id]['total_files'] += commit.files_changed
                        
                        if commits_imported % 100 == 0:
                            self.stdout.write(f'Imported {commits_imported} commits...')

            # Create batch statistics
            self.stdout.write('Creating batch statistics...')
            batch_stats_created = 0
            
            with transaction.atomic():
                for batch_id, stats in batch_stats.items():
                    if stats['commits']:
                        start_time = min(stats['commits'])
                        end_time = max(stats['commits'])
                        duration = (end_time - start_time).total_seconds()
                        
                        batch_stat = BatchStatistics(
                            batch_id=batch_id,
                            commit_count=len(stats['commits']),
                            total_insertions=stats['total_insertions'],
                            total_deletions=stats['total_deletions'],
                            total_files_changed=stats['total_files'],
                            start_time=start_time,
                            end_time=end_time,
                            duration_seconds=duration,
                            primary_author_name=stats['author_name'],
                            primary_author_email=stats['author_email']
                        )
                        batch_stat.save()
                        batch_stats_created += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully imported {commits_imported} commits and created {batch_stats_created} batch statistics.'
                )
            )

        except Exception as e:
            raise CommandError(f'Error importing data: {e}') 