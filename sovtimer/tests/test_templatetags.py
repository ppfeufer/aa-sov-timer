"""
Test for the template tag sovtimer_static
"""

# Django
from django.template import Context, Template
from django.test import TestCase, override_settings

# AA Sovereignty Timer
from sovtimer import __version__
from sovtimer.helper.static_files import calculate_integrity_hash


class TestVersionedStatic(TestCase):
    """
    Test `sovtimer_static` template tag
    """

    @override_settings(DEBUG=False)
    def test_versioned_static(self):
        """
        Test should return the versioned static

        :return:
        :rtype:
        """

        context = Context(dict_={"version": __version__})
        template_to_render = Template(
            template_string=(
                "{% load sovtimer %}"
                "{% sovtimer_static 'css/aa-sov-timer.min.css' %}"
                "{% sovtimer_static 'js/aa-sov-timer.min.js' %}"
            )
        )

        rendered_template = template_to_render.render(context=context)

        expected_static_css_src = (
            f'/static/sovtimer/css/aa-sov-timer.min.css?v={context["version"]}'
        )
        expected_static_css_src_integrity = calculate_integrity_hash(
            "css/aa-sov-timer.min.css"
        )
        expected_static_js_src = (
            f'/static/sovtimer/js/aa-sov-timer.min.js?v={context["version"]}'
        )
        expected_static_js_src_integrity = calculate_integrity_hash(
            "js/aa-sov-timer.min.js"
        )

        self.assertIn(member=expected_static_css_src, container=rendered_template)
        self.assertIn(
            member=expected_static_css_src_integrity, container=rendered_template
        )
        self.assertIn(member=expected_static_js_src, container=rendered_template)
        self.assertIn(
            member=expected_static_js_src_integrity, container=rendered_template
        )

    @override_settings(DEBUG=True)
    def test_versioned_static_with_debug_enabled(self) -> None:
        """
        Test versioned static template tag with DEBUG enabled

        :return:
        :rtype:
        """

        context = Context({"version": __version__})
        template_to_render = Template(
            template_string=(
                "{% load sovtimer %}" "{% sovtimer_static 'css/aa-sov-timer.min.css' %}"
            )
        )

        rendered_template = template_to_render.render(context=context)

        expected_static_css_src = (
            f'/static/sovtimer/css/aa-sov-timer.min.css?v={context["version"]}'
        )

        self.assertIn(member=expected_static_css_src, container=rendered_template)
        self.assertNotIn(member="integrity=", container=rendered_template)
