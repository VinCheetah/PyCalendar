"""
Client HTTP bas-niveau pour MySportU.

Gère l'authentification (CSRF + session cookies), le rate limiting,
les retries et la gestion d'erreurs.
"""

from __future__ import annotations

import time
import logging
from typing import Any

import requests
from bs4 import BeautifulSoup

from .config import MySportUConfig
from .exceptions import AuthenticationError, APIError, RateLimitError

logger = logging.getLogger(__name__)


class MySportUClient:
    """
    Client HTTP pour l'API MySportU.

    Gère :
    - Authentification via formulaire avec CSRF token
    - Session persistante avec cookies
    - Rate limiting configurable
    - Retries automatiques avec backoff
    - Headers JSON/XHR pour les appels API
    """

    def __init__(self, config: MySportUConfig):
        self.config = config
        self._session = requests.Session()
        self._logged_in = False
        self._last_request_time: float = 0

    # ── Propriétés ──────────────────────────────────────────────────────

    @property
    def is_logged_in(self) -> bool:
        return self._logged_in

    @property
    def base_url(self) -> str:
        return self.config.auth.base_url

    # ── Authentification ────────────────────────────────────────────────

    def login(self) -> None:
        """
        Connexion à MySportU via formulaire avec CSRF.

        Raises:
            AuthenticationError: Si les identifiants manquent ou sont incorrects.
        """
        if self._logged_in:
            return

        # Validation des identifiants
        if not self.config.has_credentials:
            raise AuthenticationError(
                "Identifiants MySportU non configurés.\n"
                "Options :\n"
                "  1. Variables d'env : MYSPORTU_USERNAME / MYSPORTU_PASSWORD\n"
                "  2. Fichier configs/default.yaml → mysportu.auth.username / password\n"
                "  3. Arguments CLI : --username / --password"
            )

        login_url = self.config.auth.login_url
        logger.debug("Tentative de connexion à %s (user=%s)",
                      login_url, self.config.auth.username)

        # 1. Récupérer le token CSRF
        try:
            resp = self._session.get(login_url, timeout=self.config.requests.timeout)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise AuthenticationError(
                f"Impossible d'accéder à la page de login: {e}\n"
                f"URL : {login_url}"
            ) from e

        soup = BeautifulSoup(resp.text, "html.parser")
        csrf_input = soup.find("input", {"name": "_token"})
        if not csrf_input:
            raise AuthenticationError(
                "Token CSRF introuvable sur la page de login.\n"
                f"URL : {login_url}\n"
                "Le site MySportU est peut-être indisponible ou la page de login a changé."
            )

        csrf_token = csrf_input.get("value", "")

        # 2. Soumettre le formulaire
        login_data = {
            "_token": csrf_token,
            "username": self.config.auth.username,
            "password": self.config.auth.password,
        }

        try:
            resp = self._session.post(
                login_url, data=login_data,
                headers={"Referer": login_url},
                allow_redirects=True,
                timeout=self.config.requests.timeout,
            )
        except requests.RequestException as e:
            raise AuthenticationError(f"Erreur lors de la soumission du login: {e}") from e

        # 3. Vérifier la connexion via les cookies de session
        session_cookies = [
            name for name in self._session.cookies.keys()
            if "session" in name.lower() or "ffsu" in name.lower()
        ]

        if not session_cookies:
            # Diagnostic : redirection vers login = mauvais identifiants
            if "/auth/login" in resp.url or resp.status_code == 422:
                raise AuthenticationError(
                    f"Identifiants incorrects (user: {self.config.auth.username}).\n"
                    "Vérifiez username/password dans votre configuration."
                )
            raise AuthenticationError(
                "Connexion échouée : cookie de session absent.\n"
                f"URL finale : {resp.url}\n"
                f"Status : {resp.status_code}\n"
                f"Cookies reçus : {list(self._session.cookies.keys())}"
            )

        self._logged_in = True
        logger.info("Connexion réussie à MySportU (cookies: %s)", session_cookies)

    def logout(self) -> None:
        """Ferme la session."""
        self._session.cookies.clear()
        self._logged_in = False

    def ensure_logged_in(self) -> None:
        """Garantit que la session est active, tente une reconnexion sinon."""
        if not self._logged_in:
            self.login()

    # ── Requêtes HTTP ───────────────────────────────────────────────────

    def get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """
        GET JSON sur l'API MySportU.

        Args:
            path: Chemin relatif (ex: "/feuille-de-match/rencontres")
            params: Paramètres GET optionnels

        Returns:
            Réponse JSON désérialisée

        Raises:
            APIError: Si la requête échoue
            AuthenticationError: Si la session a expiré
        """
        self.ensure_logged_in()
        url = f"{self.base_url}{path}"

        for attempt in range(1, self.config.requests.max_retries + 1):
            self._rate_limit()

            try:
                resp = self._session.get(
                    url,
                    params=params,
                    headers={
                        "Accept": "application/json",
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    timeout=self.config.requests.timeout,
                )
            except requests.RequestException as e:
                if attempt == self.config.requests.max_retries:
                    raise APIError(f"Requête échouée après {attempt} tentatives: {e}",
                                   url=url) from e
                logger.warning("Tentative %d/%d échouée: %s", attempt,
                               self.config.requests.max_retries, e)
                time.sleep(self.config.requests.retry_delay * attempt)
                continue

            if resp.status_code == 401:
                # Session expirée, tenter une reconnexion
                self._logged_in = False
                self.login()
                continue

            if resp.status_code == 429:
                raise RateLimitError("Trop de requêtes", status_code=429, url=url)

            if resp.status_code != 200:
                raise APIError(
                    f"Réponse inattendue",
                    status_code=resp.status_code,
                    url=url,
                )

            try:
                return resp.json()
            except ValueError as e:
                raise APIError(f"Réponse non-JSON: {resp.text[:200]}", url=url) from e

        raise APIError(f"Requête échouée après {self.config.requests.max_retries} tentatives",
                       url=url)

    def get_html(self, path: str) -> str:
        """GET HTML (pour scraping de pages non-API)."""
        self.ensure_logged_in()
        url = f"{self.base_url}{path}"
        self._rate_limit()

        resp = self._session.get(url, timeout=self.config.requests.timeout)
        if resp.status_code != 200:
            raise APIError("Impossible de charger la page", status_code=resp.status_code, url=url)
        return resp.text

    # ── Helpers privés ──────────────────────────────────────────────────

    def _rate_limit(self) -> None:
        """Respecte le délai minimum entre les requêtes."""
        now = time.monotonic()
        elapsed = now - self._last_request_time
        delay = self.config.requests.delay_between_requests
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self._last_request_time = time.monotonic()

    def __enter__(self) -> "MySportUClient":
        self.login()
        return self

    def __exit__(self, *_: Any) -> None:
        self.logout()
