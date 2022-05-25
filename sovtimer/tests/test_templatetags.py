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
    Test sovtimer_static template tag
    """

    def test_versioned_static(self):
        """
        Test if we get the right version on our static files
        :return:
        """

        context = Context({"version": __version__})
        template_to_render = Template(
            "{% load sovtimer_versioned_static %}"
            "{% sovtimer_static 'sovtimer/css/aa-sov-timer.min.css' %}"
        )

        rendered_template = template_to_render.render(context)

        self.assertInHTML(
            f'/static/sovtimer/css/aa-sov-timer.min.css?v={context["version"]}',
            rendered_template,
        )
