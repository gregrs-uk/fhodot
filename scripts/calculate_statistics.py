"""Add today's statistics to the database, replacing existing for today"""


from fhodot.database import session_scope
from fhodot.stats import replace_current_stats_in_session


with session_scope() as session:
    replace_current_stats_in_session()
