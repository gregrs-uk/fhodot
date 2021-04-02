"""Configuration variables"""

from logging import CRITICAL, ERROR, WARNING, INFO, DEBUG # pylint: disable=unused-import

DATABASE_URL = "postgresql+psycopg2:///gregrs_fhodot"
USER_AGENT = "https://github.com/gregrs-uk/fhodot"
LOG_LEVEL = DEBUG
