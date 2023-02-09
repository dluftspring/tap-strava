import time
import datetime
import requests
from dateutil import parser as date_parser
from typing import Dict, Optional, Any, Union
from singer_sdk.exceptions import RetriableAPIError, FatalAPIError

from singer_sdk import RESTStream
from tap_strava.auth import StravaAuthenticator
from urllib.parse import parse_qs, urlparse


class StravaStream(RESTStream):

    """
    Base stream class for the Strava API
    """

    @property
    def url_base(self):
        return "https://www.strava.com/api/v3/"

    @property
    def authenticator(self):
        """
        Instantiates OAuth2 authenticatior class for the Strava API
        """

        return StravaAuthenticator(
            self,
            auth_endpoint="https://www.strava.com/oauth/token",
        )

    def get_next_page_token(
        self, response: requests.Response, current_value: int
    ) -> Union[None, int]:
        """
        Returns the next page integer based on prior page in the request
        """

        self.logger.debug(f"Current value of the page number is {current_value}")
        # Break if the result is empty meaning we're on the last page
        if not response.json():
            next_page_token = None
        else:
            parsed_url = urlparse(response.request.url)
            query_string = parse_qs(parsed_url.query)
            prior_page = query_string.get("page", [1])[0]
            next_page_token = int(prior_page) + 1

        return next_page_token

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization."""

        params = {
            "acccess_token": self.authenticator.access_token,
            "per_page": self.config.get("results_per_page", 30),
            "page": next_page_token,
        }

        start_date = self.config.get("start_date", None)
        end_date = self.config.get("end_date", None)

        if self.replication_key:
            start_value = self.get_starting_replication_key_value(context)
            self.logger.debug(f"Your starting replication value is: {start_value}")
            if start_value:
                params["after"] = self._datetime_to_epoch_time(start_value)
        if start_date:
            params["after"] = self._datetime_to_epoch_time(start_date)
        if end_date:
            params["before"] = self._datetime_to_epoch_time(end_date)

        return params

    def check_rate_limit(self, response: requests.Response) -> dict:
        """
        Checks the rate limit and sleeps if we're over the limit
        """

        rate_limit = response.headers.get("x-ratelimit-limit", None)
        rate_usage = response.headers.get("x-ratelimit-usage", None)
        per_15_min_limit, daily_limit = rate_limit.strip().split(",")
        per_15_min_usage, daily_usage = rate_usage.strip().split(",")
        self.logger.info(
            f"""You have used: {per_15_min_usage} of your {per_15_min_limit} 15 minute request allocation
            You have used: {daily_usage} of your {daily_limit} daily request allocation"""
        )

        if int(per_15_min_usage) >= int(per_15_min_limit):
            self.logger.info("Rate limit exceeded, going to sleep for 15 minutes")
            time.sleep(900)

        if int(daily_usage) >= int(daily_limit):
            raise FatalAPIError("Daily rate limit exceeded... exiting", response)

    def validate_response(self, response: requests.Response) -> None:
        """
        Custom implementation of sdk API validation method so we can
        throttle the requests if we're over the 15 minute or daily rate
        limit imposed by the Strava API
        """

        self.check_rate_limit(response)
        if (
            response.status_code in self.extra_retry_statuses
            or 500 <= response.status_code < 600
        ):
            msg = self.response_error_message(response)
            raise RetriableAPIError(msg, response)
        elif 400 <= response.status_code < 500:
            msg = self.response_error_message(response)
            raise FatalAPIError(msg)

    def _datetime_to_epoch_time(self, dt: str) -> int:
        """
        Converts a datetime string to epoch time
        """

        self.logger.debug(f"Trying to convert {dt} to epoch time")
        return date_parser.parse(dt).strftime("%s")
