from typing import List

from singer_sdk import Tap, Stream
from singer_sdk import typing as th  # JSON schema typing helpers
from tap_strava.streams import (
    ActivitiesStream,
)

STREAM_TYPES = [
    ActivitiesStream,
]

class tapStrava(Tap):
    """Strava tap class."""
    name = "tap-strava"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "client_id",
            th.StringType,
            required=True,
            description="The integer identifier of your Strava application"
        ),
        th.Property(
            "client_secret",
            th.StringType,
            required=True,
            description="String secret of your strava application"
        ),
        th.Property(
            "refresh_token",
            th.StringType,
            required=True,
            description="Scoped refresh token obtained from the Strava oauth flow"
        )
    ).to_dict()

    def discover_streams(self) -> List[Stream]:
        """Return a list of discovered streams."""
        return [stream_class(tap=self) for stream_class in STREAM_TYPES]