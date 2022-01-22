"""Configuration variables"""

from logging import CRITICAL, ERROR, WARNING, INFO, DEBUG # pylint: disable=unused-import

# using Docker
DATABASE_URL = "postgresql://postgres:db@postgis:5432/gregrs_fhodot"
REDIS_URL = "redis://redis:6379"

# or running locally without Docker
#DATABASE_URL = "postgresql+psycopg2:///gregrs_fhodot"
#REDIS_URL = "redis://localhost:6379"

USER_AGENT = "https://github.com/gregrs-uk/fhodot"
LOG_LEVEL = DEBUG
