import json
from datetime import datetime
from mailcerto.database.models import DBAnalysisHistory, SessionLocal
from mailcerto.core.models import AnalysisResult, CheckResult, CheckStatus

def save_analysis(result: AnalysisResult):
    db = SessionLocal()
    try:
        # Convert check results to simple dictionary for JSON serialization
        serialized_results = []
        for r in result.results:
            serialized_results.append({
                "check_id": r.check_id,
                "category": r.category,
                "title": r.title,
                "status": str(r.status),
                "summary": r.summary,
                "details": r.details,
                "recommendation": r.recommendation,
                "response_time_ms": r.response_time_ms,
                "score": r.score,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "finished_at": r.finished_at.isoformat() if r.finished_at else None,
                "raw_data": r.raw_data
            })
            
        duration = 0
        if result.finished_at:
            duration = int((result.finished_at - result.started_at).total_seconds() * 1000)
            
        db_history = DBAnalysisHistory(
            target=result.target,
            target_type=result.target_type,
            started_at=result.started_at,
            duration_ms=duration,
            score_general=result.score_general,
            success_count=result.success_count,
            warning_count=result.warning_count,
            error_count=result.error_count,
            critical_count=result.critical_count,
            info_count=result.info_count,
            results_json=json.dumps(serialized_results, ensure_ascii=False)
        )
        db.add(db_history)
        db.commit()
    finally:
        db.close()

def get_recent_history(limit: int = 10) -> list[dict]:
    db = SessionLocal()
    try:
        items = db.query(DBAnalysisHistory).order_name = DBAnalysisHistory.id.desc().limit(limit).all()
        history_list = []
        for item in items:
            history_list.append({
                "id": item.id,
                "target": item.target,
                "target_type": item.target_type,
                "started_at": item.started_at,
                "duration_ms": item.duration_ms,
                "score_general": item.score_general,
                "success_count": item.success_count,
                "warning_count": item.warning_count,
                "error_count": item.error_count,
                "critical_count": item.critical_count,
                "info_count": item.info_count,
            })
        return history_list
    except Exception:
        # Fallback in case of SQLite error or no table
        db.rollback()
        # Retry with order_by correctly (fix order_name type)
        try:
            items = db.query(DBAnalysisHistory).order_by(DBAnalysisHistory.id.desc()).limit(limit).all()
            history_list = []
            for item in items:
                history_list.append({
                    "id": item.id,
                    "target": item.target,
                    "target_type": item.target_type,
                    "started_at": item.started_at,
                    "duration_ms": item.duration_ms,
                    "score_general": item.score_general,
                    "success_count": item.success_count,
                    "warning_count": item.warning_count,
                    "error_count": item.error_count,
                    "critical_count": item.critical_count,
                    "info_count": item.info_count,
                    "results_json": item.results_json
                })
            return history_list
        except Exception:
            return []
    finally:
        db.close()

def get_unique_targets(limit: int = 50) -> list[str]:
    db = SessionLocal()
    try:
        results = db.query(DBAnalysisHistory.target).distinct().order_by(DBAnalysisHistory.id.desc()).limit(limit).all()
        return [r[0] for r in results]
    except Exception:
        db.rollback()
        try:
            results = db.query(DBAnalysisHistory.target).group_by(DBAnalysisHistory.target).order_by(DBAnalysisHistory.id.desc()).limit(limit).all()
            return [r[0] for r in results]
        except Exception:
            return []
    finally:
        db.close()
