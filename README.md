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
[![Discord](https://img.shields.io/discord/399006117012832262?label=discord)](https://discord.gg/fjnHAmk)

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/N4N8CL1BY)

Sovereignty campaign overview for Alliance Auth.

______________________________________________________________________

<!-- mdformat-toc start --slug=github --maxlevel=6 --minlevel=2 -->

- [Screenshots](#screenshots)
  - [All Timers](#all-timers)
  - [Upcoming Timers (Filtered)](#upcoming-timers-filtered)
  - [Active Timers (Filtered)](#active-timers-filtered)
- [Installation](#installation)
  - [Bare Metal Installation](#bare-metal-installation)
    - [Step 1: Installing the App](#step-1-installing-the-app)
    - [Step 2: Update Your AA Settings](#step-2-update-your-aa-settings)
    - [Step 3: Finalizing the Installation](#step-3-finalizing-the-installation)
    - [Step 4: Preload EVE SDE Data](#step-4-preload-eve-sde-data)
    - [Step 5: Restart Supervisor](#step-5-restart-supervisor)
  - [Docker Installation](#docker-installation)
    - [Step 1: Add the App](#step-1-add-the-app)
    - [Step 2: Update Your AA Settings](#step-2-update-your-aa-settings-1)
    - [Step 3: Build Auth and Restart Your Containers](#step-3-build-auth-and-restart-your-containers)
    - [Step 4: Finalizing the Installation](#step-4-finalizing-the-installation)
  - [Common Steps / Configuration](#common-steps--configuration)
    - [(Optional) Allow Public Views](#optional-allow-public-views)
- [Updating](#updating)
  - [Bare Metal Installation](#bare-metal-installation-1)
  - [Docker Installation](#docker-installation-1)
  - [Common Steps](#common-steps)
- [Changelog](#changelog)
- [Translation Status](#translation-status)
- [Contributing](#contributing)

<!-- mdformat-toc end -->

______________________________________________________________________

## Screenshots<a name="screenshots"></a>

### All Timers<a name="all-timers"></a>

![AA Sov Timer DashboardAA Sov Timer (All Timers)](https://raw.githubusercontent.com/ppfeufer/aa-sov-timer/master/docs/images/presentation/aa-sov-timer.jpg "AA Sov Timer (All Timers)")

### Upcoming Timers (Filtered)<a name="upcoming-timers-filtered"></a>

![AA Sov Timer (Upcoming Timers)](https://raw.githubusercontent.com/ppfeufer/aa-sov-timer/master/docs/images/presentation/aa-sov-timer-upcoming-filtered.jpg "AA Sov Timer (Upcoming Timers)")

### Active Timers (Filtered)<a name="active-timers-filtered"></a>

![AA Sov Timer (Active Timers)](https://raw.githubusercontent.com/ppfeufer/aa-sov-timer/master/docs/images/presentation/aa-sov-timer-active-filtered.jpg "AA Sov Timer (Active Timers)")

## Installation<a name="installation"></a>

> [!IMPORTANT]
>
> Please make sure you meet all preconditions before you proceed.

> [!IMPORTANT]
>
> This app is utilising features that are only available in Alliance Auth >= 4.12.0.
> Please make sure to update your Alliance Auth instance before installing this app,
> otherwise, an update to Alliance Auth will be pulled in unsupervised.

- AA Sovereignty Timer is a plugin for Alliance Auth. If you don't have Alliance
  Auth running already, please install it first before proceeding. (see the official
  [AA installation guide](https://allianceauth.readthedocs.io/en/latest/installation/allianceauth.html) for details)

### Bare Metal Installation<a name="bare-metal-installation"></a>

#### Step 1: Installing the App<a name="step-1-installing-the-app"></a>

Make sure you're in the virtual environment (venv) of your Alliance Auth installation.
Then install the latest version:

```shell
pip install aa-sov-timer==3.5.1
```

#### Step 2: Update Your AA Settings<a name="step-2-update-your-aa-settings"></a>

Configure your AA settings (`local.py`) as follows:

- Modify `INSTALLED_APPS` to include the following entries:

  ```python
  INSTALLED_APPS = [
      # ...
      "eve_sde",  # Only if not already added for another app
      "sovtimer",
      # ...
  ]

  # This line right below the `INSTALLED_APPS` list, and only if not already added for another app
  INSTALLED_APPS = ["modeltranslation"] + INSTALLED_APPS
  ```

- Add the Scheduled Tasks

  ```python
  if "sovtimer" in INSTALLED_APPS:
      # AA Sovereignty Timer - Run sovereignty related updates every 30 seconds
      CELERYBEAT_SCHEDULE["sovtimer.tasks.run_sov_campaign_updates"] = {
          "task": "sovtimer.tasks.run_sov_campaign_updates",
          "schedule": 30,
      }

  if "eve_sde" in INSTALLED_APPS:
      # Run at 12:00 UTC each day
      CELERYBEAT_SCHEDULE["EVE SDE :: Check for SDE Updates"] = {
          "task": "eve_sde.tasks.check_for_sde_updates",
          "schedule": crontab(minute="0", hour="12"),
      }
  ```

#### Step 3: Finalizing the Installation<a name="step-3-finalizing-the-installation"></a>

Copy static files and run migrations

```shell
python manage.py collectstatic
python manage.py migrate
```

#### Step 4: Preload EVE SDE Data<a name="step-4-preload-eve-sde-data"></a>

AA Sovereignty Timer uses EVE SDE data to map IDs to names for solar systems,
regions and constellations. So you need to preload some data from SDE once.
If you already have run this command, you can skip this step.

```shell
python manage.py esde_load_sde
python manage.py sovtimer_load_initial_data
```

Both commands might take a moment or two, so be patient ...

#### Step 5: Restart Supervisor<a name="step-5-restart-supervisor"></a>

Once you have completed all previous steps, restart your AA supervisor service to apply the changes.

**Continue with the [Common Steps / Configuration](#common-steps--configuration) below to finish the installation.**

### Docker Installation<a name="docker-installation"></a>

#### Step 1: Add the App<a name="step-1-add-the-app"></a>

Add the app to your `conf/requirements.txt`:

```text
aa-sov-timer==3.5.1
```

#### Step 2: Update Your AA Settings<a name="step-2-update-your-aa-settings-1"></a>

Configure your AA settings (`conf/local.py`) as follows:

- Modify `INSTALLED_APPS` to include the following entries:

  ```python
  INSTALLED_APPS = [
      # ...
      "eve_sde",  # Only if not already added for another app
      "sovtimer",
      # ...
  ]

  # This line right below the `INSTALLED_APPS` list, and only if not already added for another app
  INSTALLED_APPS = ["modeltranslation"] + INSTALLED_APPS
  ```

- Add the Scheduled Tasks

  ```python
  if "sovtimer" in INSTALLED_APPS:
      # AA Sovereignty Timer - Run sovereignty related updates every 30 seconds
      CELERYBEAT_SCHEDULE["sovtimer.tasks.run_sov_campaign_updates"] = {
          "task": "sovtimer.tasks.run_sov_campaign_updates",
          "schedule": 30,
      }

  if "eve_sde" in INSTALLED_APPS:
      # Run at 12:00 UTC each day
      CELERYBEAT_SCHEDULE["EVE SDE :: Check for SDE Updates"] = {
          "task": "eve_sde.tasks.check_for_sde_updates",
          "schedule": crontab(minute="0", hour="12"),
      }
  ```

#### Step 3: Build Auth and Restart Your Containers<a name="step-3-build-auth-and-restart-your-containers"></a>

```shell
docker compose build --no-cache
docker compose --env-file=.env up -d
```

#### Step 4: Finalizing the Installation<a name="step-4-finalizing-the-installation"></a>

Run migrations, copy static files and load EVE SDE data:

```shell
docker compose exec allianceauth_gunicorn bash

auth collectstatic
auth migrate

auth esde_load_sde
auth sovtimer_load_initial_data
```

**Continue with the [Common Steps / Configuration](#common-steps--configuration) below to finish the installation.**

### Common Steps / Configuration<a name="common-steps--configuration"></a>

#### (Optional) Allow Public Views<a name="optional-allow-public-views"></a>

This app supports AA's feature of public views. \
To allow this feature, please add `"sovtimer",`, to the list of `APPS_WITH_PUBLIC_VIEWS` in your `local.py` or `conf/local.py` for Docker:

```python
APPS_WITH_PUBLIC_VIEWS = [
    "sovtimer",
]
```

> [!NOTE]
>
> If you don't have a list for `APPS_WITH_PUBLIC_VIEWS` yet, then add the whole
> block from here.

Restart your supervisor service or your Docker containers to apply the changes.

## Updating<a name="updating"></a>

### Bare Metal Installation<a name="bare-metal-installation-1"></a>

To update your existing installation of AA Sovereignty Timer, first enable your
virtual environment.

Then run the following commands from your AA project directory (the one that
contains `manage.py`).

```shell
pip install aa-sov-timer==3.5.1

python manage.py collectstatic
python manage.py migrate
```

Finally, restart your AA supervisor service.

### Docker Installation<a name="docker-installation-1"></a>

To update your existing installation of AA Sovereignty Timer, all you need to do is to update the respective line in your `conf/requirements.txt` file to the latest version.

```text
aa-sov-timer==3.5.1
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
