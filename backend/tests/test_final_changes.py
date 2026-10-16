import os
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from pathlib import Path
from threading import Event
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DATABASE_URL"] = "sqlite:///" + (Path(tempfile.mkdtemp(prefix="neurochi-tests-")) / "bootstrap.db").as_posix()

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import database
import main
import landing_chat
import models


@pytest.fixture
def setup(tmp_path, monkeypatch):
    engine = create_engine("sqlite:///" + (tmp_path / "case.db").as_posix(), connect_args={"check_same_thread": False})
    models.Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(landing_chat, "SessionLocal", factory)
    def get_db():
        with factory() as db:
            yield db
    main.app.dependency_overrides[database.get_db] = get_db
    monkeypatch.setattr(main, "get_rag_documents", lambda *args, **kwargs: [])
    monkeypatch.setattr(main, "call_liara_chat_completion", lambda *args, **kwargs: "پاسخ آزمایشی کامل.")
    with factory() as db:
        parent = models.User(phone_number="09999990001", parent_name="والد آزمایشی")
        stranger = models.User(phone_number="09999990002", parent_name="والد دوم")
        db.add_all([parent, stranger]); db.flush()
        child = models.Child(user_id=parent.id, name="کودک آزمایشی", gender="دختر", birth_date=date.today() - timedelta(days=1065), gestation_week=38)
        db.add(child); db.flush()
        question_set = models.SkillQuestionSet(name="fixture_fine", skill_category="مهارت های حرکتی ریز", min_age_days=1, max_age_days=2000)
        db.add(question_set); db.flush()
        question = models.Question(question_set_id=question_set.id, order_index=1, text="پرسش آزمایشی", score_A=10, score_B=5, score_C=0, option_A="بله", option_B="گاهی", option_C="هنوز نه")
        db.add(question); db.flush()
        test = models.ChildTestSession(child_id=child.id, question_set_id=question_set.id, is_completed=True, total_score=5, start_time=datetime.utcnow()-timedelta(days=2), completed_at=datetime.utcnow()-timedelta(days=1))
        db.add(test); db.flush()
        db.add(models.TestAnswer(session_id=test.id, question_id=question.id, chosen_option="B", chosen_option_text="گاهی", score_awarded=5))
        game = models.Game(title="بازی آزمایشی", description="شرح بازی", skill_category=question_set.skill_category, min_age_days=1, max_age_days=2000)
        db.add(game); db.flush()
        db.add(models.GameResponse(child_id=child.id, game_id=game.id, test_session_id=test.id, response="cannot_do"))
        db.commit()
        ids = child.id, test.id, parent.id
    client = TestClient(main.app)
    yield client, factory, ids
    main.app.dependency_overrides.clear()
    engine.dispose()


def test_history_ownership_and_games(setup):
    client, factory, (child, test, _) = setup
    url = f"/children/{child}/test-history"
    result = client.get(url, params={"phone_number": "09999990001"})
    assert result.status_code == 200
    assert result.json()["tests"][0]["id"] == test
    detail = client.get(url+f"/{test}", params={"phone_number": "09999990001"}).json()
    assert detail["games"][0]["response"] == "cannot_do"
    assert detail["answers"][0]["answer"] == "گاهی"
    assert client.get(url, params={"phone_number": "09999990002"}).status_code == 404


def test_landing_handoff_idempotent_and_general(setup):
    client, factory, (_, _, parent) = setup
    payload = {"phone_number": "09999990001", "request_id": str(uuid4()), "question": "چگونه به کودکم کمک کنم راحت بخوابد؟"}
    first = client.post('/landing-chat', json=payload)
    assert first.status_code == 202
    assert client.post('/landing-chat', json=payload).json()["chat_session_id"] == first.json()["chat_session_id"]
    for _ in range(50):
        status = client.get('/landing-chat/'+payload['request_id'], params={"phone_number": payload['phone_number']}).json()
        if status['status'] in ('completed', 'failed'): break
        time.sleep(.02)
    assert status['status'] == 'completed', status
    with factory() as db:
        session = db.get(models.ChatSession, status['chat_session_id'])
        assert session.child_id is None
        assert db.query(models.ChatMessage).filter_by(session_id=session.id).count() == 2
    assert client.get('/landing-chat/'+payload['request_id'], params={"phone_number": "09999990002"}).status_code == 404


def test_onboarding_required_for_handoff(setup):
    client, _, _ = setup
    response = client.post('/landing-chat', json={"phone_number": "09999990002", "request_id": str(uuid4()), "question": "سؤال آزمایشی"})
    assert response.status_code == 409


def test_explicit_test_navigation_without_llm(setup, monkeypatch):
    client, _, (child, _, _) = setup
    def no_llm(*args, **kwargs): raise AssertionError('Navigation must not call model')
    monkeypatch.setattr(main, 'call_liara_chat_completion', no_llm)
    response = client.post('/chat', json={"phone_number":"09999990001", "child_id":child, "message":"من را به تست حرکات ظریف هدایت کن"})
    assert response.status_code == 200
    assert response.json()['suggested_test']['skill_category'] == 'مهارت های حرکتی ریز'
    assert not main.assessment_intent('آیا نتیجه تست به معنای تشخیص مشکل کودک است؟')[0]
    assert not main.assessment_intent('ASQ چیست؟')[0]
    assert not main.assessment_intent('نتیجه تست چیه؟')[0]


def test_slow_retrieval_does_not_block_other_api(setup, monkeypatch):
    client, _, _ = setup
    entered = Event()
    def slow(*args, **kwargs): entered.set(); time.sleep(.4); return []
    monkeypatch.setattr(main, 'get_rag_documents', slow)
    with ThreadPoolExecutor() as pool:
        result = pool.submit(client.post, '/chat', json={"phone_number":"09999990001", "message":"یک سؤال معمولی درباره خواب کودک"})
        assert entered.wait(2)
        started = time.perf_counter()
        assert client.get('/health').status_code == 200
        assert time.perf_counter()-started < .25
        assert result.result().status_code == 200


def test_sqlite_write_lock_released_before_model(setup, monkeypatch):
    client, factory, (child, _, _) = setup
    entered = Event()
    def slow_model(*args, **kwargs): entered.set(); time.sleep(.4); return 'پاسخ آزمایشی'
    monkeypatch.setattr(main, 'call_liara_chat_completion', slow_model)
    with ThreadPoolExecutor() as pool:
        result = pool.submit(client.post, '/chat', json={"phone_number":"09999990001", "child_id":child, "message":"سؤال معمولی درباره خواب"})
        assert entered.wait(2)
        started = time.perf_counter()
        response = client.post('/chat-sessions', params={"phone_number":"09999990001"}, json={"title":"گفتگوی هم‌زمان"})
        assert response.status_code == 200
        assert time.perf_counter()-started < .25
        assert result.result().status_code == 200


def test_audio_general_session_and_sources(setup, monkeypatch):
    client, factory, _ = setup
    async def transcribe(path): return 'سؤال معمولی درباره خواب'
    monkeypatch.setattr(main, 'call_liara_for_transcribe', transcribe)
    response = client.post('/transcribe-audio', params={'phone_number':'09999990001'}, files={'file':('fixture.wav', b'RIFF-test-fixture', 'audio/wav')})
    assert response.status_code == 200, response.text
    assert response.json()['bot_response'] == 'پاسخ آزمایشی کامل.'
    with factory() as db:
        session = db.get(models.ChatSession, response.json()['chat_session_id'])
        assert session.child_id is None


def test_deleting_session_removes_landing_job_and_messages(setup):
    client, factory, (_, _, parent) = setup
    with factory() as db:
        session=models.ChatSession(user_id=parent, child_id=None, title='گفتگوی آزمایشی')
        db.add(session); db.flush(); sid=session.id
        db.add(models.LandingChatJob(user_id=parent, request_id=str(uuid4()), session_id=sid, question='سؤال', status='completed'))
        db.add(models.ChatMessage(user_id=parent,session_id=sid,role='assistant',content='پاسخ',sources_json='[]'));db.commit()
    assert client.delete(f'/chat-sessions/{sid}',params={'phone_number':'09999990002'}).status_code==404
    assert client.delete(f'/chat-sessions/{sid}',params={'phone_number':'09999990001'}).status_code==204
    with factory() as db:
        assert db.query(models.ChatMessage).filter_by(session_id=sid).count()==0
        assert db.query(models.LandingChatJob).filter_by(session_id=sid).count()==0


def test_landing_failed_generation_can_retry_without_new_session(setup, monkeypatch):
    client, factory, _ = setup
    def fail(*args, **kwargs): raise RuntimeError('Synthetic provider failure')
    monkeypatch.setattr(main,'call_liara_chat_completion',fail)
    payload={'phone_number':'09999990001','request_id':str(uuid4()),'question':'سؤال معمولی درباره خواب'}
    first=client.post('/landing-chat',json=payload).json()
    for _ in range(100):
        state=client.get('/landing-chat/'+payload['request_id'],params={'phone_number':payload['phone_number']}).json()
        if state['status']=='failed': break
        time.sleep(.01)
    assert state['status']=='failed'
    monkeypatch.setattr(main,'call_liara_chat_completion',lambda *args,**kwargs:'پاسخ پس از تلاش دوباره')
    second=client.post('/landing-chat',json={**payload,'retry':True}).json()
    assert second['chat_session_id']==first['chat_session_id']
    for _ in range(100):
        state=client.get('/landing-chat/'+payload['request_id'],params={'phone_number':payload['phone_number']}).json()
        if state['status']=='completed': break
        time.sleep(.01)
    assert state['status']=='completed'
    with factory() as db:
        assert db.query(models.ChatMessage).filter_by(session_id=state['chat_session_id']).count()==2


def test_restart_recovery_does_not_regenerate_saved_answer(setup, monkeypatch):
    client, factory, (_, _, parent) = setup
    with factory() as db:
        session=models.ChatSession(user_id=parent,child_id=None,title='پاسخ ذخیره‌شده');db.add(session);db.flush()
        job=models.LandingChatJob(user_id=parent,request_id=str(uuid4()),session_id=session.id,question='سؤال',status='running');db.add(job)
        db.add_all([models.ChatMessage(user_id=parent,session_id=session.id,role='user',content='سؤال'),models.ChatMessage(user_id=parent,session_id=session.id,role='assistant',content='پاسخ')]);db.commit();jid=job.id;sid=session.id
    def forbidden(*args,**kwargs): raise AssertionError('Must not regenerate a saved answer')
    landing_chat.resume_jobs(forbidden)
    for _ in range(100):
        with factory() as db:
            state=db.get(models.LandingChatJob,jid).status
        if state=='completed':break
        time.sleep(.01)
    assert state=='completed'
    with factory() as db:
        assert db.query(models.ChatMessage).filter_by(session_id=sid).count()==2


def test_query_preserves_explicit_age_and_calendar_months(monkeypatch):
    class FixedDate(date):
        @classmethod
        def today(cls): return cls(2026,10,13)
    monkeypatch.setattr(main,'date',FixedDate)
    assert main._child_age_search_phrase(1065)=='۳۵ ماهه'
    query='غذای کمکی نوزاد شش ماهه را چگونه شروع کنم؟'
    assert main.build_rag_search_query(query,child_age_days=1065)==query
    # The question's age governs retrieval; the profile is still factual context.
    class FakeRetriever:
        def retrieve_documents(self, query, **kwargs):
            assert kwargs['child_age_days']==182
            assert '۳۵ ماهه' not in query
            return []
    monkeypatch.setattr(main,'retrieval_manager',FakeRetriever())
    assert main.get_rag_documents(query,child_age_days=1065)==[]


def test_bridge_outputs_one_persian_question(monkeypatch):
    monkeypatch.setattr(main,'call_liara_chat_completion',lambda *args,**kwargs:'کودک به چند ساعت خواب نیاز دارد؟')
    assert main.build_rag_search_query('How much sleep do kids need?')=='کودک به چند ساعت خواب نیاز دارد؟'
    assert main._clean_rag_query('کودک چقدر sleep نیاز دارد')==''


def test_greeting_with_real_question_is_answered_and_saved(setup, monkeypatch):
    client,factory,(child,_,_)=setup
    called=[]
    def model(messages,**kwargs):
        called.append(messages)
        return 'پاسخ کامل درباره خواب کودک.'
    monkeypatch.setattr(main,'call_liara_chat_completion',model)
    response=client.post('/chat',json={'phone_number':'09999990001','child_id':child,
        'message':'سلام، در مورد خواب کودک سه ساله سؤال دارم؛ چقدر خواب نیاز دارد؟'})
    assert response.status_code==200
    assert response.json()['response']=='پاسخ کامل درباره خواب کودک.'
    assert len(called)==1
    with factory() as db:
        assert db.query(models.ChatMessage).filter_by(session_id=response.json()['chat_session_id']).count()==2
