import copy
from uuid import UUID

from db.topic import Answer, Statement, Topic, TopicDB


def sort_by_id(e):
    e.sort(key=lambda x: str(x.id))
    return e


def prepare_topics(db) -> [Topic]:
    topics = [Topic(version=0, content=c)
              for c in ("Eins", "Zwei", "Drei", "Vier")]

    for t in topics:
        t.insert(db)

    return sort_by_id(topics)


def test_db_singleton():
    a = TopicDB()
    b = TopicDB()
    assert a is b


def test_temp_db_is_unique():
    a = TopicDB()
    b = TopicDB.tempdb()
    assert a is not b


def test_topic():
    db = TopicDB.tempdb()
    original = Topic(version=0, content="Test")

    # Roundtrip
    original.insert(db)
    fetched = Topic.fetch(original.id, original.version, db)
    assert fetched == original

    # Edit
    fetched.content = "39"
    fetched.insert(db)
    refetched = Topic.fetch(original.id, original.version, db)
    assert refetched == fetched
    assert refetched != original


def test_statement():
    db = TopicDB.tempdb()
    topic = Topic(version=0, content="Test Topic")
    topic.insert(db)

    original = Statement(
        topic_id=topic.id,
        topic_version=topic.version,
        content="Test",
        position=1,
    )

    # Roundtrip
    original.insert(db)
    fetched = Statement.fetch(original.id, db)
    assert fetched == original

    # Edit
    fetched.content = "39"
    fetched.insert(db)
    refetched = Statement.fetch(original.id, db)
    assert refetched == fetched
    assert refetched != original

    # Check topic this statement belongs to
    assert topic == fetched.topic(db)


def test_answer():
    db = TopicDB.tempdb()
    topic = Topic(version=0, content="Test Topic")
    topic.insert(db)

    original = Answer(
        topic_id=topic.id,
        topic_version=topic.version,
        content="Test",
        color="red",
        icon="missing"
    )

    # Roundtrip
    original.insert(db)
    fetched = Answer.fetch(original.id, db)
    assert fetched == original

    # Edit
    fetched.content = "39"
    fetched.insert(db)
    refetched = Answer.fetch(original.id, db)
    assert refetched == fetched
    assert refetched != original

    # Check topic this answer belongs to
    assert topic == fetched.topic(db)


def test_topic_list_all():
    db = TopicDB.tempdb()

    # Fetch all topics
    topics = prepare_topics(db)
    assert topics == sort_by_id(Topic.list_all(db))

    # Ensure that only the newest topics are returned
    old_version = copy.copy(topics[0])
    topics[0].version += 1
    topics[0].content = "Second Version"
    topics[0].insert(db)

    results = sort_by_id(Topic.list_all(db))
    assert topics == results
    assert old_version not in results
    assert sort_by_id(Topic.list_all(db)) == sort_by_id(
        Topic.list_all_and_ignored(db))


def test_topic_answers():
    db = TopicDB.tempdb()
    topics = prepare_topics(db)

    a1 = Answer(
        topic_id=topics[0].id,
        topic_version=topics[0].version,
        content="A1",
        color="red",
        icon="missing"
    )

    a2 = Answer(
        topic_id=topics[0].id,
        topic_version=topics[0].version,
        content="A2",
        color="green",
        icon="missing"
    )

    a3 = Answer(
        topic_id=topics[1].id,
        topic_version=topics[1].version,
        content="A3",
        color="yellow",
        icon="missing"
    )

    a1.insert(db)
    a2.insert(db)
    a3.insert(db)

    assert [a2, a1] == topics[0].answers(db)
    assert [a3] == topics[1].answers(db)
    assert [] == topics[2].answers(db)
    assert [] == topics[3].answers(db)


def test_topic_statements():
    db = TopicDB.tempdb()
    topics = prepare_topics(db)

    s1 = Statement(
        topic_id=topics[0].id,
        topic_version=topics[0].version,
        content="S1",
        position=0,
    )

    s2 = Statement(
        topic_id=topics[0].id,
        topic_version=topics[0].version,
        content="S2",
        position=1,
    )

    s3 = Statement(
        topic_id=topics[1].id,
        topic_version=topics[1].version,
        content="S3",
        position=0,
    )

    s1.insert(db)
    s2.insert(db)
    s3.insert(db)

    assert [s1, s2] == topics[0].statements(db)
    assert [s3] == topics[1].statements(db)
    assert [] == topics[2].statements(db)
    assert [] == topics[3].statements(db)


def test_topic_as_json():
    topic = Topic(
        version=0, content="Test", id=UUID("dbc0bbea-7a03-40cb-9484-0d21431dcb85")
    )

    a1 = Answer(
        id=UUID("d841294d-0e3b-4865-ada8-7b2d4af24846"),
        topic_id=topic.id,
        topic_version=topic.version,
        content="A1",
        color="red",
        icon="missing"
    )

    a2 = Answer(
        id=UUID("661a8e88-293d-46cb-b877-1cb4f0c61837"),
        topic_id=topic.id,
        topic_version=topic.version,
        content="A2",
        color="green",
        icon="missing"
    )

    s1 = Statement(
        id=UUID("6ff67ff0-36a8-482b-9dcc-a4e1930fff7a"),
        topic_id=topic.id,
        topic_version=topic.version,
        content="S1",
        position=0,
    )

    s2 = Statement(
        id=UUID("6ba78833-e2a9-4a2a-9897-9d3cb7176077"),
        topic_id=topic.id,
        topic_version=topic.version,
        content="S2",
        position=1,
    )

    db = TopicDB.tempdb()

    topic.insert(db)
    a1.insert(db)
    a2.insert(db)
    s1.insert(db)
    s2.insert(db)

    original_json = '{"version": 0, "content": "Test", "id": "dbc0bbea-7a03-40cb-9484-0d21431dcb85", "answers": [{"topic_id": "dbc0bbea-7a03-40cb-9484-0d21431dcb85", "topic_version": 0, "content": "A2", "color": "green", "icon": "missing", "id": "661a8e88-293d-46cb-b877-1cb4f0c61837"}, {"topic_id": "dbc0bbea-7a03-40cb-9484-0d21431dcb85", "topic_version": 0, "content": "A1", "color": "red", "icon": "missing", "id": "d841294d-0e3b-4865-ada8-7b2d4af24846"}], "statements": [{"topic_id": "dbc0bbea-7a03-40cb-9484-0d21431dcb85", "topic_version": 0, "content": "S1", "position": 0, "id": "6ff67ff0-36a8-482b-9dcc-a4e1930fff7a"}, {"topic_id": "dbc0bbea-7a03-40cb-9484-0d21431dcb85", "topic_version": 0, "content": "S2", "position": 1, "id": "6ba78833-e2a9-4a2a-9897-9d3cb7176077"}]}'
    assert original_json == topic.as_json(db)


def test_recent_topics():
    db = TopicDB.tempdb()
    v0 = Topic(version=0, content="First Version")
    v1 = Topic(version=1, content="Second Version", id=v0.id)

    v0.insert(db)
    v1.insert(db)

    assert v1 == Topic.get_newest_version(v0.id, db)
    assert v0 != Topic.get_newest_version(v0.id, db)


def test_get_all_versions():
    db = TopicDB.tempdb()
    v0 = Topic(version=0, content="First Version")
    v1 = Topic(version=1, content="Second Version", id=v0.id)

    v0.insert(db)
    v1.insert(db)

    assert [v1, v0] == Topic.get_all_versions(v0.id, db)


def test_ignored():
    db = TopicDB.tempdb()
    topics = prepare_topics(db)

    topics[1].set_ignored(True, db)
    topics[0].set_ignored(False, db)

    topics_active = copy.copy(topics)
    topics_active.remove(topics[1])

    assert sort_by_id(Topic.list_all(db)) != sort_by_id(
        Topic.list_all_and_ignored(db))
    assert topics_active == sort_by_id(Topic.list_all(db))

    topics[1].set_ignored(False, db)
    assert sort_by_id(Topic.list_all(db)) == sort_by_id(
        Topic.list_all_and_ignored(db))
    assert topics == sort_by_id(Topic.list_all(db))


def test_is_ignored():
    db = TopicDB.tempdb()

    topic = Topic(version=0, content="Test")
    topic.insert(db)

    assert not topic.is_ignored(db)

    topic.set_ignored(True, db)
    assert topic.is_ignored(db)

    topic.set_ignored(False, db)
    assert not topic.is_ignored(db)


def test_list_ignored():
    db = TopicDB.tempdb()

    topic = Topic(version=0, content="Test")
    topic.insert(db)

    assert [] == Topic.list_ignored(db)

    topic.set_ignored(True, db)
    assert [topic] == Topic.list_ignored(db)

    topic.set_ignored(False, db)
    assert [] == Topic.list_ignored(db)
