"""Test history with explicit game links and conservative legacy attribution."""
from collections import defaultdict

from sqlalchemy.orm import joinedload, selectinload

import models


def test_history(db, child_id, result_for_score, include_details=True, offset=0, limit=None):
    query = db.query(models.ChildTestSession).filter(
        models.ChildTestSession.child_id == child_id,
    ).options(
        joinedload(models.ChildTestSession.question_set).selectinload(models.SkillQuestionSet.questions),
    ).order_by(models.ChildTestSession.start_time.desc(), models.ChildTestSession.id.desc())
    if include_details:
        query = query.options(selectinload(models.ChildTestSession.answers).joinedload(models.TestAnswer.question))
    else:
        query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
    sessions = query.all()
    responses = db.query(models.GameResponse).filter(
        models.GameResponse.child_id == child_id,
    ).options(joinedload(models.GameResponse.game)).order_by(models.GameResponse.timestamp.asc()).all() if include_details else []
    by_skill = defaultdict(list)
    for session in sessions:
        if session.is_completed and session.question_set:
            by_skill[session.question_set.skill_category].append(session)
    games_by_session = defaultdict(dict)
    for response in responses:
        if not response.game:
            continue
        session_id = response.test_session_id
        if session_id is None:
            candidates = [s for s in by_skill[response.game.skill_category]
                          if (s.completed_at or s.start_time) <= response.timestamp]
            if not candidates:
                continue
            session_id = max(candidates, key=lambda s: (s.completed_at or s.start_time, s.id)).id
        games_by_session[session_id][response.game_id] = {
            "id": response.game_id,
            "title": response.game.title,
            "description": response.game.description,
            "image_url": response.game.image_url,
            "response": response.response,
            "played_at": response.timestamp,
            "link_inferred": response.test_session_id is None,
        }
    history = []
    for session in sessions:
        question_set = session.question_set
        if not question_set:
            continue
        maximum = sum(q.score_A for q in question_set.questions) or 1
        result = result_for_score((session.total_score or 0) / maximum * 100, question_set.skill_category)
        history.append({
            "id": session.id, "started_at": session.start_time,
            "completed_at": session.completed_at, "is_completed": session.is_completed,
            "skill_category": question_set.skill_category, "set_name": question_set.name,
            "score": session.total_score or 0, "max_score": maximum,
            "status": result["status"] if session.is_completed else "ناتمام",
            "status_color": result["color"] if session.is_completed else "pending",
            "suggestion": result["suggestion"] if session.is_completed else "",
            "answers": [{"question": a.question.text, "answer": a.chosen_option_text or a.chosen_option}
                        for a in sorted((a for a in session.answers if a.question), key=lambda a: a.question.order_index)] if include_details else [],
            "games": list(games_by_session[session.id].values()),
        })
    return history
