import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from langchain_core.documents import Document
from embedding_cache import EmbeddingCache
from chat_support import extract_used_sources
from retrieve import RetrievalManager, filter_documents_for_child_age, query_age_days
from process import has_usable_article_body


def test_age_guards_written_month_year_and_preschool():
    docs = [Document(page_content='', metadata={'title':title,'url':url}) for title,url in [
        ('برنامه خواب نوزاد شش ماهه',''),('مهارت پریدن کودک پنج ساله',''),
        ('میزان خواب کودکان','https://www.babycenter.com/child/sleep/preschoolers-and-big-kids')]]
    assert not filter_documents_for_child_age(docs, 304)
    assert filter_documents_for_child_age(docs, 1826) == docs[1:]
    assert query_age_days('کودک ۱۰ ماهه چقدر خواب لازم دارد؟') == 304


def test_citations_only_include_used_context():
    docs = [Document(page_content='مرتبط'),Document(page_content='نامرتبط')]
    answer, used = extract_used_sources('جواب کامل\n[[sources:1,99,1]]',docs)
    assert answer == 'جواب کامل'
    assert used == docs[:1]
    assert extract_used_sources('پاسخ از دانش عمومی [[sources:]]',docs)[1] == []
    assert extract_used_sources('پاسخ بدون ادعای منبع',docs)[1] == []


def test_embedding_batch_and_persistent_cache(tmp_path, monkeypatch):
    class FakeEmbeddings:
        model='test-model'
        def __init__(self): self.calls=[]
        def embed_documents(self,texts): self.calls.append(texts); return [[1.,2.,3.] for text in texts]
    fake=FakeEmbeddings()
    monkeypatch.setattr(RetrievalManager,'_load_embeddings',lambda self:fake)
    manager=RetrievalManager(); manager.embedding_cache=EmbeddingCache(tmp_path/'cache.db')
    docs=[Document(page_content='متن اول',metadata={'title':'عنوان اول'}),Document(page_content='متن دوم',metadata={'title':'عنوان دوم'})]
    first=manager._query_and_candidate_embeddings('سؤال',docs)
    assert len(fake.calls)==1 and len(fake.calls[0])==3
    other=RetrievalManager(); other.embedding_cache=EmbeddingCache(tmp_path/'cache.db')
    second=other._query_and_candidate_embeddings('سؤال',docs)
    assert len(fake.calls)==1 and first==second


def test_title_candidates_retain_non_babycenter_article(monkeypatch):
    monkeypatch.setattr(RetrievalManager,'_load_embeddings',lambda self:None)
    manager=RetrievalManager()
    docs=[Document(page_content='ساعت خواب و خواب کودک',metadata={'title':'خواب','source_file':'baby.txt'}),
          Document(page_content='مقدار استراحت در شبانه روز',metadata={'title':'کودک ده ماهه چند ساعت خواب نیاز دارد','source_file':'kinedu.txt'})]
    manager.setup_retrievers(docs)
    results=manager.retrieve_documents('کودک ده ماهه چند ساعت خواب نیاز دارد')
    assert any(doc.metadata['source_file']=='kinedu.txt' for doc in results)
    assert not manager.retrieve_documents('موضوع کاملاً متفاوت درباره تعمیر خودرو')


def test_link_only_and_empty_translation_do_not_enter_corpus():
    assert not has_usable_article_body('عنوان: مقاله خواب\nلینک مقاله اصلی: https://www.babycenter.com/baby/sleep/example\nمحتوای مقاله:')
    assert not has_usable_article_body('')
    assert has_usable_article_body('عنوان: خواب کودک\nلینک مقاله اصلی: https://example.com\nمحتوای مقاله:\nداشتن برنامهٔ منظم پیش از خواب و محیط آرام به کودک کمک می‌کند برای خواب آماده شود.')


def test_colloquial_jumping_question_matches_article(monkeypatch):
    monkeypatch.setattr(RetrievalManager,'_load_embeddings',lambda self:None)
    manager=RetrievalManager()
    docs=[Document(page_content='آموزش پریدن با هر دو پا',metadata={'title':'استاد پریدن شدن','source_file':'jump.txt'}),
          Document(page_content='خواب کودک',metadata={'title':'ساعت خواب','source_file':'sleep.txt'})]
    manager.setup_retrievers(docs)
    result=manager.retrieve_documents('غزل خوب نمیتونه بپره مشکلی نداره؟')
    assert result[0].metadata['source_file']=='jump.txt'
