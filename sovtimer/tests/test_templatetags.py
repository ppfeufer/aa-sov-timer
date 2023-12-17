"""
Test for the template tag sovtimer_static
"""

# Django
from django.template import Context, Template
from django.test import TestCase

# AA Sovereignty Timer
from sovtimer import __version__


class TestForumVersionedStatic(TestCase):
    """
    Test `sovtimer_static` template tag
    """

    def test_sovtimer_static(self):
        """
        Test if we get the right version on our static files

        :return:
        """

        context = Context(dict_={"version": __version__})
        template_to_render = Template(
            template_string=(
                "{% load sovtimer %}"
                "{% sovtimer_static 'sovtimer/css/aa-sov-timer.min.css' %}"
            )
        )

        rendered_template = template_to_render.render(context=context)

        self.assertInHTML(
            needle=f'/static/sovtimer/css/aa-sov-timer.min.css?v={context["version"]}',
            haystack=rendered_template,
        )
