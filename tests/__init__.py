"""Unit tests for fhodot

Tests are contained in the individual modules and should inherit the
TestCaseWithReconfiguredSession class.
"""

from unittest import TestCase

from sqlalchemy.orm import sessionmaker

from fhodot.database import engine, Session
from fhodot.models.base import DeclarativeBase


class TestCaseWithReconfiguredSession(TestCase):
    """Base TestCase with database session reconfigured"""

    # see https://docs.sqlalchemy.org/en/13/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites

    def setUp(self):
        """Set up transaction and reconfigure global session"""
        Session.remove() # in case any scoped sessions already present
        # transaction can be rolled back, even if we commit
        self.connection = engine.connect()
        self.transaction = self.connection.begin()
        # reconfigure global session to use test connection
        Session.configure(bind=self.connection)
        DeclarativeBase.metadata.drop_all(bind=self.connection)
        DeclarativeBase.metadata.create_all(bind=self.connection)

    def tearDown(self):
        """Roll back transaction and close connection"""
        Session.remove()
        self.transaction.rollback() # including commits
        self.connection.close()
        # N.B. doesn't reconfigure Session to bind to engine
