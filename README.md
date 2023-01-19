# tap-strava

This is a singer tap for the [Strava API](https://developers.strava.com/docs/) built using Meltano's [singer SDK](https://github.com/meltano/sdk).


[![Unit Tests](https://github.com/dluftspring/tap-strava/actions/workflows/test.yaml/badge.svg)](https://github.com/dluftspring/tap-strava/actions/workflows/test.yaml)
[![Integration tests](https://github.com/dluftspring/tap-strava/actions/workflows/integration_tests.yml/badge.svg)](https://github.com/dluftspring/tap-strava/actions/workflows/integration_tests.yml)
## Quickstart

Install the repo from source:

```bash
pip install git+https://github.com/dluftspring/tap-strava.git
```

To run the tap:

```bash
tap-strava --config <path-to-your-config.json> --test
```

This should validate the tap by trying to sync a single record from the available streams

### For developers

```bash
poetry install
```

```bash
poetry run pytest
```

We use mypy for static type checking and black for formatting in CI. To run these locally:

```bash
poetry run mypy -p tap_strava
```

```bash
poetry run black tap_strava
```

It's recommended you set these up as pre-commit hooks to make contributing easier

## Configuration

The tap requires a refresh token, client id, and client secret to be configured. You can get these by following the steps below.

The tap requires a `config.json` file which contains each of your three credentials. Right now the tap only supports a single stream from the `/athlete/activities` endpoint but more will be added in the future.

### Accepted Config Options

A full list of supported settings and capabilities for this
tap is available by running:

```bash
tap-strava --about
```

You'll need to supply three config parameters

| Parameter | Description | Type | Env Variable Alias |
| :-------- | :---------- | :--- | :----------------- |
| client_id | Unique client identifier for your strava application | string (required) | TAP_STRAVA_CLIENT_ID |
| client_secret | Unique secret key for your strava application | string (required) | TAP_STRAVA_CLIENT_SECRET |
| refresh_token | Scoped refresh token obtained from the Strava Oauth flow | string (required) | TAP_STRAVA_REFRESH_TOKEN |
| start_date | Date from which to start syncing data in YYYY-MM-DD format | Date (optional) | TAP_STRAVA_START_DATE |
| end_date | Date at which to stop syncing data in YYYY-MM-DD format | Date (optional) | TAP_STRAVA_END_DATE |

Note that the usage of start and end date parameters will override the default behaviour of syncing based on incremental state

You can set these parameters as environment variables or by specifying a json configuration file with the following info

```json

  {
    "client_id": "<YOUR CLIENT ID>",
    "client_secret": "<YOUR CLIENT SECRET>",
    "refresh_token": "<YOUR REFRESH TOKEN>",
    "start_date": "2021-01-01",
    "end_date": "2021-01-31"
  }
```

## Getting a properly scoped refresh token

The Strava API implements Oauth2 which they've documented in detail [here](https://developers.strava.com/docs/authentication/). For the purposes of getting your own data out there is a one time set up process required in order to obtain a properly scoped refresh token so the tap can continue to function. If the tap stops working or you find that the scopes you've requested aren't sufficent to access data you'll have to go through this flow again with the correct scopes.

To make this smoother we'd have to spin up a web server to handle redirect requests and that's not really in scope for this project! If anyone wants to make that happen and pay for the hosting I'd be more than happy to accept a PR. However, I think for the purposes of a data exporting application it's relatively safe to assume that scopes shouldn't change frequently once set.

Before you do any of this I'm assuming you've already created an [app on Strava](https://developers.strava.com/docs/getting-started/#:~:text=If%20you%20have%20not%20already,My%20API%20Application%E2%80%9D%20page%20now.) and have a client id and a client secret available. I'm also assuming you have curl installed on the command line.

### Steps

Open your browser and enter the following URL

```markdown
https://www.strava.com/oauth/authorize?client_id=<YOUR_CLIENT_ID>&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=<YOUR_SCOPES>
```

You should be redirected to a Strava authentication modal that looks like:

![Strava Auth Modal](images/strava_auth_modal.png)

After you click authorize you should be redirected to an empty page with a URL that looks like:

```markdown
http://localhost/exchange_code?state=&code=<YOUR_ACCESS_CODE>&scope=<YOUR_SCOPES>
```

Copy the access code and then use it to generate your refresh token:

```bash
curl -X POST https://www.strava.com/api/v3/oauth/token \
  -d client_id=<YOUR_CLIENT_ID> \
  -d client_secret=<YOUR_CLIENT_SECRET> \
  -d code=<YOUR_ACCESS_CODE> \
  -d grant_type=authorization_code
```

You'll get a response like

```json
{
    "token_type": "Bearer",
    "expires_at": 1672268955,
    "expires_in": 21600,
    "refresh_token": "definitely-a-real-refresh-token",
    "access_token": "definitely-a-real-access-token",
    .
    .
    .
}
```

Copy the refresh token and use it to configure the tap along with your client id and client secret.