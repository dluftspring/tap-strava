from pathlib import Path
from tap_strava.client import stravaStream

SCHEMAS_DIR = Path(__file__).parent / Path("./schemas")

class ActivitiesStream(stravaStream):
    name = "activities"
    path = "/athlete/activities"
    primary_keys = ["id"]
    replication_key = "start_date"
    schema_filepath = SCHEMAS_DIR / "activities.json"