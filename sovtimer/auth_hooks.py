"""
Hook into AA
"""

# Alliance Auth
from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook

# AA Sovereignty Timer
from sovtimer import __title__, urls


class AaSovtimerMenuItem(MenuItemHook):  # pylint: disable=too-few-public-methods
    """
    This class ensures only authorized users will see the menu entry
    """

    def __init__(self):
        # Setup menu entry for sidebar
        MenuItemHook.__init__(
            self,
            text=__title__,
            classes="fa-regular fa-clock",
            url_name="sovtimer:dashboard",
            navactive=["sovtimer:"],
        )

    def render(self, request):
        """
        Check if the user has the permission to view this app

        :param request:
        :return:
        """

        if request.user.has_perm(perm="sovtimer.basic_access"):
            return MenuItemHook.render(self, request=request)

        return ""


@hooks.register("menu_item_hook")
def register_menu():
    """
    Register our menu item

    :return:
    """

    return AaSovtimerMenuItem()


@hooks.register("url_hook")
def register_urls():
    """
    Register our base url

    :return:
    """

    return UrlHook(urls=urls, namespace="sovtimer", base_url=r"^sovereignty-timer/")
