"""Testing module for the assetfeedback app."""

import csv
from datetime import timedelta
from io import StringIO
from pathlib import Path
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import CommandError, call_command
from django.template.loader import render_to_string
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone

from assetfeedback import views
from assetfeedback.models import AssetFeedback

ASSET = 3543155705
URL = f"/asset-feedback/{ASSET}/"
ADDRESS = "VW55KZ3NF4GDOWI7IPWLGZDFWNXWKSRD5PETRLDABZVU5XPKRJJRK3CBSU"
APP_AGENT = "Mozilla/5.0 ASAStatsApp/1.1.0 (ios)"
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clean_cache():
    cache.clear()
    yield
    cache.clear()


def _token(asset_id=ASSET, age=10):
    with mock.patch("django.core.signing.time.time", return_value=_now() - age):
        return views._signer.sign(str(asset_id))


def _now():
    return timezone.now().timestamp()


def _post(client=None, url=URL, **fields):
    data = {"kind": "market", "details": "Sold on X", "started": _token(), **fields}
    return (client or Client()).post(url, data)


class TestAssetFeedbackGet:
    def test_url_name(self):
        assert reverse("asset_feedback", args=[ASSET]) == URL

    def test_fragment_is_never_cached_and_opens_by_id(self):
        response = Client().get(URL)
        assert response.status_code == 200
        assert "no-store" in response["Cache-Control"]
        assert 'id="id-asset-feedback-dialog"' in response.content.decode()

    def test_name_is_escaped_and_truncated(self):
        html = Client().get(URL, {"name": "<script>x" + "a" * 100}).content.decode()
        assert "<script>x" not in html
        assert "a" * 65 not in html

    def test_browser_sees_personal_fields_and_rewards(self):
        html = Client().get(URL).content.decode()
        assert 'name="contact"' in html
        assert 'name="reporter_address"' in html
        assert "community rewards" in html

    def test_app_does_not_see_personal_fields_or_rewards(self):
        html = Client(headers={"user-agent": APP_AGENT}).get(URL).content.decode()
        assert 'name="contact"' not in html
        assert 'name="reporter_address"' not in html
        assert "rewards" not in html

    def test_asset_id_beyond_the_database_range_is_404(self):
        assert Client().get(f"/asset-feedback/{2**63}/").status_code == 404

    def test_browser_links_the_website_privacy_policy(self):
        html = Client().get(URL).content.decode()
        assert "/auth_privacy.html#asset-reports" in html
        assert "asm-privacy" not in html


class TestAssetFeedbackPost:
    def test_post_for_asset_id_beyond_the_database_range_is_404(self):
        assert _post(url=f"/asset-feedback/{2**63}/").status_code == 404

    def test_valid_report_is_stored_without_ip(self):
        html = _post(link="https://market.example/x", reporter_address=ADDRESS).content
        report = AssetFeedback.objects.get()
        assert b"Thank you" in html
        assert report.asset_id == ASSET
        assert report.source == "web"
        assert report.status == "new"
        assert report.reporter_address == ADDRESS
        assert not any("ip" in field.name for field in AssetFeedback._meta.fields)

    def test_details_or_link_is_required(self):
        response = _post(details="")
        assert b"Add some details or a link" in response.content
        assert not AssetFeedback.objects.exists()

    def test_link_alone_is_enough(self):
        _post(details="", link="https://market.example/x")
        assert AssetFeedback.objects.count() == 1

    @pytest.mark.parametrize("link", ["javascript:alert(1)", "ftp://example.com/x"])
    def test_link_scheme_is_refused(self, link):
        _post(details="", link=link)
        assert not AssetFeedback.objects.exists()

    def test_invalid_address_is_refused(self):
        assert b"valid Algorand address" in _post(reporter_address="NOPE").content
        assert not AssetFeedback.objects.exists()

    def test_details_length_is_limited(self):
        _post(details="x" * 1001)
        assert not AssetFeedback.objects.exists()

    def test_honeypot_thanks_and_stores_nothing(self):
        assert b"Thank you" in _post(website="http://spam").content
        assert not AssetFeedback.objects.exists()

    def test_too_fast_is_refused(self):
        response = _post(started=_token(age=0))
        assert b"very quick" in response.content
        assert not AssetFeedback.objects.exists()

    def test_expired_form_gets_a_fresh_token(self):
        response = _post(started=_token(age=7 * 3600))
        assert b"expired" in response.content
        assert not AssetFeedback.objects.exists()

    def test_token_for_another_asset_is_refused(self):
        assert b"expired" in _post(started=_token(asset_id=5)).content
        assert not AssetFeedback.objects.exists()

    def test_forged_token_is_refused(self):
        assert b"expired" in _post(started="1:forged:x").content
        assert not AssetFeedback.objects.exists()

    def test_repeat_for_same_asset_thanks_and_stores_once(self):
        _post()
        assert b"Thank you" in _post().content
        assert AssetFeedback.objects.count() == 1

    def test_app_report_is_marked_and_ignores_personal_fields(self):
        client = Client(headers={"user-agent": APP_AGENT})
        _post(client, contact="me@example.com", reporter_address=ADDRESS)
        report = AssetFeedback.objects.get()
        assert report.source == "app"
        assert report.contact == ""
        assert report.reporter_address == ""

    def test_csrf_is_enforced(self):
        client = Client(enforce_csrf_checks=True)
        assert _post(client).status_code == 403

    def _fill_limit(self, count):
        for asset_id in range(1, count + 1):
            _post(url=f"/asset-feedback/{asset_id}/", started=_token(asset_id=asset_id))

    def test_anonymous_limit_requires_captcha(self):
        self._fill_limit(views.ANONYMOUS_HOURLY_LIMIT)
        response = _post()
        assert b'name="captcha_1"' in response.content
        assert AssetFeedback.objects.filter(asset_id=ASSET).count() == 0

    def test_limit_keys_on_nginx_header_not_forwarded_for(self):
        for forwarded in range(views.ANONYMOUS_HOURLY_LIMIT + 1):
            with override_settings(ALLAUTH_TRUSTED_CLIENT_IP_HEADER="X-Real-IP"):
                client = Client(
                    headers={
                        "x-real-ip": "1.2.3.4",
                        "x-forwarded-for": f"9.9.9.{forwarded}",
                    }
                )
                response = _post(
                    client,
                    url=f"/asset-feedback/{forwarded + 1}/",
                    started=_token(asset_id=forwarded + 1),
                )
        assert b'name="captcha_1"' in response.content

    def test_signed_in_user_gets_higher_limit_and_no_captcha(self):
        user = get_user_model().objects.create_user("reader", password="x")
        client = Client()
        client.force_login(user)
        for asset_id in range(1, views.USER_HOURLY_LIMIT + 1):
            _post(
                client,
                url=f"/asset-feedback/{asset_id}/",
                started=_token(asset_id=asset_id),
            )
        assert AssetFeedback.objects.filter(user=user).count() == views.USER_HOURLY_LIMIT
        response = _post(client)
        assert b"a lot of reports" in response.content
        assert b"captcha_1" not in response.content


class TestAssetFeedbackPrivacy:
    def test_website_policy_describes_reports_and_app_policy_does_not(self):
        root = Path(__file__).resolve().parents[2]
        website = (root / "static/auth_privacy.html").read_text()
        app = (root / "templates/asm-privacy.html").read_text()
        assert 'id="asset-reports"' in website
        assert "12 months" in website
        assert "asset report" not in app

    def test_account_deletion_clears_contact_and_address(self):
        user = get_user_model().objects.create_user("reader", password="x")
        report = AssetFeedback.objects.create(
            asset_id=1,
            kind="other",
            details="x",
            contact="c",
            reporter_address=ADDRESS,
            user=user,
        )
        user.delete()
        report.refresh_from_db()
        assert (report.user, report.contact, report.reporter_address) == (None, "", "")

    def test_purge_clears_only_old_contacts(self):
        old = AssetFeedback.objects.create(asset_id=1, kind="other", contact="c")
        new = AssetFeedback.objects.create(asset_id=2, kind="other", contact="c")
        AssetFeedback.objects.filter(pk=old.pk).update(
            created=timezone.now() - timedelta(days=366)
        )
        call_command("assetfeedbackpurge", stdout=StringIO())
        old.refresh_from_db()
        new.refresh_from_db()
        assert (old.contact, new.contact) == ("", "c")


class TestAssetFeedbackModel:
    def test_str_names_asset_kind_and_status(self):
        report = AssetFeedback(asset_id=7, kind="other", status="new")
        assert str(report) == "7 other new"


class TestAssetFeedbackCommands:
    def test_export_groups_new_reports_and_escapes_formulas(self):
        AssetFeedback.objects.create(asset_id=1, kind="other", details="=HYPERLINK(1)")
        AssetFeedback.objects.create(asset_id=2, kind="other", details="a")
        AssetFeedback.objects.create(asset_id=2, kind="other", details="b")
        AssetFeedback.objects.create(asset_id=3, kind="other", status="rejected")
        out = StringIO()
        call_command("assetfeedbackexport", stdout=out)
        rows = list(csv.DictReader(StringIO(out.getvalue())))
        assert [row["asset_id"] for row in rows] == ["2", "2", "1"]
        assert rows[0]["reports_for_asset"] == "2"
        assert rows[2]["details"] == "'=HYPERLINK(1)"

    def test_export_no_contact_leaves_out_only_the_contact(self):
        AssetFeedback.objects.create(
            asset_id=1,
            kind="other",
            details="d",
            contact="me@example.com",
            reporter_address=ADDRESS,
        )
        out = StringIO()
        call_command("assetfeedbackexport", "--no-contact", stdout=out)
        assert "me@example.com" not in out.getvalue()
        row = next(csv.DictReader(StringIO(out.getvalue())))
        assert "contact" not in row
        assert (row["details"], row["reporter_address"]) == ("d", ADDRESS)

    def test_export_keeps_the_contact_by_default(self):
        AssetFeedback.objects.create(asset_id=1, kind="other", contact="me@example.com")
        out = StringIO()
        call_command("assetfeedbackexport", stdout=out)
        assert (
            next(csv.DictReader(StringIO(out.getvalue())))["contact"] == "me@example.com"
        )

    @pytest.mark.parametrize("args", [(), ("--rewards",)])
    def test_export_is_silent_without_rows(self, args):
        AssetFeedback.objects.create(asset_id=3, kind="other", status="rejected")
        out = StringIO()
        call_command("assetfeedbackexport", *args, stdout=out)
        assert out.getvalue() == ""

    def test_export_rewards_is_first_accepted_with_address_per_asset(self):
        first = AssetFeedback.objects.create(
            asset_id=1, kind="other", status="accepted", reporter_address=ADDRESS
        )
        AssetFeedback.objects.create(
            asset_id=1, kind="other", status="accepted", reporter_address=ADDRESS
        )
        AssetFeedback.objects.create(asset_id=2, kind="other", status="accepted")
        out = StringIO()
        call_command("assetfeedbackexport", "--rewards", stdout=out)
        rows = list(csv.DictReader(StringIO(out.getvalue())))
        assert [row["id"] for row in rows] == [str(first.pk)]

    def test_resolve_sets_status_and_clears_contact(self):
        report = AssetFeedback.objects.create(asset_id=1, kind="other", contact="c")
        call_command(
            "assetfeedbackresolve", report.pk, "accepted", note="ok", stdout=StringIO()
        )
        report.refresh_from_db()
        assert (report.status, report.reviewer_note, report.contact) == (
            "accepted",
            "ok",
            "",
        )

    def test_resolve_unknown_report_raises(self):
        with pytest.raises(CommandError):
            call_command("assetfeedbackresolve", 999, "accepted", stdout=StringIO())


class TestNonvalButton:
    def _html(self, asset):
        return render_to_string(
            "snippets/nonval.html",
            {"notevals": [{"asset": asset, "amount": 1, "programs": []}]},
        )

    def test_button_targets_slot_outside_details(self):
        html = self._html({"id": ASSET, "name": "A & B", "decimals": 0})
        assert f'hx-get="/asset-feedback/{ASSET}/?name=A%20%26%20B"' in html
        assert html.index("</details>") < html.index('id="id-asset-feedback-slot"')

    def test_null_asset_with_engine_id_gets_a_button(self):
        html = render_to_string(
            "snippets/nonval.html",
            {"notevals": [{"id": ASSET, "asset": None, "amount": 1, "programs": []}]},
        )
        assert f'hx-get="/asset-feedback/{ASSET}/' in html

    @pytest.mark.parametrize("reason", ["curated:suspicious", "pera:suspicious"])
    def test_label_is_escaped_and_changes_button_and_link_title(self, reason):
        html = render_to_string(
            "snippets/nonval.html",
            {
                "notevals": [
                    {
                        "id": ASSET,
                        "asset": {
                            "id": ASSET,
                            "name": "A",
                            "decimals": 0,
                            "url": "https://x.example",
                        },
                        "amount": 1,
                        "programs": [],
                        "reason": reason,
                        "note": "Reported <b>as suspicious",
                    }
                ]
            },
        )
        assert "Reported &lt;b&gt;as suspicious" in html
        assert "Suggest a correction" in html
        assert "Official URL" not in html
        assert "nofollow" in html

    def test_no_label_keeps_the_default_button(self):
        html = self._html(
            {"id": ASSET, "name": "A", "decimals": 0, "url": "https://x.example"}
        )
        assert "asset-note" not in html
        assert "Help evaluate this asset" in html
        assert "Official URL" in html

    def test_null_asset_has_no_button_and_does_not_raise(self):
        html = self._html(None)
        assert "hx-get" not in html
