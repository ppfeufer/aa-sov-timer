"""
Initializing our tests
"""

# Standard Library
import re
import socket

# Django
from django.contrib.auth.models import User
from django.core.handlers.wsgi import WSGIRequest
from django.test import TestCase

# Alliance Auth
from allianceauth.tests.auth_utils import AuthUtils


class SocketAccessError(Exception):
    """Error raised when a test script accesses the network"""


class BaseTestCase(TestCase):
    """Variation of Django's TestCase class that prevents any network use.

    Example:

        .. code-block:: python

            class TestMyStuff(BaseTestCase):
                def test_should_do_what_i_need(self): ...

    """

    @classmethod
    def setUpClass(cls):
        """
        Set up the test class by replacing the socket.socket method with a guard that raises an error if accessed.

        :return:
        :rtype:
        """

        cls.socket_original = socket.socket

        socket.socket = cls.guard

        return super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Tear down the test class by restoring the original socket.socket method.

        :return:
        :rtype:
        """

        socket.socket = cls.socket_original

        return super().tearDownClass()

    @staticmethod
    def guard(*args, **kwargs):
        """
        Guard method that raises a SocketAccessError if an attempt is made to access the network.

        :param args:
        :type args:
        :param kwargs:
        :type kwargs:
        :return:
        :rtype:
        """

        raise SocketAccessError("Attempted to access network")

    @staticmethod
    def create_fake_user(
        character_id: int,
        character_name: str,
        corporation_id: int = None,
        corporation_name: str = None,
        corporation_ticker: str = None,
        alliance_id: int = None,
        alliance_name: str = None,
        permissions: list[str] = None,
    ) -> User:
        """
        Create a fake user with given character and corporation/alliance info.

        :param character_id:
        :type character_id:
        :param character_name:
        :type character_name:
        :param corporation_id:
        :type corporation_id:
        :param corporation_name:
        :type corporation_name:
        :param corporation_ticker:
        :type corporation_ticker:
        :param alliance_id:
        :type alliance_id:
        :param alliance_name:
        :type alliance_name:
        :param permissions:
        :type permissions:
        :return:
        :rtype:
        """

        username = re.sub(pattern=r"[^\w\d@\.\+-]", repl="_", string=character_name)
        user = AuthUtils.create_user(username=username)

        if not corporation_id:
            corporation_id = 2001
            corporation_name = "Wayne Technologies Inc."
            corporation_ticker = "WTE"

        if not alliance_id:
            alliance_id = 3001
            alliance_name = "Wayne Enterprises"

        AuthUtils.add_main_character_2(
            user=user,
            name=character_name,
            character_id=character_id,
            corp_id=corporation_id,
            corp_name=corporation_name,
            corp_ticker=corporation_ticker,
            alliance_id=alliance_id,
            alliance_name=alliance_name,
        )

        if permissions:
            perm_objs = [
                AuthUtils.get_permission_by_name(perm=perm) for perm in permissions
            ]
            user = AuthUtils.add_permissions_to_user(perms=perm_objs, user=user)

        return user

    @staticmethod
    def response_content_to_str(response: WSGIRequest) -> str:
        """
        Return the content of a WSGIRequest response as string

        :param response:
        :type response:
        :return:
        :rtype:
        """

        return response.content.decode(response.charset)
