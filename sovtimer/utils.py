"""
utilities
"""

import logging


class LoggerAddTag(logging.LoggerAdapter):
    """
    add custom tag to a logger
    """

    def __init__(self, my_logger, prefix):
        super().__init__(my_logger, {})
        self.prefix = prefix

    def process(self, msg, kwargs):
        """
        process log items
        :param msg:
        :param kwargs:
        :return:
        """
        return f"[{self.prefix}] {msg}", kwargs


logger = LoggerAddTag(logging.getLogger(__name__), __package__)
