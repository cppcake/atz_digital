import json
import uuid
from dataclasses import dataclass, field
from typing import Self
from uuid import UUID

from db.database import Database


class TopicDB(Database):
    def init_lazy(self):
        super().set_db_path("topics.db")

    def _setup_tables(self):
        self.execute_many(
            [
                """
                CREATE TABLE IF NOT EXISTS recent_topics (
                    topic_id TEXT PRIMARY KEY,
                    topic_version INTEGER NOT NULL,
                    FOREIGN KEY (topic_id, topic_version) REFERENCES topics(id, version) ON DELETE CASCADE 
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS ignored_topics (
                    topic_id TEXT PRIMARY KEY,
                    FOREIGN KEY (topic_id) REFERENCES topics(id) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS topics (
                    id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    PRIMARY KEY(id, version)
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS statements (
                    id TEXT PRIMARY KEY,
                    topic_id TEXT NOT NULL,
                    topic_version INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    FOREIGN KEY(topic_id, topic_version) REFERENCES topics(id, version) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS answers (
                    id TEXT PRIMARY KEY,
                    topic_id TEXT NOT NULL,
                    topic_version INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    color TEXT NOT NULL,
                    icon TEXT,
                    UNIQUE (color, topic_id, topic_version),
                    FOREIGN KEY(topic_id, topic_version) REFERENCES topics(id, version) ON DELETE CASCADE
                )
                """,
            ]
        )


@dataclass
class Topic:
    version: int
    content: str
    id: UUID = field(default_factory=lambda: uuid.uuid4())

    @staticmethod
    def fetch(id: UUID, version: int, db: TopicDB = None) -> Self | None:
        """Tries to fetch a Topic with the given uuid and version from the database."""

        db = db or TopicDB()

        result = db.execute(
            "SELECT version, content, id FROM topics WHERE id=? AND version=?",
            (str(id), version),
        )

        if result:
            row = result.fetchone()

            if row is None:
                return None

            return Topic(version=row[0], content=row[1], id=UUID(row[2]))

        return None

    def insert(self, db: TopicDB = None):
        """Commits the contents of this class to the database, updating recent topics aswell if necessary"""

        db = db or TopicDB()

        db.execute(
            "INSERT OR REPLACE INTO topics (version, content, id) VALUES (?, ?, ?)",
            (self.version, self.content, str(self.id)),
        )

        recent = Topic.get_newest_version(self.id, db)
        if recent is None or recent.version < self.version:
            db.execute(
                "INSERT OR REPLACE INTO recent_topics (topic_id, topic_version) VALUES (?, ?)",
                (str(self.id), self.version),
            )

    @staticmethod
    def list_all(db: TopicDB = None) -> [Self]:
        """Fetches all topics that are not ignored from the database and returns them as a list. Only the most recent version of a topic is returned"""

        db = db or TopicDB()

        if result := db.execute("""
                                    SELECT t.id, t.version, t.content
                                    FROM topics as t
                                    INNER JOIN recent_topics as r
                                    ON t.id=r.topic_id and t.version=r.topic_version
                                    LEFT JOIN ignored_topics as i
                                    ON t.id = i.topic_id
                                    WHERE i.topic_id IS NULL
                                """):
            return [
                Topic(id=UUID(row[0]), version=row[1], content=row[2])
                for row in result.fetchall()
            ]

        return []

    @staticmethod
    def list_ignored(db: TopicDB = None) -> [Self]:
        """Fetches only topics that ARE ignored from the database and returns them as a list. Only the most recent version of a topic is returned"""

        db = db or TopicDB()

        if result := db.execute("""
                                    SELECT t.id, t.version, t.content
                                    FROM topics as t
                                    INNER JOIN recent_topics as r
                                    ON t.id=r.topic_id and t.version=r.topic_version
                                    INNER JOIN ignored_topics as i
                                    ON t.id = i.topic_id
                                """):
            return [
                Topic(id=UUID(row[0]), version=row[1], content=row[2])
                for row in result.fetchall()
            ]

        return []

    @staticmethod
    def list_all_and_ignored(db: TopicDB = None) -> [Self]:
        """Fetches all topics even if they are ignored from the database and returns them as a list. Only the most recent version of a topic is returned"""

        db = db or TopicDB()

        if result := db.execute("""
                                    SELECT t.id, t.version, t.content
                                    FROM topics as t
                                    INNER JOIN recent_topics as r
                                    ON t.id=r.topic_id and t.version=r.topic_version
                                """):
            return [
                Topic(id=UUID(row[0]), version=row[1], content=row[2])
                for row in result.fetchall()
            ]

        return []

    def answers(self, db: TopicDB = None) -> []:
        """Fetches all answers related to this Topic"""

        db = db or TopicDB()

        if result := db.execute(
            """
                SELECT a.content, a.color, a.id, a.icon
                FROM answers as a
                JOIN topics as t
                ON a.topic_id=t.id AND a.topic_version=t.version
                WHERE a.topic_id=? AND a.topic_version=?
                ORDER BY a.color ASC
                                    
            """,
            (str(self.id), self.version),
        ):
            return [
                Answer(
                    topic_id=self.id,
                    topic_version=self.version,
                    content=row[0],
                    color=row[1],
                    id=UUID(row[2]),
                    icon=row[3]
                )
                for row in result.fetchall()
            ]

        return []

    def statements(self, db: TopicDB = None) -> []:
        """Fetches all statements related to this Topic"""

        db = db or TopicDB()

        if result := db.execute(
            """
                SELECT s.content, s.position, s.id
                FROM statements as s
                JOIN topics as t
                ON s.topic_id=t.id AND s.topic_version=t.version
                WHERE s.topic_id=? AND s.topic_version=?
                ORDER BY s.position ASC
                                    
            """,
            (str(self.id), self.version),
        ):
            return [
                Statement(
                    topic_id=self.id,
                    topic_version=self.version,
                    content=row[0],
                    position=row[1],
                    id=UUID(row[2]),
                )
                for row in result.fetchall()
            ]

        return []

    @staticmethod
    def get_newest_version(id: UUID, db: TopicDB = None) -> Self:
        """Gets the most recent version of this topic"""

        db = db or TopicDB()

        if result := db.execute(
            "SELECT topic_version FROM recent_topics WHERE topic_id=?", (str(
                id),)
        ):
            if topic := result.fetchone():
                version = topic[0]
                return Topic.fetch(id, version, db)

        return None

    @staticmethod
    def get_all_versions(id: UUID, db: TopicDB = None) -> [Self]:
        """Fetches all versions of a specified topic from the database"""

        db = db or TopicDB()

        ret = []

        if result := db.execute(
            "SELECT id, version, content FROM topics WHERE id=? ORDER BY version DESC",
            (str(id),),
        ):
            if topics := result.fetchall():
                ret = [
                    Topic(id=UUID(row[0]), version=row[1], content=row[2])
                    for row in topics
                ]

        return ret

    def set_ignored(self, ignored: bool, db: TopicDB = None):
        """Sets whether or not a topic is considered ignored, essentially soft deleting it"""
        db = db or TopicDB()

        if ignored:
            db.execute(
                "INSERT OR REPLACE INTO ignored_topics (topic_id) VALUES (?)",
                (str(self.id),),
            )
        else:
            db.execute("DELETE FROM ignored_topics WHERE topic_id=?",
                       (str(self.id),))

    def is_ignored(self, db: TopicDB = None) -> bool:
        """Returns whether or not this topic is ignored"""
        db = db or TopicDB()

        if result := db.execute(
            "SELECT COUNT(id) FROM topics as t JOIN ignored_topics as i ON t.id = i.topic_id"
        ):
            if count := result.fetchone():
                return count[0] > 0

        return False

    def as_dict(self, db: TopicDB = None) -> {}:
        """Provides a dictionary representation of this entity"""
        return {
            "version": self.version,
            "content": self.content,
            "id": str(self.id),
            "answers": [a.as_dict() for a in self.answers(db)],
            "statements": [s.as_dict() for s in self.statements(db)],
        }

    def as_json(self, db: TopicDB = None) -> str:
        """Provides a json representation of this entity"""
        return json.dumps(self.as_dict(db))


@dataclass
class Statement:
    topic_id: UUID
    topic_version: int
    content: str
    position: int
    id: UUID = field(default_factory=lambda: uuid.uuid4())

    @staticmethod
    def fetch(id: UUID, db: TopicDB = None) -> Self | None:
        """Tries to fetch a Statement with the given id from the database."""

        db = db or TopicDB()

        result = db.execute(
            "SELECT id, topic_id, topic_version, content, position FROM statements WHERE id=?",
            (str(id),),
        )

        if result:
            row = result.fetchone()

            if row is None:
                return None

            return Statement(
                id=UUID(row[0]),
                topic_id=UUID(row[1]),
                topic_version=row[2],
                content=row[3],
                position=row[4],
            )

        return None

    def insert(self, db: TopicDB = None):
        """Commits the contents of this class to the database"""

        db = db or TopicDB()

        db.execute(
            "INSERT OR REPLACE INTO statements (id, topic_id, topic_version, content, position) VALUES (?, ?, ?, ?, ?)",
            (
                str(self.id),
                str(self.topic_id),
                self.topic_version,
                self.content,
                self.position,
            ),
        )

    def topic(self, db=None) -> Topic:
        """Fetches this statements topic from the database"""
        return Topic.fetch(self.topic_id, self.topic_version, db)

    def as_dict(self) -> {}:
        """Provides a dictionary representation of this entity"""
        d = vars(self)
        d["id"] = str(self.id)
        d["topic_id"] = str(self.topic_id)
        return d

    def as_json(self) -> str:
        """Provides a json representation of this entity"""
        return json.dumps(self.as_dict())


@dataclass
class Answer:
    topic_id: str
    topic_version: int
    content: str
    color: str
    icon: str
    id: UUID = field(default_factory=lambda: uuid.uuid4())

    @staticmethod
    def fetch(id: UUID, db: TopicDB = None) -> Self | None:
        """Tries to fetch a Answer with the given id from the database."""

        db = db or TopicDB()

        result = db.execute(
            "SELECT id, topic_id, topic_version, content, color, icon FROM answers WHERE id=?",
            (str(id),),
        )

        if result:
            row = result.fetchone()

            if row is None:
                return None

            return Answer(
                id=UUID(row[0]),
                topic_id=UUID(row[1]),
                topic_version=row[2],
                content=row[3],
                color=row[4],
                icon=row[5]
            )

        return None

    def insert(self, db: TopicDB = None):
        """Commits the contents of this class to the database"""

        db = db or TopicDB()

        db.execute(
            "INSERT OR REPLACE INTO answers (id, topic_id, topic_version, content, color, icon) VALUES (?, ?, ?, ?, ?, ?)",
            (
                str(self.id),
                str(self.topic_id),
                self.topic_version,
                self.content,
                self.color,
                self.icon
            ),
        )

    def topic(self, db=None) -> Topic:
        """Fetches this answers topic from the database"""
        return Topic.fetch(self.topic_id, self.topic_version, db)

    def as_dict(self) -> {}:
        """Provides a dictionary representation of this entity"""
        d = vars(self)
        d["id"] = str(self.id)
        d["topic_id"] = str(self.topic_id)
        d["icon"] = str(self.icon)
        return d

    def as_json(self) -> str:
        """Provides a json representation of this entity"""
        return json.dumps(self.as_dict())
