"""Module for connecting to the database

All modules share the same global scoped session without needing to pass
it between methods.

You can use Session directly e.g.

from fhodot.database import Session
Session.add(some_object)
Session.commit()
Session.remove()

or create an instance e.g.

from fhodot.database import Session
session = database.Session()
session.add(some_object)
session.commit()
session.remove()

or you can use the session_scope() context manager to automatically
commit() or rollback() and then remove() e.g.

from fhodot.database import session_scope
with session_scope() as session:
    # do something
    # do something else

These three examples will all use the same scoped session.
"""

from contextlib import contextmanager
from logging import debug, info

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from fhodot.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
# see https://docs.sqlalchemy.org/en/13/orm/contextual.html
Session = scoped_session(sessionmaker(bind=engine))

# see https://docs.sqlalchemy.org/en/13/orm/session_basics.html
@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations"""

    session = Session()
    try:
        yield session
        debug("Committing session")
        session.commit()
    except:
        info("Rolling back session")
        session.rollback()
        raise
    finally:
        # close() session and remove from scoped session registry in
        # case the session config has been modified
        Session.remove()
