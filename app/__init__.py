# This file makes the 'backend' folder a Python package

from . import gh_fetch
from . import llm_client
from . import lesson_generator
from . import quiz_generator
from . import ingestion # <-- ADD THIS LINE