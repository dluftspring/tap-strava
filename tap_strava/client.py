import os
import datetime
import requests
from typing import Dict, Optional, Any, Union

from singer_sdk import RESTStream
from tap_strava.auth import StravaAuthenticator
from urllib.parse import parse_qs, urlparse


class stravaStream(RESTStream):

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
            prior_page = parse_qs(urlparse(response.request.url).query).get(
                "page", [1]
            )[0]
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

        return params
