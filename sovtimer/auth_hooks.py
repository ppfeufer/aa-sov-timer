# -*- coding: utf-8 -*-

"""
hook into AA
"""

from sovtimer import urls, __title__

from django.utils.translation import ugettext_lazy as _

from allianceauth.services.hooks import MenuItemHook, UrlHook
from allianceauth import hooks


class AaSovtimerMenuItem(MenuItemHook):  # pylint: disable=too-few-public-methods
    """
    This class ensures only authorized users will see the menu entry
    """

    def __init__(self):
        # setup menu entry for sidebar
        MenuItemHook.__init__(
            self,
            _(__title__),
            "far fa-clock fa-fw",
            "sovtimer:dashboard",
            navactive=["sovtimer:"],
        )

    def render(self, request):
        """
        check if the user has the permission to view this app
        :param request:
        :return:
        """

        if request.user.has_perm("sovtimer.basic_access"):
            return MenuItemHook.render(self, request)

        return ""


@hooks.register("menu_item_hook")
def register_menu():
    """
    register our menu item
    :return:
    """

    return AaSovtimerMenuItem()


@hooks.register("url_hook")
def register_urls():
    """
    register our basu url
    :return:
    """

    return UrlHook(urls, "sovtimer", r"^sovereignty-timer/")
