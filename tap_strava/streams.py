from typing import Optional, Union, Dict, Any
from pathlib import Path
import requests
from tap_strava.client import StravaStream

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")


class ActivitiesStream(StravaStream):
    name = "activities"
    path = "/athlete/activities"
    primary_keys = ["id"]
    replication_key = "start_date"
    schema_filepath = SCHEMAS_DIR / "activities.json"

    def get_child_context(self, record: dict, context: Optional[dict]) -> dict:
        """
        This is how we pass activity_id to all relevant substreams that inherit
        from the Activities Stream class
        """
        return {"activity_id": record["id"]}


class ActivityKudoersStream(StravaStream):
    """
    Sub stream to retrieve kudoers for a given activity
    """

    name = "activity_kudoers"
    parent_stream_type = ActivitiesStream
    ignore_parent_replication_keys = True
    path = "/activities/{activity_id}/kudos"
    schema_filepath = SCHEMAS_DIR / "activity_kudoers.json"


class ActivityCommentsStream(StravaStream):
    """
    Sub stream to retrieve comments for a given activity
    """

    name = "activity_comments"
    parent_stream_type = ActivitiesStream
    ignore_parent_replication_keys = True
    primary_keys = ["id"]
    replication_key = "created_at"
    path = "/activities/{activity_id}/comments"
    schema_filepath = SCHEMAS_DIR / "activity_comments.json"

    def get_next_page_token(
        self, response: requests.Response, current_value: int
    ) -> Union[None, int]:
        """
        Returns the next page integer based on prior page in the request.
        We're overriding here because activity_comments uses a different pagination header
        than the other API endpoints
        """

        response_json = response.json()
        if not response.json():
            return None

        # We only need the last item in the list to get the cursor value
        next_page_token = response_json[-1].get("cursor", None)
        self.logger.debug(f"Next page token is {next_page_token}")

        return next_page_token

    def get_url_params(
        self, context: Optional[dict], next_page_token: Optional[Any]
    ) -> Dict[str, Any]:
        """Return a dictionary of values to be used in URL parameterization."""

        params = {
            "acccess_token": self.authenticator.access_token,
            "per_page": self.config.get("results_per_page", 30),
            "after_cursor": next_page_token,
        }

        start_date = self.config.get("start_date", None)
        end_date = self.config.get("end_date", None)

        if start_date:
            params["after"] = self._datetime_to_epoch_time(start_date)
        if end_date:
            params["before"] = self._datetime_to_epoch_time(end_date)

        return params
