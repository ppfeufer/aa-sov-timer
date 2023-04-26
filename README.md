# AA Sovereignty Timer

[![Version](https://img.shields.io/pypi/v/aa-sov-timer?label=release "Version")](https://pypi.org/project/aa-sov-timer/)
[![License](https://img.shields.io/badge/license-GPLv3-green "License")](https://pypi.org/project/aa-sov-timer/)
[![Python](https://img.shields.io/pypi/pyversions/aa-sov-timer "Python")](https://pypi.org/project/aa-sov-timer/)
[![Django](https://img.shields.io/pypi/djversions/aa-sov-timer?label=django "Django")](https://pypi.org/project/aa-sov-timer/)
[![Code Style: black](https://img.shields.io/badge/code%20style-black-000000.svg "Code Style: black")](http://black.readthedocs.io/en/latest/)
[![Automated Checks](https://github.com/ppfeufer/aa-sov-timer/actions/workflows/automated-checks.yml/badge.svg "Automated Checks")](https://github.com/ppfeufer/aa-sov-timer/actions/workflows/automated-checks.yml)
[![codecov](https://codecov.io/gh/ppfeufer/aa-sov-timer/branch/master/graph/badge.svg?token=J9PBF0HM8C "codecov")](https://codecov.io/gh/ppfeufer/aa-sov-timer)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg "Contributor Covenant")](https://github.com/ppfeufer/aa-forum/blob/master/CODE_OF_CONDUCT.md)
[![Discord](https://img.shields.io/discord/790364535294132234?label=discord "Discord")](https://discord.gg/zmh52wnfvM)


Sovereignty campaign overview for Alliance Auth.


---

<!-- TOC -->
* [AA Sovereignty Timer](#aa-sovereignty-timer)
  * [Screenshots](#screenshots)
    * [AA Sov Timer Dashboard (Light Mode)](#aa-sov-timer-dashboard-light-mode)
    * [AA Sov Timer Dashboard (Dark Mode)](#aa-sov-timer-dashboard-dark-mode)
  * [Installation](#installation)
    * [Step 1: Installing the App](#step-1-installing-the-app)
    * [Step 2: Update Your AA Settings](#step-2-update-your-aa-settings)
    * [Step 3: Finalizing the Installation](#step-3-finalizing-the-installation)
    * [Step 4: Preload Eve Universe Data](#step-4-preload-eve-universe-data)
    * [Step 5: Setting up Permission](#step-5-setting-up-permission)
    * [Step 6: Keep Campaigns Updated](#step-6-keep-campaigns-updated)
  * [Updating](#updating)
<!-- TOC -->

---


## Screenshots

### AA Sov Timer Dashboard (Light Mode)

![AA Sov Timer Dashboard (Light Mode)](https://raw.githubusercontent.com/ppfeufer/aa-sov-timer/master/sovtimer/docs/presentation/aa-sov-timer-light-mode.jpg "AA Sov Timer Dashboard (Light Mode)")


### AA Sov Timer Dashboard (Dark Mode)

![AA Sov Timer Dashboard (Dark Mode)](https://raw.githubusercontent.com/ppfeufer/aa-sov-timer/master/sovtimer/docs/presentation/aa-sov-timer-dark-mode.jpg "AA Sov Timer Dashboard (Dark Mode)")


## Installation

**Important**: Please make sure you meet all preconditions before you proceed:

- AA Sovereignty Timer is a plugin for Alliance Auth. If you don't have Alliance
  Auth running already, please install it first before proceeding. (see the official
  [AA installation guide](https://allianceauth.readthedocs.io/en/latest/installation/allianceauth.html) for details)
- AA Sovereignty Timer needs the app [django-eveuniverse](https://gitlab.com/ErikKalkoken/django-eveuniverse)
  to function. Please make sure it is installed before continuing.


### Step 1: Installing the App

Make sure you're in the virtual environment (venv) of your Alliance Auth installation.
Then install the latest version:

```shell
pip install aa-sov-timer
```


### Step 2: Update Your AA Settings

Configure your AA settings (`local.py`) as follows:

- Add `'eveuniverse',` to `INSTALLED_APPS`
- Add `'sovtimer',` to `INSTALLED_APPS`

Restart your supervisor


### Step 3: Finalizing the Installation

Copy static files and run migrations

```shell
python manage.py collectstatic
```

```shell
python manage.py migrate
```


### Step 4: Preload Eve Universe Data

AA Sovereignty Timer uses Eve Universe data to map IDs to names for solar systems,
regions and constellations. So you need to preload some data from ESI once.
If you already have run this command, you can skip this step.

```shell
python manage.py eveuniverse_load_data map
```

```shell
python manage.py sovtimer_load_initial_data
```

Both commands might take a moment or two, so be patient ...


### Step 5: Setting up Permission

Now you can set up permissions in Alliance Auth for your users.
Add ``sovtimer | Sovereignty Timer | Can access the Sovereignty Timer module`` to
the states and/or groups you would like to have access.


### Step 6: Keep Campaigns Updated

Add the following scheduled task to your `local.py`. One done, restart your supervisor.

```python
# AA Sovereignty Timer - Run sovereignty related updates every 30 seconds
CELERYBEAT_SCHEDULE["sovtimer.tasks.run_sov_campaign_updates"] = {
    "task": "sovtimer.tasks.run_sov_campaign_updates",
    "schedule": 30.0,
}
```

Now your system is updating the sovereignty campaigns every 30 seconds.


## Updating

To update your existing installation of AA Sovereignty Timer, first enable your
virtual environment.

Then run the following commands from your AA project directory (the one that
contains `manage.py`).

```shell
pip install -U aa-sov-timer
```

```shell
python manage.py collectstatic
```

```shell
python manage.py migrate
```

Finally, restart your AA supervisor services.
