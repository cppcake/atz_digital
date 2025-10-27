import sqlite3
from utils import Singleton


class Database(Singleton):
    """A Singleton managing a sqlite connection."""

    def init_lazy(self, **kwargs):
        self._db_path = None
        self._conn = None
        self._is_temp = False

    @property
    def temp(self) -> bool:
        return self._is_temp

    @classmethod
    def tempdb(cls):
        """Creates a temporary in memory database for testing"""

        me = object.__new__(cls)
        me.set_db_path(":memory:")
        me._is_temp = True
        return me

    @property
    def db_path(self) -> str:
        return self._db_path

    @db_path.setter
    def db_path(self, path: str):
        self.set_db_path(path)

    def into_tempdb(self):
        self.set_db_path(":memory:")
        self._is_temp = True

    def set_db_path(self, path: str):
        """Sets the path of this database and reinitializes it using the given path."""

        self._db_path = path
        self._create_conn()

    def try_execute(self, *args, **kwargs) -> (sqlite3.Cursor, Exception | None):
        """Tries to perform a query on this database, rolling back if any error occured and returning the exception. None is returned on Success"""

        exception = None
        c = None

        try:
            c = self._conn.cursor()
            c.execute(*args, **kwargs)
            self._conn.commit()

        except Exception as e:
            exception = e
            self._conn.rollback()

        return (c, exception)

    def execute(self, *args, **kwargs) -> sqlite3.Cursor:
        """Performs a query on this database. In the event of an exceptions any changes are rolled back and the exception is raised again."""
        (c, e) = self.try_execute(*args, **kwargs)

        if e is not None:
            raise e

        return c

    def try_execute_many(self, queries: list[str], *args, **kwargs) -> Exception | None:
        """Tries to perform a list of queriess on this database, rolling back if any error occured and returning the exception. None is returned on Success"""

        exception = None

        try:
            c = self._conn.cursor()

            for q in queries:
                c.execute(q, *args, **kwargs)

            self._conn.commit()

        except Exception as e:
            exception = e
            self._conn.rollback()

        return exception

    def execute_many(self, queries: list[str], *args, **kwargs):
        """Performs a list of queries on this database. In the event of an exceptions any changes are rolled back and the exception is raised again."""
        if (e := self.try_execute_many(queries, *args, **kwargs)) is not None:
            raise e

    def _setup_tables(self): ...

    def _create_conn(self):
        if self._db_path is None:
            return

        # Connect to the database
        self._conn = sqlite3.connect(self._db_path)

        # Create all tables
        self._setup_tables()
