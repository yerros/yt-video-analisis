"""CLI commands for database export/import."""

import json
from pathlib import Path
from datetime import datetime
import click
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from db.session import sync_engine, SyncSessionLocal
from models.job import Job
from core.config import settings


@click.group()
def cli():
    """Database export/import commands."""
    pass


@cli.command()
@click.option('--output', '-o', default=None, help='Output SQL file path')
@click.option('--status', default='done', help='Filter by job status (default: done)')
def export_db(output: str, status: str):
    """Export jobs data to SQL file for easy migration."""
    session = SyncSessionLocal()
    
    try:
        # Query jobs
        if status:
            jobs = session.query(Job).filter(Job.status == status).all()
        else:
            jobs = session.query(Job).all()
        
        if not jobs:
            click.echo(f"No jobs found with status: {status}")
            return
        
        # Create output file
        if output is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output = f"export_jobs_{timestamp}.sql"
        
        output_path = Path(output)
        
        # Generate SQL INSERT statements
        with output_path.open('w') as f:
            f.write("-- Video Analysis Jobs Export\n")
            f.write(f"-- Generated: {datetime.now().isoformat()}\n")
            f.write(f"-- Total jobs: {len(jobs)}\n\n")
            
            f.write("-- Disable triggers during import\n")
            f.write("SET session_replication_role = 'replica';\n\n")
            
            for job in jobs:
                # Serialize job data
                embedding_str = "NULL"
                if job.embedding is not None:
                    # Convert vector to array literal
                    embedding_list = [float(x) for x in str(job.embedding).strip("[]").split(",")]
                    embedding_str = f"ARRAY{embedding_list}::vector"
                
                # Escape strings for SQL
                def escape_sql(value):
                    if value is None:
                        return "NULL"
                    if isinstance(value, str):
                        return "'" + value.replace("'", "''").replace("\\", "\\\\") + "'"
                    if isinstance(value, (dict, list)):
                        return "'" + json.dumps(value).replace("'", "''") + "'::jsonb"
                    if isinstance(value, datetime):
                        return f"'{value.isoformat()}'"
                    if isinstance(value, bool):
                        return str(value).upper()
                    return str(value)
                
                # Build INSERT statement
                sql = f"""
INSERT INTO jobs (
    id, youtube_url, video_title, video_duration,
    youtube_metadata, channel_title, channel_id, description,
    tags, category_id, published_at, view_count, like_count, comment_count,
    thumbnail_url, title_en, description_en, disable_transcript,
    status, progress, transcript, frames_count, analysis, error_message,
    embedding, created_at, updated_at
) VALUES (
    {escape_sql(str(job.id))},
    {escape_sql(job.youtube_url)},
    {escape_sql(job.video_title)},
    {escape_sql(job.video_duration)},
    {escape_sql(job.youtube_metadata)},
    {escape_sql(job.channel_title)},
    {escape_sql(job.channel_id)},
    {escape_sql(job.description)},
    {escape_sql(job.tags)},
    {escape_sql(job.category_id)},
    {escape_sql(job.published_at)},
    {escape_sql(job.view_count)},
    {escape_sql(job.like_count)},
    {escape_sql(job.comment_count)},
    {escape_sql(job.thumbnail_url)},
    {escape_sql(job.title_en)},
    {escape_sql(job.description_en)},
    {escape_sql(job.disable_transcript)},
    {escape_sql(job.status)},
    {escape_sql(job.progress)},
    {escape_sql(job.transcript)},
    {escape_sql(job.frames_count)},
    {escape_sql(job.analysis)},
    {escape_sql(job.error_message)},
    {embedding_str},
    {escape_sql(job.created_at)},
    {escape_sql(job.updated_at)}
) ON CONFLICT (id) DO UPDATE SET
    video_title = EXCLUDED.video_title,
    status = EXCLUDED.status,
    progress = EXCLUDED.progress,
    analysis = EXCLUDED.analysis,
    updated_at = EXCLUDED.updated_at;
"""
                f.write(sql)
                f.write("\n")
            
            f.write("\n-- Re-enable triggers\n")
            f.write("SET session_replication_role = 'origin';\n")
        
        click.echo(f"✅ Exported {len(jobs)} jobs to: {output_path.absolute()}")
        click.echo(f"📦 File size: {output_path.stat().st_size / 1024:.2f} KB")
        
    finally:
        session.close()


@cli.command()
@click.argument('sql_file')
@click.option('--dry-run', is_flag=True, help='Show what would be imported without executing')
def import_db(sql_file: str, dry_run: bool):
    """Import jobs data from SQL file."""
    sql_path = Path(sql_file)
    
    if not sql_path.exists():
        click.echo(f"❌ File not found: {sql_file}")
        return
    
    session = SyncSessionLocal()
    
    try:
        # Read SQL file
        sql_content = sql_path.read_text()
        
        if dry_run:
            click.echo("🔍 Dry run mode - showing SQL preview:\n")
            click.echo(sql_content[:1000])
            click.echo("\n... (truncated)")
            return
        
        # Execute SQL
        click.echo(f"📥 Importing from: {sql_path.absolute()}")
        
        # Split by statements and execute
        statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
        
        for i, statement in enumerate(statements):
            if statement:
                try:
                    session.execute(text(statement))
                    if (i + 1) % 10 == 0:
                        click.echo(f"   Processed {i + 1}/{len(statements)} statements...")
                except Exception as e:
                    click.echo(f"⚠️  Error at statement {i + 1}: {str(e)[:100]}")
                    if "duplicate key" not in str(e).lower():
                        raise
        
        session.commit()
        click.echo(f"✅ Import completed successfully!")
        
    except Exception as e:
        session.rollback()
        click.echo(f"❌ Import failed: {str(e)}")
        raise
    finally:
        session.close()


@cli.command()
def stats():
    """Show database statistics."""
    session = SyncSessionLocal()
    
    try:
        total_jobs = session.query(Job).count()
        done_jobs = session.query(Job).filter(Job.status == "done").count()
        pending_jobs = session.query(Job).filter(Job.status == "pending").count()
        failed_jobs = session.query(Job).filter(Job.status == "failed").count()
        
        click.echo("\n📊 Database Statistics:")
        click.echo(f"   Total jobs: {total_jobs}")
        click.echo(f"   ✅ Done: {done_jobs}")
        click.echo(f"   ⏳ Pending: {pending_jobs}")
        click.echo(f"   ❌ Failed: {failed_jobs}")
        click.echo()
        
    finally:
        session.close()


if __name__ == '__main__':
    cli()
