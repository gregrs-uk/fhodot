"""Tests and demonstrations for fhodot.database"""

import sqlalchemy.orm.session

from fhodot.database import Session, session_scope
from tests import TestCaseWithReconfiguredSession


class TestDatabase(TestCaseWithReconfiguredSession):
    """Test connecting to the database"""


    # inherits setUp and tearDown


    def test_session_is_scoped_session(self):
        """fhodot.database.Session is a scoped session"""
        self.assertTrue(isinstance(Session,
                                   sqlalchemy.orm.scoping.scoped_session))


    def test_create_scoped_sessions(self):
        """Two instances of (scoped) Session are the same object"""

        # see https://docs.sqlalchemy.org/en/13/orm/contextual.html#contextual-thread-local-sessions
        session_1 = Session()
        session_2 = Session()
        self.assertTrue(session_1 is session_2)
        session_1.close()
        session_2.close()


    def test_session_scope(self):
        """session_scope() should yield a session"""

        with self.assertLogs(level="DEBUG"):
            with session_scope() as my_session:
                self.assertTrue(isinstance(my_session,
                                           sqlalchemy.orm.session.Session))


    def test_session_scope_same_session(self):
        """session_scope() yields the same session as Session()"""
        with self.assertLogs(level="DEBUG"):
            with session_scope() as session_1:
                session_2 = Session()
                self.assertTrue(session_1 is session_2)


    def test_session_scope_raise_exception(self):
        """session_scope() should re-raise exceptions and print info"""

        with self.assertLogs(level="INFO"):
            with self.assertRaises(RuntimeError):
                with session_scope():
                    raise RuntimeError


    def test_test_transaction(self):
        """Global session bound to test connection"""

        # global session bound to same connection used by test transaction
        self.assertTrue(
            Session.get_bind() is self.transaction.connection)
