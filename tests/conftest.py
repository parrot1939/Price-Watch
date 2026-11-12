import pytest
from app.database import Base, make_engine, make_session_factory

@pytest.fixture
def db(tmp_path):
    engine = make_engine(f'sqlite:///{tmp_path / "test.db"}')
    Base.metadata.create_all(engine)
    with make_session_factory(engine)() as session:
        yield session
    engine.dispose()
