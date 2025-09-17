"""
Constants we use throughout the app
"""

# Prefix used for all internal URLs within the application.
# This ensures that internal URLs are easily distinguishable.
INTERNAL_URL_PREFIX = "-"

# Time-to-live (TTL) for ETag caching, defined in seconds.
# Currently set to 7 days (60 seconds * 60 minutes * 24 hours * 7 days).
ETAG_TTL = 60 * 60 * 24 * 7  # 7 Days
