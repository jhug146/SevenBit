from __future__ import annotations

import threading
import time

import requests

TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
SCOPE = "https://api.ebay.com/oauth/api_scope/sell.inventory"
EXPIRY_BUFFER_SECONDS = 60


class EbayOAuth:
    """Exchanges the account's stored refresh token for a short-lived user access
    token needed by eBay's REST APIs (e.g. the Media API), caching it until shortly
    before it expires. Unlike the Trading API's Auth'n'Auth token, REST APIs require
    a real OAuth user access token obtained via the authorization code grant; the
    refresh token that grant produces is what accounts.refresh_token holds.
    """

    def __init__(self, accounts):
        self.accounts = accounts
        self._lock = threading.Lock()
        self._access_token = None
        self._expires_at = 0
        self._cached_refresh_token = None

    def get_access_token(self) -> str:
        refresh_token = self.accounts.refresh_token
        if not refresh_token:
            raise RuntimeError(
                "No eBay OAuth refresh token configured for this account. "
                "Generate one (scope sell.inventory) via the eBay Developer Portal's "
                "User Tokens tool and add it as credentials.refresh_token in accounts.json."
            )

        with self._lock:
            if (
                self._access_token
                and refresh_token == self._cached_refresh_token
                and time.time() < self._expires_at
            ):
                return self._access_token

            response = requests.post(
                TOKEN_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "scope": SCOPE,
                },
                auth=(self.accounts.appid, self.accounts.certid),
            )
            body = response.json()
            if "access_token" not in body:
                raise RuntimeError(f"Failed to refresh eBay OAuth token: {body}")

            self._access_token = body["access_token"]
            self._expires_at = time.time() + body["expires_in"] - EXPIRY_BUFFER_SECONDS
            self._cached_refresh_token = refresh_token
            return self._access_token
