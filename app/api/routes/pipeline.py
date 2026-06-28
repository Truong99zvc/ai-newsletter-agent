"""
Pipeline management endpoints.

Provides API to trigger pipeline runs, check status,
and view execution history.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import (
    PipelineRunRequest,
    PipelineRunResponse,
    PipelineRunListResponse,
)
from app.database.connection import get_db
from app.database.repository import Repository
from app.pipeline.orchestrator import PipelineOrchestrator
from app.logging_config import get_logger

router = APIRouter(prefix="/api/v1/pipeline", tags=["pipeline"])
logger = get_logger(__name__)


def _run_pipeline_background(hours: int, top_n: int, send_email: bool):
    """Background task that runs the full pipeline."""
    try:
        orchestrator = PipelineOrchestrator()
        orchestrator.run(hours=hours, top_n=top_n, send_email_flag=send_email)
    except Exception as e:
        logger.error(f"Background pipeline run failed: {e}", exc_info=True)


@router.post("/run", response_model=PipelineRunResponse, status_code=202)
def trigger_pipeline(
    request: PipelineRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Trigger a new pipeline run.

    The pipeline runs in the background. Use the returned run_id
    to poll for status via GET /api/v1/pipeline/status/{run_id}.
    """
    repo = Repository(session=db)

    # Create the run record first so we can return its ID
    run = repo.create_pipeline_run(hours=request.hours, top_n=request.top_n)

    # Schedule the pipeline to run in the background
    background_tasks.add_task(
        _run_pipeline_background,
        hours=request.hours,
        top_n=request.top_n,
        send_email=request.send_email,
    )

    logger.info(
        f"Pipeline run {run.id} triggered (hours={request.hours}, top_n={request.top_n})"
    )

    return PipelineRunResponse(
        run_id=run.id,
        status="pending",
        started_at=run.started_at,
        hours_lookback=run.hours_lookback,
        top_n=run.top_n,
    )


@router.get("/status/{run_id}", response_model=PipelineRunResponse)
def get_pipeline_status(run_id: str, db: Session = Depends(get_db)):
    """Get the status of a specific pipeline run."""
    repo = Repository(session=db)
    run = repo.get_pipeline_run(run_id)

    if not run:
        raise HTTPException(status_code=404, detail=f"Pipeline run {run_id} not found")

    return PipelineRunResponse(
        run_id=run.id,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        duration_seconds=run.duration_seconds,
        hours_lookback=run.hours_lookback,
        top_n=run.top_n,
        current_step=run.current_step,
        steps_completed=run.steps_completed,
        articles_scraped=run.articles_scraped,
        articles_enriched=run.articles_enriched,
        digests_created=run.digests_created,
        email_sent=run.email_sent,
        error_message=run.error_message,
    )


@router.get("/history", response_model=PipelineRunListResponse)
def get_pipeline_history(limit: int = 20, db: Session = Depends(get_db)):
    """Get pipeline execution history."""
    repo = Repository(session=db)
    runs = repo.get_pipeline_runs(limit=limit)

    return PipelineRunListResponse(
        runs=[
            PipelineRunResponse(
                run_id=r.id,
                status=r.status,
                started_at=r.started_at,
                completed_at=r.completed_at,
                duration_seconds=r.duration_seconds,
                hours_lookback=r.hours_lookback,
                top_n=r.top_n,
                current_step=r.current_step,
                steps_completed=r.steps_completed,
                articles_scraped=r.articles_scraped,
                articles_enriched=r.articles_enriched,
                digests_created=r.digests_created,
                email_sent=r.email_sent,
                error_message=r.error_message,
            )
            for r in runs
        ],
        total=len(runs),
    )
