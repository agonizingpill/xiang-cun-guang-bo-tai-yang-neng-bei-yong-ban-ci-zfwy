import os

os.environ.setdefault('DATABASE_URL', 'sqlite:////tmp/hamlet_test.db')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/15')
os.environ.setdefault('JWT_SECRET', 'test-secret')

import fakeredis
import pytest

import core.queueing as queueing


@pytest.fixture()
def conn():
    from core.db import engine, metadata
    metadata.drop_all(engine)
    metadata.create_all(engine)
    connection = engine.connect()
    transaction = connection.begin()
    yield connection
    transaction.rollback()
    connection.close()


@pytest.fixture()
def redis(monkeypatch):
    server = fakeredis.FakeStrictRedis(decode_responses=True)
    monkeypatch.setattr(queueing, 'broker', server)
    import core.worker as worker
    monkeypatch.setattr(worker, 'broker', server)
    yield server
    server.flushall()


@pytest.fixture()
def reviewer():
    return {'sub': 'reviewer@demo.test', 'role': 'reviewer'}


@pytest.fixture()
def operator():
    return {'sub': 'operator@demo.test', 'role': 'operator'}
