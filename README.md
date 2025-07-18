# AA Sovereignty Timer<a name="aa-sovereignty-timer"></a>

[![Version](https://img.shields.io/pypi/v/aa-sov-timer?label=release "Version")](https://pypi.org/project/aa-sov-timer/)
[![License](https://img.shields.io/badge/license-GPLv3-green "License")](https://pypi.org/project/aa-sov-timer/)
[![Python](https://img.shields.io/pypi/pyversions/aa-sov-timer "Python")](https://pypi.org/project/aa-sov-timer/)
[![Django](https://img.shields.io/pypi/djversions/aa-sov-timer?label=django "Django")](https://pypi.org/project/aa-sov-timer/)
![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/ppfeufer/aa-sov-timer/master.svg)](https://results.pre-commit.ci/latest/github/ppfeufer/aa-sov-timer/master)
[![Code Style: black](https://img.shields.io/badge/code%20style-black-000000.svg "Code Style: black")](http://black.readthedocs.io/en/latest/)
[![Automated Checks](https://github.com/ppfeufer/aa-sov-timer/actions/workflows/automated-checks.yml/badge.svg "Automated Checks")](https://github.com/ppfeufer/aa-sov-timer/actions/workflows/automated-checks.yml)
[![codecov](https://codecov.io/gh/ppfeufer/aa-sov-timer/branch/master/graph/badge.svg?token=J9PBF0HM8C "codecov")](https://codecov.io/gh/ppfeufer/aa-sov-timer)
[![Translation status](https://weblate.ppfeufer.de/widget/alliance-auth-apps/aa-sov-timer/svg-badge.svg)](https://weblate.ppfeufer.de/engage/alliance-auth-apps/)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg "Contributor Covenant")](https://github.com/ppfeufer/aa-sov-timer/blob/master/CODE_OF_CONDUCT.md)
[![Discord](https://img.shields.io/discord/790364535294132234?label=discord "Discord")](https://discord.gg/zmh52wnfvM)

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/N4N8CL1BY)

Sovereignty campaign overview for Alliance Auth.

______________________________________________________________________

<!-- mdformat-toc start --slug=github --maxlevel=6 --minlevel=2 -->

- [Screenshots](#screenshots)
  - [AA Sov Timer Dashboard](#aa-sov-timer-dashboard)
- [Installation](#installation)
  - [Bare Metaal Installation](#bare-metaal-installation)
    - [Step 1: Installing the App](#step-1-installing-the-app)
    - [Step 2: Update Your AA Settings](#step-2-update-your-aa-settings)
    - [Step 3: Finalizing the Installation](#step-3-finalizing-the-installation)
    - [Step 4: Preload Eve Universe Data](#step-4-preload-eve-universe-data)
    - [Step 5: Setting up Permission](#step-5-setting-up-permission)
    - [Step 6: Keep Campaigns Updated](#step-6-keep-campaigns-updated)
  - [Docker Installation](#docker-installation)
    - [Step 1: Add the App](#step-1-add-the-app)
    - [Step 2: Update Your AA Settings](#step-2-update-your-aa-settings-1)
    - [Step 3: Build Auth and Restart Your Containers](#step-3-build-auth-and-restart-your-containers)
    - [Step 4: Finalizing the Installation](#step-4-finalizing-the-installation)
- [Updating](#updating)
  - [Bare Metal Installation](#bare-metal-installation)
  - [Docker Installation](#docker-installation-1)
  - [Common Steps](#common-steps)
- [Changelog](#changelog)
- [Translation Status](#translation-status)
- [Contributing](#contributing)

<!-- mdformat-toc end -->

______________________________________________________________________

## Screenshots<a name="screenshots"></a>

### AA Sov Timer Dashboard<a name="aa-sov-timer-dashboard"></a>

![AA Sov Timer Dashboard](https://raw.githubusercontent.com/ppfeufer/aa-sov-timer/master/docs/images/presentation/aa-sov-timer.jpg "AA Sov Timer Dashboard")

## Installation<a name="installation"></a>

> [!IMPORTANT]
>
> Please make sure you meet all preconditions before you proceed.

- AA Sovereignty Timer is a plugin for Alliance Auth. If you don't have Alliance
  Auth running already, please install it first before proceeding. (see the official
  [AA installation guide](https://allianceauth.readthedocs.io/en/latest/installation/allianceauth.html) for details)
- AA Sovereignty Timer needs the app [django-eveuniverse](https://gitlab.com/ErikKalkoken/django-eveuniverse)
  to function. Please make sure it is installed before continuing.

### Bare Metaal Installation<a name="bare-metaal-installation"></a>

#### Step 1: Installing the App<a name="step-1-installing-the-app"></a>

Make sure you're in the virtual environment (venv) of your Alliance Auth installation.
Then install the latest version:

```shell
pip install aa-sov-timer
```

#### Step 2: Update Your AA Settings<a name="step-2-update-your-aa-settings"></a>

Configure your AA settings (`local.py`) as follows:

- Add `'eveuniverse',` to `INSTALLED_APPS` if not already done for another app
- Add `'sovtimer',` to `INSTALLED_APPS`

Restart your supervisor

#### Step 3: Finalizing the Installation<a name="step-3-finalizing-the-installation"></a>

Copy static files and run migrations

```shell
python manage.py collectstatic
python manage.py migrate
```

#### Step 4: Preload Eve Universe Data<a name="step-4-preload-eve-universe-data"></a>

AA Sovereignty Timer uses Eve Universe data to map IDs to names for solar systems,
regions and constellations. So you need to preload some data from ESI once.
If you already have run this command, you can skip this step.

```shell
python manage.py eveuniverse_load_data map
python manage.py sovtimer_load_initial_data
```

Both commands might take a moment or two, so be patient ...

#### Step 5: Setting up Permission<a name="step-5-setting-up-permission"></a>

Now you can set up permissions in Alliance Auth for your users.
Add `sovtimer | Sovereignty Timer | Can access the Sovereignty Timer module` to
the states and/or groups you would like to have access.

#### Step 6: Keep Campaigns Updated<a name="step-6-keep-campaigns-updated"></a>

Add the following scheduled task to your `local.py`. One done, restart your supervisor.

```python
# AA Sovereignty Timer - Run sovereignty related updates every 30 seconds
CELERYBEAT_SCHEDULE["sovtimer.tasks.run_sov_campaign_updates"] = {
    "task": "sovtimer.tasks.run_sov_campaign_updates",
    "schedule": 30,
}
```

Now your system is updating the sovereignty campaigns every 30 seconds.

### Docker Installation<a name="docker-installation"></a>

#### Step 1: Add the App<a name="step-1-add-the-app"></a>

Add the app to your `conf/requirements.txt`:

```text
aa-sov-timer==2.5.0
```

#### Step 2: Update Your AA Settings<a name="step-2-update-your-aa-settings-1"></a>

Configure your AA settings (`conf/local.py`) as follows:

- Add `'eveuniverse',` to `INSTALLED_APPS` if not already done for another app
- Add `'sovtimer',` to `INSTALLED_APPS`
- Add the Scheduled Task

```python
# AA Sovereignty Timer - Run sovereignty related updates every 30 seconds
CELERYBEAT_SCHEDULE["sovtimer.tasks.run_sov_campaign_updates"] = {
    "task": "sovtimer.tasks.run_sov_campaign_updates",
    "schedule": 30,
}
```

#### Step 3: Build Auth and Restart Your Containers<a name="step-3-build-auth-and-restart-your-containers"></a>

```shell
docker compose build --no-cache
docker compose --env-file=.env up -d
```

#### Step 4: Finalizing the Installation<a name="step-4-finalizing-the-installation"></a>

Run migrations, copy static files and load EVE universe data:

```shell
docker compose exec allianceauth_gunicorn bash

auth collectstatic
auth migrate

auth eveuniverse_load_data map
auth sovtimer_load_initial_data
```

## Updating<a name="updating"></a>

### Bare Metal Installation<a name="bare-metal-installation"></a>

To update your existing installation of AA Sovereignty Timer, first enable your
virtual environment.

Then run the following commands from your AA project directory (the one that
contains `manage.py`).

```shell
pip install -U aa-sov-timer

python manage.py collectstatic
python manage.py migrate
```

Finally, restart your AA supervisor service.

### Docker Installation<a name="docker-installation-1"></a>

To update your existing installation of AA Sovereignty Timer, all you need to do is to update the respective line in your `conf/requirements.txt` file to the latest version.

```text
aa-sov-timer==2.5.0
```

Now rebuild your containers and restart them:

```shell
docker compose build --no-cache
docker compose --env-file=.env up -d
```

After that, run the following commands to update your database and static files:

```shell
docker compose exec allianceauth_gunicorn bash

auth collectstatic
auth migrate
```

### Common Steps<a name="common-steps"></a>

It is possible that some versions need some more changes. Always read the [changelog] and/or [release notes](https://github.com/ppfeufer/aa-sov-timer/releases) to find out more.

## Changelog<a name="changelog"></a>

See [CHANGELOG.md][changelog] for a detailed list of changes and improvements.

## Translation Status<a name="translation-status"></a>

[![Translation status](https://weblate.ppfeufer.de/widget/alliance-auth-apps/aa-sov-timer/multi-auto.svg)](https://weblate.ppfeufer.de/engage/alliance-auth-apps/)

Do you want to help translate this app into your language or improve the existing
translation? - [Join our team of translators][weblate engage]!

## Contributing<a name="contributing"></a>

Do you want to contribute to this project? That's cool!

Please make sure to read the [Contribution Guidelines].\
(I promise, it's not much, just some basics)

<!-- Links -->

[changelog]: https://github.com/ppfeufer/aa-sov-timer/blob/master/CHANGELOG.md
[contribution guidelines]: https://github.com/ppfeufer/aa-sov-timer/blob/master/CONTRIBUTING.md "Contribution Guidelines"
[weblate engage]: https://weblate.ppfeufer.de/engage/alliance-auth-apps/ "Weblate Translations"
