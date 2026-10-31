"""The site's allauth login form (``ACCOUNT_FORMS["login"]``)."""

from allauth.account.forms import LoginForm

from core.appclient import app_client


class AppAwareLoginForm(LoginForm):
    """Allauth's login form; in the app the session is always remembered.

    A session cookie dies with the WebView when Android kills the app.
    """

    def clean(self):
        """Force ``remember`` for requests from the app.

        :return: dict
        """
        cleaned_data = super().clean()
        if app_client(self.request) is not None:
            self.cleaned_data["remember"] = True
        return cleaned_data
