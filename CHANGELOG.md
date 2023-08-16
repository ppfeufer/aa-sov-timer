# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).


## [In Development] - Unreleased


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

[Alliance Auth 3.0.0 release notes]: https://gitlab.com/allianceauth/allianceauth/-/tags/v3.0.0 "Alliance Auth 3.0.0 release notes"

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
  ![image](https://raw.githubusercontent.com/ppfeufer/aa-sov-timer/master/sovtimer/docs/changelog/0.6.0/128572686-b01869c4-005e-4141-a28f-7bd286c301f0.png)


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
