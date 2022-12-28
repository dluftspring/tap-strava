from singer_sdk.authenticators import APIAuthenticatorBase
from singer_sdk.streams import Stream
from datetime import datetime
import requests
from singer import utils
from singer_sdk.helpers._util import utc_now

class StravaAuthenticator(APIAuthenticatorBase):
    """Strava API OAuth Authenticator"""

    def __init__(
        self,
        stream: Stream,
        auth_endpoint: str | None = None,
        oauth_scopes: str | None = None,
        default_expiration: int | None = None,
    ) -> None:
        """Create a new authenticator.
        Args:
            stream: The stream instance to use with this authenticator.
            auth_endpoint: API username.
            oauth_scopes: API password.
            default_expiration: Default token expiry in seconds.
        """
        super().__init__(stream=stream)
        self._auth_endpoint = auth_endpoint
        self._default_expiration = default_expiration
        self._oauth_scopes = oauth_scopes

        # Initialize internal tracking attributes
        self.refresh_token: str | None = None
        self.access_token: str | None = None
        self.last_refreshed: datetime | None = None
        self.expires_in: int | None = None

    @property
    def auth_params(self) -> dict:
        """Return a dictionary of query params to be applied.
        These will be merged with any `http_headers` specified in the stream.
        Returns:
            HTTP query params for authentication.
        """
        if not self.is_token_valid():
            self.update_access_token()
        result = super().auth_headers
        result["access_token"] = f"{self.access_token}"
        return result

    @property
    def auth_endpoint(self) -> str:
        """Get the authorization endpoint.
        Returns:
            The API authorization endpoint if it is set.
        Raises:
            ValueError: If the endpoint is not set.
        """
        if not self._auth_endpoint:
            raise ValueError("Authorization endpoint not set.")
        return self._auth_endpoint

    @property
    def oauth_scopes(self) -> str | None:
        """Get OAuth scopes.
        Returns:
            String of OAuth scopes, or None if not set.
        """
        return self._oauth_scopes

    @property
    def oauth_request_payload(self) -> dict:
        """Get request body.
        Returns:
            A plain (OAuth) or encrypted (JWT) request body.
        """
        return self.oauth_request_body

    @property
    def oauth_request_body(self) -> dict:
        """
        Format the request body Stravas auth endpoint is expecting
        """

        return {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token or self.config.get('refresh_token'),
            "grant_type": "refresh_token",
        }

    @property
    def client_id(self) -> str | None:
        """Get client ID string to be used in authentication.
        Returns:
            Optional client secret from stream config if it has been set.
        """
        if self.config:
            return self.config.get("client_id")
        return None

    @property
    def client_secret(self) -> str | None:
        """Get client secret to be used in authentication.
        Returns:
            Optional client secret from stream config if it has been set.
        """
        if self.config:
            return self.config.get("client_secret")
        return None

    def is_token_valid(self) -> bool:
        """Check if token is valid.
        Returns:
            True if the token is valid (fresh).
        """
        if self.last_refreshed is None:
            return False
        if not self.expires_in:
            return True
        if self.expires_in > (utils.now() - self.last_refreshed).total_seconds():
            return True
        return False

    # Authentication and refresh
    def update_access_token(self) -> None:
        """Update `access_token` along with: `last_refreshed` and `expires_in`.
        Raises:
            RuntimeError: When OAuth login fails.
        """
        request_time = utc_now()
        auth_request_payload = self.oauth_request_payload
        token_response = requests.post(self.auth_endpoint, data=auth_request_payload)
        try:
            token_response.raise_for_status()
            self.logger.info("OAuth authorization attempt was successful.")
        except Exception as ex:
            raise RuntimeError(
                f"Failed OAuth login, response was '{token_response.json()}'. {ex}"
            )
        token_json = token_response.json()
        self.access_token = token_json["access_token"]
        self.refresh_token = token_json["refresh_token"]
        self.expires_in = token_json.get("expires_in", self._default_expiration)
        if self.expires_in is None:
            self.logger.debug(
                "No expires_in receied in OAuth response and no "
                "default_expiration set. Token will be treated as if it never "
                "expires."
            )
        self.last_refreshed = request_time
