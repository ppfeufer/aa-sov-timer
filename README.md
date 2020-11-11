# AA Sovereignty Timer

[![Version](https://img.shields.io/pypi/v/aa-sov-timer?label=release)](https://pypi.org/project/aa-sov-timer/)
[![License](https://img.shields.io/badge/license-GPLv3-green)](https://pypi.org/project/aa-sov-timer/)
[![Python](https://img.shields.io/pypi/pyversions/aa-sov-timer)](https://pypi.org/project/aa-sov-timer/)
[![Django](https://img.shields.io/pypi/djversions/aa-sov-timer?label=django)](https://pypi.org/project/aa-sov-timer/)
[![Code Style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](http://black.readthedocs.io/en/latest/)

Sovereignty campaign overview for Alliance Auth.

![AA Sov Timer Dashboard](https://raw.githubusercontent.com/ppfeufer/aa-sov-timer/master/sovtimer/docs/aa-sov-timer.jpg)


## Installation

**Important**: Please make sure you meet all preconditions before you proceed:

- AA Sovereignty Timer is a plugin for Alliance Auth. If you don't have Alliance Auth running already, please install it first before proceeding. (see the official [AA installation guide](https://allianceauth.readthedocs.io/en/latest/installation/allianceauth.html) for details)
- AA Sovereignty Timer needs the app [django-eveuniverse](https://gitlab.com/ErikKalkoken/django-eveuniverse) to function. Please make sure it is installed, before continuing.

### Step 1 - Install the app

Make sure you are in the virtual environment (venv) of your Alliance Auth installation.
Then install the latest version:

```bash
pip install aa-sov-timer
```

### Step 2 - Update your AA settings

Configure your AA settings (`local.py`) as follows:

- Add `'eveuniverse',` to `INSTALLED_APPS`
- Add `'sovtimer',` to `INSTALLED_APPS`

And setup the update task:

```python
## AA Sovereignty Timer
# Run sovereignty related updates every 30 seconds
CELERYBEAT_SCHEDULE["sovtimer.tasks.run_sov_campaign_updates"] = {
    "task": "sovtimer.tasks.run_sov_campaign_updates",
    "schedule": 30.0,
}
```


### Step 3 - Finalize the installation

Copy static files and run migrations

```bash
python manage.py collectstatic
```

```bash
python manage.py migrate
```

Restart your supervisor services for AA

### Step 4 - Preload Eve Universe data

AA Sovereignty Timer uses Eve Universe data to map IDs to names for solar systems,
regions and constellations. So you need to preload some data from ESI once.
If you already have run this command, you can skip this step.

```bash
python manage.py eveuniverse_load_data map
```

### Step 5 - Setup permission

Now you can setup permissions in Alliance Auth for your users.
Add ``sovtimer | Sovereignty Timer | Can access the Sovereignty Timer module`` to the states and/or
groups you would like to have access.


## Updating

To update your existing installation of AA Sovereignty Timer first enable your virtual environment.

Then run the following commands from your AA project directory (the one that contains `manage.py`).

```bash
pip install -U aa-sov-timer
```

```bash
python manage.py collectstatic
```

```bash
python manage.py migrate
```

Finally restart your AA supervisor services.
