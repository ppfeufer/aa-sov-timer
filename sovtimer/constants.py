"""
Our constants
"""


class Constants:
    """
    Constants we use throughout the app
    """

    # Prefix used for all internal URLs within the application.
    # This ensures that internal URLs are easily distinguishable.
    INTERNAL_URL_PREFIX = "-"

    TASK_PRIORITY = 6
    TASK_RUN_TTL = 600  # Stop after 10 minutes
    TASK_ESI_MAX_RETRIES = 5
    TASK_DEFAULT_RETRY_DELAY = 180  # Retry after 3 minutes

    TASK_STRUCTURE_CACHE_KEY = "sov_structures_task_run"
    TASK_STRUCTURE_CACHE_TTL = 300
