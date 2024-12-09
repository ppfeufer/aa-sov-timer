# Makefile for AA Sov Timer

# Variables
appname = aa-sov-timer
appname_verbose = AA Sov Timer
package = sovtimer
translation_template = $(package)/locale/django.pot
git_repository = https://github.com/ppfeufer/$(appname)
git_repository_issues = $(git_repository)/issues

# Default goal
.DEFAULT_GOAL := help

# Confirm action
.PHONY: confirm-action
confirm-action:
	@read -p "Are you sure you want to run '$(MAKECMDGOALS)'? [Y/n] " response; \
	response=$${response:-Y}; \
	if [ "$$response" != "Y" ] && [ "$$response" != "y" ]; then \
		echo "Aborted"; \
		exit 1; \
	fi

# General confirmation
.PHONY: confirm
confirm:
	@read -p "Are you sure? [Y/n] " response; \
	response=$${response:-Y}; \
	if [ "$$response" != "Y" ] && [ "$$response" != "y" ]; then \
		echo "Aborted"; \
		exit 1; \
	fi

# Graph models
.PHONY: graph_models
graph_models:
	@echo "Creating a graph of the models"
	@python ../myauth/manage.py \
		graph_models \
		$(package) \
		--arrow-shape normal \
		-o $(appname)-models.png

# Prepare a new release
# Update the graph of the models, translation files and the version in the package
.PHONY: prepare-release
prepare-release: graph_models translations
	@echo ""
	@echo "Preparing a release"
	@read -p "New Version Number: " new_version; \
	sed -i "/__version__/c\__version__ = \"$$new_version\"" $(package)/__init__.py; \
	sed -i "/\"Project-Id-Version: /c\\\"Project-Id-Version: $(appname_verbose) $$new_version\\\n\"" $(translation_template); \
	sed -i "/\"Report-Msgid-Bugs-To: /c\\\"Report-Msgid-Bugs-To: $(git_repository_issues)\\\n\"" $(translation_template); \
	echo "Updated version in $(TEXT_BOLD)$(package)/__init__.py$(TEXT_BOLD_END)"

# Help
.PHONY: help
help::
	@echo ""
	@echo "$(TEXT_BOLD)$(appname_verbose)$(TEXT_BOLD_END) Makefile"
	@echo ""
	@echo "$(TEXT_BOLD)Usage:$(TEXT_BOLD_END)"
	@echo "  make [command]"
	@echo ""
	@echo "$(TEXT_BOLD)Commands:$(TEXT_BOLD_END)"
	@echo "  $(TEXT_UNDERLINE)General:$(TEXT_UNDERLINE_END)"
	@echo "    graph_models              Create a graph of the models"
	@echo "    help                      Show this help message"
	@echo "    prepare-release           Prepare a release and update the version in '$(package)/__init__.py'."
	@echo "                              Please make sure to update the 'CHANGELOG.md' file accordingly."
	@echo ""

# Include the configurations
include .make/conf.d/*.mk
