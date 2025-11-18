"""
Job Cleanup Utilities

Provides utilities for cleaning up old jobs and managing data retention.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from db import SessionLocal, OCRJob

logger = logging.getLogger(__name__)

# Configuration
DEFAULT_RETENTION_DAYS = 30  # Keep jobs for 30 days by default
FAILED_JOB_RETENTION_DAYS = 7  # Keep failed jobs for 7 days


def cleanup_old_jobs(
    retention_days: int = DEFAULT_RETENTION_DAYS,
    failed_retention_days: int = FAILED_JOB_RETENTION_DAYS,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Clean up old jobs from the database based on retention policy.

    Args:
        retention_days: Number of days to retain completed/pending jobs
        failed_retention_days: Number of days to retain failed jobs
        dry_run: If True, only report what would be deleted without actually deleting

    Returns:
        Dictionary with cleanup statistics
    """
    logger.info(f"Starting job cleanup (dry_run={dry_run})")

    stats = {
        "completed_deleted": 0,
        "failed_deleted": 0,
        "pending_deleted": 0,
        "total_deleted": 0,
        "errors": 0
    }

    try:
        with SessionLocal() as session:
            # Calculate cutoff dates
            completed_cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
            failed_cutoff = datetime.now(timezone.utc) - timedelta(days=failed_retention_days)

            # Find jobs to delete - completed/successful jobs
            completed_jobs = session.query(OCRJob).filter(
                OCRJob.status == "COMPLETED",
                OCRJob.created_at < completed_cutoff
            ).all()

            stats["completed_deleted"] = len(completed_jobs)
            logger.info(f"Found {len(completed_jobs)} completed jobs older than {retention_days} days")

            # Find jobs to delete - failed jobs
            failed_jobs = session.query(OCRJob).filter(
                OCRJob.status == "FAILED",
                OCRJob.created_at < failed_cutoff
            ).all()

            stats["failed_deleted"] = len(failed_jobs)
            logger.info(f"Found {len(failed_jobs)} failed jobs older than {failed_retention_days} days")

            # Find jobs to delete - stuck pending jobs (> retention_days)
            pending_jobs = session.query(OCRJob).filter(
                OCRJob.status.in_(["PENDING", "PROCESSING"]),
                OCRJob.created_at < completed_cutoff
            ).all()

            stats["pending_deleted"] = len(pending_jobs)
            logger.info(f"Found {len(pending_jobs)} stuck pending jobs older than {retention_days} days")

            # Delete jobs if not dry run
            if not dry_run:
                for job in completed_jobs + failed_jobs + pending_jobs:
                    try:
                        session.delete(job)
                    except Exception as e:
                        logger.error(f"Error deleting job {job.id}: {e}")
                        stats["errors"] += 1

                session.commit()
                logger.info("Job cleanup committed to database")
            else:
                logger.info("Dry run - no jobs deleted")

            stats["total_deleted"] = stats["completed_deleted"] + stats["failed_deleted"] + stats["pending_deleted"]

    except Exception as e:
        logger.error(f"Error during job cleanup: {e}", exc_info=True)
        stats["errors"] += 1
        raise

    logger.info(f"Job cleanup completed: {stats}")
    return stats


def cleanup_jobs_by_status(
    status: str,
    days_old: int = 7,
    dry_run: bool = False
) -> int:
    """
    Clean up jobs with a specific status that are older than a certain number of days.

    Args:
        status: Job status to filter by (e.g., "FAILED", "COMPLETED")
        days_old: Delete jobs older than this many days
        dry_run: If True, only count without deleting

    Returns:
        Number of jobs deleted (or would be deleted in dry run)
    """
    logger.info(f"Cleaning up {status} jobs older than {days_old} days (dry_run={dry_run})")

    try:
        with SessionLocal() as session:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)

            jobs = session.query(OCRJob).filter(
                OCRJob.status == status.upper(),
                OCRJob.created_at < cutoff
            ).all()

            count = len(jobs)

            if not dry_run and count > 0:
                for job in jobs:
                    session.delete(job)
                session.commit()
                logger.info(f"Deleted {count} {status} jobs")
            else:
                logger.info(f"Would delete {count} {status} jobs (dry run)")

            return count

    except Exception as e:
        logger.error(f"Error cleaning up {status} jobs: {e}", exc_info=True)
        raise


def get_job_statistics() -> Dict[str, Any]:
    """
    Get statistics about jobs in the database.

    Returns:
        Dictionary with job statistics by status and age
    """
    try:
        with SessionLocal() as session:
            total = session.query(OCRJob).count()
            pending = session.query(OCRJob).filter(OCRJob.status == "PENDING").count()
            processing = session.query(OCRJob).filter(OCRJob.status == "PROCESSING").count()
            completed = session.query(OCRJob).filter(OCRJob.status == "COMPLETED").count()
            failed = session.query(OCRJob).filter(OCRJob.status == "FAILED").count()

            # Get oldest and newest jobs
            oldest_job = session.query(OCRJob).order_by(OCRJob.created_at.asc()).first()
            newest_job = session.query(OCRJob).order_by(OCRJob.created_at.desc()).first()

            oldest_date = oldest_job.created_at if oldest_job else None
            newest_date = newest_job.created_at if newest_job else None

            return {
                "total": total,
                "by_status": {
                    "pending": pending,
                    "processing": processing,
                    "completed": completed,
                    "failed": failed
                },
                "oldest_job": oldest_date.isoformat() if oldest_date else None,
                "newest_job": newest_date.isoformat() if newest_date else None
            }

    except Exception as e:
        logger.error(f"Error getting job statistics: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # CLI interface for manual cleanup
    import argparse

    parser = argparse.ArgumentParser(description="Clean up old OCR jobs")
    parser.add_argument(
        "--retention-days",
        type=int,
        default=DEFAULT_RETENTION_DAYS,
        help=f"Days to retain completed jobs (default: {DEFAULT_RETENTION_DAYS})"
    )
    parser.add_argument(
        "--failed-retention-days",
        type=int,
        default=FAILED_JOB_RETENTION_DAYS,
        help=f"Days to retain failed jobs (default: {FAILED_JOB_RETENTION_DAYS})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show job statistics"
    )

    args = parser.parse_args()

    if args.stats:
        stats = get_job_statistics()
        print("Job Statistics:")
        print(f"  Total jobs: {stats['total']}")
        print(f"  Pending: {stats['by_status']['pending']}")
        print(f"  Processing: {stats['by_status']['processing']}")
        print(f"  Completed: {stats['by_status']['completed']}")
        print(f"  Failed: {stats['by_status']['failed']}")
        print(f"  Oldest job: {stats['oldest_job']}")
        print(f"  Newest job: {stats['newest_job']}")
    else:
        result = cleanup_old_jobs(
            retention_days=args.retention_days,
            failed_retention_days=args.failed_retention_days,
            dry_run=args.dry_run
        )
        print("Cleanup Results:")
        print(f"  Completed jobs deleted: {result['completed_deleted']}")
        print(f"  Failed jobs deleted: {result['failed_deleted']}")
        print(f"  Pending jobs deleted: {result['pending_deleted']}")
        print(f"  Total deleted: {result['total_deleted']}")
        print(f"  Errors: {result['errors']}")
