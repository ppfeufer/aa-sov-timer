# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).


## [In Development] - Unreleased


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

- Better way on implementing the background colours for campaigns that are upcoming
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
- zKillboard icon with link to constellation killboard on active campaigns


## [0.1.0] - 2020-11-10

### Added

- initial version
