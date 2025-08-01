# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

<!--
GitHub MD Syntax:
https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax

Highlighting:
https://docs.github.com/assets/cb-41128/mw-1440/images/help/writing/alerts-rendered.webp

> [!NOTE]
> Highlights information that users should take into account, even when skimming.

> [!IMPORTANT]
> Crucial information necessary for users to succeed.

> [!WARNING]
> Critical content demanding immediate user attention due to potential risks.
-->

## [In Development] - Unreleased

<!--
Section Order:

### Added
### Fixed
### Changed
### Deprecated
### Removed
### Security
-->

## [2.5.0] - 2025-07-08

### Added

- New dependency
  - `django-esi>=7.0.1`

### Changed

- User Agent generation updated to match latest `django-esi` guidelines
- Translations updated

## [2.4.3] - 2025-06-20

### Added

- Docker install and update instructions to README.md

### Changed

- Wording: Use "campaigns" instead of "timers" in the campaign table
- Improved explanatory text in the campaign table a bit

### Removed

- Unused constants

## [2.4.2] - 2025-06-16

### Fixed

- Contrast issue with upcoming and active campaigns when using the Darkly theme

## [2.4.1] - 2025-06-13

### Changed

- Task code refactored \
  This also fixes an issue with the ADMs getting reset when a Sovhub was reinforced.
  Unfortunately, the ADM information are not available in the ESI data for
  reinforced Sovhubs, so the code had to be changed to not reset the ADMs
  when a Sovhub is reinforced. \
  This will not fix it for already registered campaigns, but for new ones.
- Management command for the initial data load refactored
- zKillboard icon properly loaded via Django static files
- Dotlan constellation links now generated using the `eveonline` app

## [2.4.0] - 2025-06-03

### Removed

- Cache breaker for static files. Doesn't work as expected with `django-sri`.

## [2.3.5] - 2025-05-05

### Changed

- Translations updated

## [2.3.4] - 2025-04-09

### Changed

- Check for `DEBUG` status has been moved to its own function

### Removed

- Obsolete template

## [2.3.3] - 2025-03-04

### Changed

- Improved the task code
- Improved date/time localization
- Improved the code for the `sovtimer_static` template tag

### Removed

- Redundant localization call in JavaScript

## [2.3.2] - 2025-02-27

### Fixed

- The last campaign wasn't removed reliably when there were no more campaigns reported
  by ESI

## [2.3.1] - 2025-02-26

### Changed

- Localize datetime output in the campaign table
- Use DataTables' translations instead of our own
- Simplify constant names
- Make ajax call URL an internal URL
- Translations updated

### Fixed

- `TypeError: object of type 'NoneType' has no len()` in update task.
  Thank you, CCP, for reinvigorating null-sec with the Equinox update. This led to a
  period when there were no sovereignty campaigns at all, which gave me the chance
  to find this bug. Now this bug is fixed, you can make null-sec great again, please,
  and thank you.

## [2.3.0] - 2025-02-02

### Fixed

- Upcoming Timer Threshold

### Changed

- Use `django-sri` for sri hashes
- Material Icon font updated to v143
- Minimum requirements
  - Alliance Auth >= 4.6.0

## [2.2.4] - 2025-01-13

### Fixed

- Escaping translation strings to fix potential issues with French and Italian translations

### Changed

- Set user agent according to MDN guidelines

## [2.2.3] - 2024-12-15

### Added

- Integrity hashes for the static files
- More logging to the task, since I couldn't believe there are no sovereignty
  campaigns at all. Well, the Equinox update works, null-sec is "truly" reinvigorated.

### Changed

- Hide campaign type column. Since there is now only one campaign type, we don't need it.
- Proper JS settings merge

## [2.2.2] - 2024-12-14

### Added

- Python 3.13 to the test matrix

### Changed

- Translations updated

## [2.2.1] - 2024-11-01

### Changed

- Ukrainian translation improved

## [2.2.0] - 2024-09-16

### Changed

- Dependencies updated
  - `allianceauth`>=4.3.1
- French translation improved
- German translation improved
- Japanese translation improved
- Lingua codes updated to match Alliance Auth v4.3.1

## [2.1.0] - 2024-07-16

### Changed

- Campaign event name from "IHub defense" to "Sov Hub defense" to reflect the structure name change in EVE Online

### Removed

- Support for Python 3.8 and Python 3.9

## [2.0.2] - 2024-05-16

### Changed

- Translations updated

## [2.0.1] - 2024-03-16

### Fixed

- Cell width in the table

## [2.0.0] - 2024-03-16

> [!NOTE]
>
> **This version needs at least Alliance Auth v4.0.0!**
>
> Please make sure to update your Alliance Auth instance **before**
> you install this version, otherwise, an update to Alliance Auth will
> be pulled in unsupervised.

### Added

- Compatibility to Alliance Auth v4
  - Bootstrap 5
  - Django 4.2

### Changed

- JS modernized
- CSS modernizes
- Templates changed to Bootstrap 5

### Removed

- Compatibility to Alliance Auth v3

## [2.0.0-beta.1] - 2024-02-18

> [!NOTE]
>
> **This version needs at least Alliance Auth v4.0.0b1!**
>
> Please make sure to update your Alliance Auth instance **before**
> you install this version, otherwise, an update to Alliance Auth will
> be pulled in unsupervised.

### Added

- Compatibility to Alliance Auth v4
  - Bootstrap 5
  - Django 4.2

### Changed

- JS modernized
- CSS modernizes
- Templates changed to Bootstrap 5

### Removed

- Compatibility to Alliance Auth v3

## [1.12.3] - 2023-09-26

> [!NOTE]
>
> **This is the last version compatible with Alliance Auth v3.**

### Fixed

- Capitalization for translatable strings

### Changed

- Ensure the task only runs one instance at a time and is not fired when already running
- Translations updated
- Test suite updated

## [1.12.2] - 2023-09-20

### Fixed

- Pylint issues
- Missing `<tr>` tag

### Changed

- Use keyword arguments wherever possible
- German translation improved

## [1.12.1] - 2023-09-02

### Changed

- Korean translation improved

## [1.12.0] - 2023-08-31

### Added

- Korean translation

## [1.11.0] - 2023-08-16

### Added

- Spanish translation

## [1.10.2] - 2023-08-13

### Fixed

- Bootstrap CSS fix

## [1.10.1] - 2023-07-30

### Added

- Footer to promote help with the app translation

## [1.10.0] - 2023-04-26

### Added

- Ukrainian translation prepared. Not translated yet, [need translators](https://github.com/ppfeufer/aa-sov-timer/blob/master/CONTRIBUTING.md#translation).

### Changed

- Moved the build process to PEP 621 / pyproject.toml

## [1.9.0] - 2023-04-16

### Added

- Russian translation

## [1.8.0] - 2023-04-13

### Added

- German translation

## [1.7.0] - 2022-10-12

### Update Information

Before you update to this version, make sure you have at least Alliance Auth v3.0.0
installed and running, otherwise, this update will pull in Alliance Auth 3.x
unsupervised with all its breaking changes. (See [Alliance Auth 3.0.0 release notes])

### Changed

- No longer testing for AA alpha versions
- Moved CSS and JS to their own bundled templates
- Minimum requirements
  - Alliance Auth >= 3.2.0
  - Python >= 3.8

### Removed

- Auto retry for ESI and OS errors in tasks, since django-esi already retries all
  relevant errors

## [1.6.0] - 2022-07-11

### Changed

- Use bundled version of AA provided JavaScripts
- Minimum requirement
  - Alliance Auth >= 2.14.0

### Removed

- Unused JavaScript

## [1.5.1] - 2022-05-25

### Added

- Versioned static files to break the browser cache on app update

### Changed

- JavaScript modernized

### Fixed

- Attackers default score in DB

## [1.5.0] - 2022-03-02

### Added

- Test suite for AA 3.x and Django 4

### Changed

- Switched to `setup.cfg` as config file, since `setup.py` is deprecated now

### Removed

- Deprecated settings

## [1.4.0] - 2022-02-28

### Fixed

- [Compatibility] AA 3.x / Django 4 :: ImportError: cannot import name
  'ugettext_lazy' from 'django.utils.translation'

## [1.3.1] - 2022-02-02

### Changed

- Using `path` in URL config instead of soon-to-be removed `url`

## [1.3.0] - 2022-01-30

### Added

- Useragent for ESI calls

### Changed

- `models.TextChoices` refactored for better code readability
- Models refactored
- Views refactored
- Switched to `allianceauth-app-utils` for logging

### Update Instructions

This release has significant changes to its models, so make sure to follow the
instructions below.

```shell
pip install aa-sov-timer==1.3.0

python myauth/manage.py collectstatic --noinput
python myauth/manage.py migrate
python myauth/manage.py sovtimer_load_initial_data
```

And restart your supervisor.

## [1.2.0] - 2022-01-12

### Added

- Tests for Python 3.11

### Changed

- Javascript: `const` instead of `let` where ever appropriate
- Minimum requirements
  - Alliance Auth v2.9.4

## [1.1.0] - 2021-11-30

### Changed

- Minimum requirements
  - Python 3.7
  - Alliance Auth v2.9.3

## [1.0.0] - 2021-11-04

### Changed

- Now with a proper test suite, it's time to bump it to v1.0.0

## [0.6.2] - 2021-09-24

### Added

- Basic tests

### Changed

- Better way of implementing the background colours for campaigns that are upcoming
  or in progress
- Material Icon font updated
- Codebase cleaned up

### Fixed

- Use minified JS in template

## [0.6.1] - 2021-09-23

### Added

- Background colour for campaigns that are upcoming or in progress

## [0.6.0] - 2021-08-06

### Added

- Numbers for total, upcoming (< 4 hrs) and active timers to the table head
  ![image](https://raw.githubusercontent.com/ppfeufer/aa-sov-timer/master/docs/images/changelog/0.6.0/128572686-b01869c4-005e-4141-a28f-7bd286c301f0.png)

## [0.5.8] - 2021-07-08

### Added

- Tested for compatibility with Python 3.9 and Django 3.2

## [0.5.7] - 2021-06-19

### Changed

- Performance improvements

## [0.5.6] - 2021-03-24

### Fixed

- Dotlan links

## [0.5.5] - 2021-02-17

### Fixed

- Alt attribute for alliance logos

### Added

- Explanation for ADM

## [0.5.4] - 2021-01-31

### Fixed

- Let's use the right repo url, shall we? (Thanks @milleruk for the hint!)

## [0.5.3] - 2021-01-29

### Added

- Alliance logos to defender column

## [0.5.2] - 2021-01-27

### Changed

- How to deal with UTC in javascript

## [0.5.1] - 2020-12-16

### Fixed

- Bootstrap classes in template

## [0.5.0] - 2020-11-15

### Changed

- Progress logic improved (task)
- Progress display improved (view)

## [0.4.0] - 2020-11-13

### Changed

- Moved the last ESI calls to the task

### Added

- Progress Icons

## [0.3.0] - 2020-11-12

### Changed

- All relevant updates are now done via scheduled task (see README.md)

### Added

- Active campaigns are now highlighted

## [0.2.0] - 2020-11-11

### Added

- Filter for active campaigns
- zKillboard icon with a link to the constellation killboard on active campaigns

## [0.1.0] - 2020-11-10

### Added

- initial version

[alliance auth 3.0.0 release notes]: https://gitlab.com/allianceauth/allianceauth/-/tags/v3.0.0 "Alliance Auth 3.0.0 release notes"
