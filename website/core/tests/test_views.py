"""Testing module for :py:mod:`website.core.views` module."""

import re
from unittest import mock

from allauth.account.forms import LoginForm
from captcha.models import CaptchaStore
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import gettext_lazy

from core.forms import (
    AddressForm,
    CustomSignupForm,
    DeactivateProfileForm,
    ProfileBundleNameForm,
    ProfileFormSet,
    ProfileLiveRefreshForm,
    UpdateUserForm,
)
from core.models import BundleName, Profile
from utils.constants.core import INVALID_ADDRESS_TEXT

from . import dom
from utils.constants.users import (
    DUPLICATE_BUNDLE_ERROR,
    REQUIRED_BUNDLE_NAME_ERROR,
    SUBSCRIPTION_TIER_PERMISSIONS,
    TOO_LONG_USER_FIRST_NAME_ERROR,
    TOO_LONG_USER_LAST_NAME_ERROR,
)
from utils.tests.fixtures import TEST_ADDRESS, TEST_ADDRESS2, TEST_ADDRESS3

user_model = get_user_model()


# # HELPERS
def get_user_edit_fake_post_data(user, first_name="first_name", last_name="last_name"):
    return {
        "first_name": first_name,
        "last_name": last_name,
        "csrfmiddlewaretoken": "ebklx66wgoqT9kReeo67yxdCyzG2EtoBIRDvGjShzWfvbAnOhsdC4dok2vNta0PQ",
        "profile-TOTAL_FORMS": 1,
        "profile-INITIAL_FORMS": 1,
        "profile-MIN_NUM_FORMS": 0,
        "profile-MAX_NUM_FORMS": 1,
        "profile-0-address": "",
        "profile-0-authorized": False,
        "profile-0-permission": 0,
        "profile-0-currency": "ALGO",
        "profile-0-id": user.profile.id,
        "profile-0-user": user.id,
        "_mutable": False,
    }


def get_bundlename_fake_post_data(user, first_name="first_name", last_name="last_name"):
    return {
        "first_name": first_name,
        "last_name": last_name,
        "csrfmiddlewaretoken": "ebklx66wgoqT9kReeo67yxdCyzG2EtoBIRDvGjShzWfvbAnOhsdC4dok2vNta0PQ",
        "profile-TOTAL_FORMS": 1,
        "profile-INITIAL_FORMS": 1,
        "profile-MIN_NUM_FORMS": 0,
        "profile-MAX_NUM_FORMS": 1,
        "profile-0-address": "",
        "profile-0-authorized": False,
        "profile-0-permission": 0,
        "profile-0-currency": "ALGO",
        "profile-0-id": user.profile.id,
        "bundlename-0-profile": user.profile.id,
        "_mutable": False,
    }


class FilesViewTest(TestCase):
    # # assets_file
    def test_assets_file_returns_svg_content_type_for_svg(self):
        response = self.client.get(reverse("assets_file", args=["logo.svg"]))
        self.assertIn("image/svg+xml", response._content_type_for_repr)

    def test_assets_file_returns_png_content_type_for_png(self):
        response = self.client.get(reverse("assets_file", args=["logo.png"]))
        self.assertIn("image/png", response._content_type_for_repr)

    def test_assets_file_returns_pdf_content_type_for_pdf(self):
        response = self.client.get(reverse("assets_file", args=["whitepaper.pdf"]))
        self.assertIn("application/pdf", response._content_type_for_repr)

    def test_assets_file_raises_404_for_no_file_found(self):
        response = self.client.get(
            reverse("assets_file", args=["transparency-report-2021-09.pdf"])
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.reason_phrase, "Not Found")

    # # index_file
    def test_index_file_returns_txt_content_type_for_robots_file(self):
        response = self.client.get(reverse("index_file", args=["robots.txt"]))
        self.assertIn("text/plain", response._content_type_for_repr)

    def test_index_file_returns_txt_content_type_for_google_ownership_f(self):
        response = self.client.get(
            reverse("index_file", args=[settings.GOOGLE_OWNERSHIP_FILE])
        )
        self.assertIn("text/plain", response._content_type_for_repr)

    # # service_worker
    def test_service_worker_is_served_as_javascript(self):
        """It is a script, and a browser will refuse to register one served as
        anything else."""
        response = self.client.get(reverse("alerts_service_worker"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/javascript", response._content_type_for_repr)

    def test_service_worker_handles_a_push(self):
        """**The only thing it has to do.** A worker that registers and ignores
        `push` is indistinguishable, from the outside, from one that never
        registered - and nothing reports either."""
        response = self.client.get(reverse("alerts_service_worker"))
        body = response.content.decode()

        self.assertIn('addEventListener("push"', body)
        self.assertIn("showNotification", body)

    def test_service_worker_is_served_from_the_site_root(self):
        """**Scope is the path it is served from.** Under /static/ it would
        register cleanly and receive nothing for the site, which is why this is
        a view beside `index_file` rather than a static file."""
        url = reverse("alerts_service_worker")

        self.assertEqual(url, "/alerts-service-worker.js")
        self.assertNotIn("/static/", url)

    # # social_icons
    def test_social_icons_view_returns_png_content_type_for_png(self):
        response = self.client.get(reverse("social_icons", args=["twitter24.png"]))
        self.assertIn("image/png", response._content_type_for_repr)


class IndexPageTest(TestCase):
    def post_invalid_input(self):
        return self.client.post(reverse("index"), data={"address": "foobar"})

    def test_index_page_renders_index_template(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")

    def test_index_page_jsonld_script_haspart_elements(self):
        response = self.client.get(reverse("index"))
        for part in (
            "about",
            "tokenomics",
            "faq",
            "disclaimer",
            "asm-privacy",
            "features",
            "subscriptions",
        ):
            self.assertContains(
                response, '"url":"{}/{}/"'.format(settings.WEBSITE_URL, part)
            )

    def test_index_page_jsonld_script_type_organization_element(self):
        response = self.client.get(reverse("index"))
        self.assertContains(response, '"@type":"Organization"')

    def test_index_page_jsonld_script_type_website_element(self):
        response = self.client.get(reverse("index"))
        self.assertContains(response, '"@type":"WebSite"')

    def test_index_page_for_invalid_input_renders_index_template(self):
        response = self.post_invalid_input()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")

    def test_index_page_for_invalid_input_passes_form_to_template(self):
        response = self.post_invalid_input()
        self.assertIsInstance(response.context["form"], AddressForm)

    def test_index_page_for_invalid_input_shows_errors_on_page(self):
        response = self.post_invalid_input()
        self.assertContains(response, escape(INVALID_ADDRESS_TEXT))

    def test_index_page_for_invalid_bundle_input_shows_errors_on_page(self):
        response = self.client.post(reverse("index"), data={"bundle": "foobar"})
        self.assertContains(response, escape(INVALID_ADDRESS_TEXT))

    def test_index_page_post_ends_in_address_page(self):
        response = self.client.post(
            reverse("index"),
            data={"address": TEST_ADDRESS},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRegex(response.url, TEST_ADDRESS)

    def test_index_page_bundle_post_ends_in_address_page(self):
        test_address2 = "A" + TEST_ADDRESS[1:]
        bundle = f"{TEST_ADDRESS} {test_address2}"
        response = self.client.post(
            reverse("index"),
            data={"bundle": bundle},
        )
        self.assertEqual(response.status_code, 302)
        # TODO check this
        # self.assertRegex(response.url, create_bundle(bundle))

    def test_index_page_links_to_about_page(self):
        response = self.client.get(reverse("index"))
        self.assertContains(response, 'href="{}"'.format(reverse("about")))

    def test_index_page_links_to_twitter_page(self):
        response = self.client.get(reverse("index"))
        self.assertContains(
            response, 'href="https://x.com/{}"'.format(settings.X_HANDLE)
        )

    def test_index_page_links_to_reddit_page(self):
        response = self.client.get(reverse("index"))
        self.assertContains(
            response,
            'href="https://www.reddit.com/r/{}"'.format(settings.SUBREDDIT_NAME),
        )

    def test_index_page_links_to_discord_invite(self):
        response = self.client.get(reverse("index"))
        self.assertContains(
            response, 'href="https://discord.gg/{}"'.format(settings.DISCORD_INVITE)
        )


class AboutPageTest(TestCase):
    def test_about_page_renders_about_template(self):
        response = self.client.get("/about/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "about.html")

    def test_about_page_links_to_roadmap(self):
        response = self.client.get(reverse("about"))
        self.assertContains(
            response, "https://github.com/asastats/docs/blob/main/roadmap.md"
        )


class FaqPageTest(TestCase):
    def test_faq_page_renders_faq_template(self):
        response = self.client.get("/faq/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "faq.html")


class DisclaimerPageTest(TestCase):
    def test_disclaimer_page_renders_disclaimer_of_use_template(self):
        response = self.client.get("/disclaimer/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "disclaimer.html")


class FeaturesPageTest(TestCase):
    def test_features_page_renders_features_template(self):
        response = self.client.get("/features/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "features.html")


class SubscriptionsPageTest(TestCase):
    def test_subscriptions_page_renders_subscriptions_template(self):
        response = self.client.get("/subscriptions/")

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "subscriptions.html")


class TaxDownloadViewTest(TestCase):
    # # export_download
    def test_export_download_raises_404_for_no_report_in_request(self):
        response = self.client.get(reverse("export_download"))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.reason_phrase, "Not Found")

    def test_export_download_redirects_for_wrong_report(self):
        response = self.client.get("/export/download?report=foo_bar")
        self.assertEqual(response.status_code, 301)


class HomePageTest(TestCase):
    def setUp(self):
        self.user = user_model.objects.create(
            email="testprofile@testprofile.com",
            username="testprofile",
        )
        self.user.set_password("12345o")
        self.user.save()
        with mock.patch("core.models.get_permission_provider") as mocked_provider:
            mocked_provider.return_value.votes_and_permission.return_value = [0, 0]
            self.client.login(username="testprofile", password="12345o")

    def test_home_page_uses_home_template(self):
        response = self.client.get(reverse("home"))
        self.assertTemplateUsed(response, "home.html")

    def test_home_page_passes_correct_profile_to_template(self):
        profile = Profile.objects.create()
        response = self.client.get(reverse("home"))
        self.assertNotEqual(response.context["profile"], profile)

    def test_home_page_displays_button_with_link_to_add_bundlename(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("bundlename_add"))

    def test_home_page_displays_button_with_link_to_edit_profile(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("profile"))

    def test_home_page_displays_only_bundlenames_for_that_profile(self):
        BundleName.objects.create(
            name="name-1", addresses=TEST_ADDRESS, profile=self.user.profile
        )
        BundleName.objects.create(
            name="name-2", addresses=TEST_ADDRESS2, profile=self.user.profile
        )
        other_profile = Profile.objects.create()
        BundleName.objects.create(
            name="name-3", addresses=TEST_ADDRESS3, profile=other_profile
        )
        BundleName.objects.create(
            name="name-4", addresses=TEST_ADDRESS, profile=other_profile
        )

        response = self.client.get(reverse("home"))

        self.assertContains(response, "name-1")
        self.assertContains(response, "name-2")
        self.assertNotContains(response, "name-3")
        self.assertNotContains(response, "name-4")

    def test_home_page_links_to_bundlename_edit_page(self):
        bundlename = BundleName.objects.create(
            name="name-1", addresses=TEST_ADDRESS3, profile=self.user.profile
        )
        response = self.client.get(reverse("home"))
        self.assertContains(
            response, reverse("bundlename_edit", args=[bundlename.name])
        )


class HomeProfileLinkTest(TestCase):
    """What the link to the profile page calls the reader.

    It used to be the email and nothing else, which was wrong in two
    directions: a reader who had set a name was still addressed by their email
    address, and an account with no email -- a wallet sign-in never asks for
    one -- got a link with no text in it at all, which is a link a keyboard can
    focus and a screen reader cannot announce.

    `profile.name` is the existing answer to "what do we call this reader"
    (first and last name if either is set, else the username, else the local
    part of the email), so the link leads with that. The email follows it only
    when there is one and it is not already what was just said -- otherwise the
    common case, an account whose username *is* its email, printed the same
    string twice side by side.

    All three cases are here rather than in a functional test because they are
    about which of several fields is rendered, which the markup answers
    exactly; the functional suite holds the one assertion the markup cannot
    make, that the reader is named once on the whole page.
    """

    def _sign_in(self, **fields):
        """Create and sign in a reader with the given user fields."""
        user = user_model.objects.create(username="linktest", **fields)
        user.set_password("12345o")
        user.save()
        with mock.patch("core.models.get_permission_provider") as mocked_provider:
            mocked_provider.return_value.votes_and_permission.return_value = [0, 0]
            self.client.login(username="linktest", password="12345o")
        return user

    def _node(self, response):
        """Return the profile link, requiring there to be exactly one."""
        found = dom.parse(response.content.decode()).by_id("id_profile")
        self.assertEqual(1, len(found), "the home page has no one link to the profile")
        return found[0]

    #: The affordance at the end of the chip. Stripped by `_link` so the tests
    #: below keep asserting on the one thing they are about - which of the
    #: reader's fields is rendered, and in what order - rather than being
    #: rewritten every time the label is reworded.
    AFFORDANCE = "Open profile \u2192"

    def _link(self, response):
        """Return how the link names the reader, whitespace collapsed.

        The trailing affordance is removed: it is the same on every account and
        is pinned once, by `test_the_link_says_where_it_goes`.
        """
        return self._link_text(self._node(response))

    def _link_text(self, node):
        """How `node` names the reader, affordance removed."""
        text = " ".join(node.text().split())
        return text.removesuffix(self.AFFORDANCE).strip()

    def test_the_link_says_where_it_goes(self):
        """**It was grey text that did not look like anything.** A name and an
        email in the page's own muted colour, underlined only on hover: nothing
        said it was a link, and the profile page is where the subscription
        address is authorised."""
        self._sign_in(email="named@example.com")

        text = " ".join(self._node(self.client.get(reverse("home"))).text().split())

        assert text.endswith(self.AFFORDANCE)

    def test_the_mark_is_inside_the_one_link_and_hidden_from_readers(self):
        """One tab stop for one destination, and the link already says whose
        account it is - a mark announced beside it would say it twice."""
        self._sign_in(email="named@example.com")
        node = self._node(self.client.get(reverse("home")))

        marks = node.select("svg")

        self.assertEqual(1, len(marks))
        self.assertIn("identicon", marks[0].classes)
        self.assertEqual("true", marks[0].attrs.get("aria-hidden"))

    def test_a_reader_who_set_a_name_is_called_by_it(self):
        """The bug the reader reported: a set name was ignored."""
        user = self._sign_in(
            email="named@example.com", first_name="Ada", last_name="Lovelace"
        )

        text = self._link(self.client.get(reverse("home")))

        self.assertEqual(f"Ada Lovelace {user.email}", text)

    def test_the_email_follows_the_name_rather_than_replacing_it(self):
        """Two facts, one link.

        Split across two anchors they would be two tab stops to one
        destination, so both sit inside the single link. Asserted on the text
        rather than by counting spans: the chip wraps them for layout, and a
        count breaks whenever the wrapper changes while saying nothing about
        what a reader hears.
        """
        self._sign_in(email="named@example.com", first_name="Ada")

        node = self._node(self.client.get(reverse("home")))

        self.assertEqual("a", node.tag)
        self.assertEqual("Ada named@example.com", self._link_text(node))

    def test_an_account_with_no_email_still_has_link_text(self):
        """A wallet sign-in never asks for one.

        Without this the anchor was empty: focusable, announced as nothing, and
        invisible to a reader looking for the way to their profile.
        """
        self._sign_in(email="")

        text = self._link(self.client.get(reverse("home")))

        self.assertEqual("linktest", text)

    def test_an_email_that_is_already_the_name_is_not_repeated(self):
        """The common case: signing up with an email makes it the username.

        `profile.name` falls back to the username, so naming the email again
        after it would print the same string twice, three characters apart.
        """
        user = user_model.objects.create(
            username="same@example.com", email="same@example.com"
        )
        user.set_password("12345o")
        user.save()
        with mock.patch("core.models.get_permission_provider") as mocked_provider:
            mocked_provider.return_value.votes_and_permission.return_value = [0, 0]
            self.client.login(username="same@example.com", password="12345o")

        text = self._link(self.client.get(reverse("home")))

        self.assertEqual("same@example.com", text)


class EditProfilePageTest(TestCase):
    def setUp(self):
        self.user = user_model.objects.create(
            email="profilepage@testuser.com",
            username="profilepage",
        )
        self.user.set_password("12345o")
        self.user.save()
        with mock.patch("core.models.get_permission_provider") as mocked_provider:
            mocked_provider.return_value.votes_and_permission.return_value = [0, 0]
            self.client.login(username="profilepage", password="12345o")

    def post_invalid_input(self):
        return self.client.post(
            reverse("profile"),
            data=get_user_edit_fake_post_data(self.user, first_name="xyz" * 51),
        )

    def test_profile_page_uses_profile_template(self):
        response = self.client.get(reverse("profile"))
        self.assertTemplateUsed(response, "profile.html")

    def test_profile_page_passes_correct_user_to_template(self):
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.context["form"].instance.username, self.user.username)

    def test_profile_page_displays_updateuserform_for_edit_user_data(self):
        response = self.client.get(reverse("profile"))
        self.assertIsInstance(response.context["form"], UpdateUserForm)
        self.assertContains(response, "first_name")

    def test_profile_page_displays_profileformset_for_edit_profile_data(self):
        response = self.client.get(reverse("profile"))
        self.assertIsInstance(response.context["profile_form"], ProfileFormSet)
        self.assertContains(response, "profile-0-address")

    def test_profile_page_post_ends_in_profile_page(self):
        response = self.client.post(
            reverse("profile"), data=get_user_edit_fake_post_data(self.user)
        )
        self.assertRedirects(response, reverse("profile"))

    def test_profile_page_saving_a_post_request_to_an_existing_user(self):
        self.client.post(
            reverse("profile"),
            data=get_user_edit_fake_post_data(
                self.user, first_name="Newname", last_name="Newlastname"
            ),
        )
        user = user_model.objects.last()
        self.assertEqual(user.first_name, "Newname")
        self.assertEqual(user.last_name, "Newlastname")

    def test_profile_page_for_too_long_first_name_shows_errors_on_page(self):
        response = self.client.post(
            reverse("profile"),
            data=get_user_edit_fake_post_data(self.user, first_name="xyz" * 51),
        )
        self.assertContains(response, escape(TOO_LONG_USER_FIRST_NAME_ERROR))

    def test_profile_page_for_too_long_lastname_shows_errors_on_page(self):
        response = self.client.post(
            reverse("profile"),
            data=get_user_edit_fake_post_data(self.user, last_name="xyz " * 40),
        )
        self.assertContains(response, escape(TOO_LONG_USER_LAST_NAME_ERROR))

    def test_profile_page_edit_profile_for_invalid_input_nothing_saved_to_db(self):
        oldname = self.user.first_name
        self.post_invalid_input()
        self.assertEqual(oldname, self.user.first_name)

    def test_profile_page_for_invalid_input_renders_profile_template(self):
        response = self.post_invalid_input()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "profile.html")

    def test_profile_page_edit_profile_for_invalid_input_passes_form_to_template(self):
        response = self.post_invalid_input()
        self.assertIsInstance(response.context["form"], UpdateUserForm)

    def test_profile_page_edit_profile_links_to_profile_account_page(self):
        response = self.client.get(reverse("profile"))
        self.assertContains(response, reverse("profile_account"))


class ProfileAccountPageTest(TestCase):
    def setUp(self):
        self.user = user_model.objects.create(
            email="profile_account@testuser.com",
            username="profile_account",
        )
        self.user.set_password("12345o")
        self.user.save()
        with mock.patch("core.models.get_permission_provider") as mocked_provider:
            mocked_provider.return_value.votes_and_permission.return_value = [0, 0]
            self.client.login(username="profile_account", password="12345o")

    def test_profile_page_profile_account_uses_profile_account_template(self):
        response = self.client.get(reverse("profile_account"))
        self.assertTemplateUsed(response, "profile_account.html")

    def test_profile_page_profile_account_links_to_deactivate_account_page(self):
        response = self.client.get(reverse("profile_account"))
        self.assertContains(response, reverse("deactivate_profile"))


class DeactivateProfilePageTest(TestCase):
    def setUp(self):
        self.user = user_model.objects.create(
            email="deactivate_profile@testuser.com",
            username="deactivate_profile",
        )
        self.user.set_password("12345o")
        self.user.save()
        with mock.patch("core.models.get_permission_provider") as mocked_provider:
            mocked_provider.return_value.votes_and_permission.return_value = [0, 0]
            self.client.login(username="deactivate_profile", password="12345o")

    def post_invalid_input(self):
        return self.client.post(reverse("deactivate_profile"), data={"captcha": "1234"})

    def test_deactivate_profile_page_uses_deactivate_profile_template(self):
        response = self.client.get(reverse("deactivate_profile"))
        self.assertTemplateUsed(response, "deactivate_profile.html")

    def test_deactivate_profile_page_deactivate_uses_deactivateprofileform_object(self):
        response = self.client.get(reverse("deactivate_profile"))
        self.assertIsInstance(response.context["form"], DeactivateProfileForm)
        self.assertContains(response, "captcha_0")

    def test_deactivate_profile_page_for_invalid_input_nothing_changed_in_db(self):
        is_active = self.user.is_active
        self.post_invalid_input()
        self.assertEqual(is_active, self.user.is_active)

    def test_deactivate_profile_page_deactivate_for_invalid_renders_profile_template(
        self,
    ):
        response = self.post_invalid_input()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "deactivate_profile.html")

    def test_deactivate_profile_page_deactivate_for_invalid_passes_form_to_template(
        self,
    ):
        response = self.post_invalid_input()
        self.assertIsInstance(response.context["form"], DeactivateProfileForm)

    def __extract_hash_and_response(self, r):
        hash_ = re.findall(r'name="captcha_0" value="([0-9a-f]+)"', str(r.content))[0]
        response = CaptchaStore.objects.get(hashkey=hash_).response
        return hash_, response

    def valid_captcha(self):
        r = self.client.get(reverse("deactivate_profile"))
        self.assertEqual(r.status_code, 200)
        hash_, response = self.__extract_hash_and_response(r)
        return self.client.post(
            reverse("deactivate_profile"), dict(captcha_0=hash_, captcha_1=response)
        )

    def test_deactivate_profile_page_deactivate_valid_form_redirects_to_inactive(
        self,
    ):
        # time.sleep(5)
        response = self.valid_captcha()
        self.assertEqual(response.status_code, 302)
        self.assertEqual("/accounts/inactive/", response.url)

    def test_deactivate_profile_page_deactivate_valid_form_calls_deactivate_profile(
        self,
    ):
        # time.sleep(5)
        with mock.patch(
            "core.forms.DeactivateProfileForm.deactivate_profile"
        ) as mock_deactivate:
            self.valid_captcha()
            self.assertNotEqual(mock_deactivate.call_args_list, [])

    def test_deactivate_profile_page_deactivate_invalid_form_submit(self):
        response = self.client.get(reverse("deactivate_profile"))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            reverse("deactivate_profile"),
            dict(captcha_0="abc", captcha_1="wrong response"),
        )
        self.assertFormError(
            response.context_data["form"], "captcha", gettext_lazy("Invalid CAPTCHA")
        )


class BundleNameAddPageTest(TestCase):
    def setUp(self):
        self.user = user_model.objects.create(
            email="testuser@testuser.com",
            username="testuser",
        )
        self.user.set_password("12345o")
        self.user.save()
        self.user.profile.permission = 258_885_438_201
        self.user.profile.save()
        with mock.patch("core.models.get_permission_provider") as mocked_provider:
            mocked_provider.return_value.votes_and_permission.return_value = [
                self.user.profile.votes,
                self.user.profile.permission,
            ]
            self.client.login(username="testuser", password="12345o")

    def post_invalid_input(self):
        return self.client.post(
            reverse("bundlename_add"), data={"name": "", "addresses": TEST_ADDRESS2}
        )

    def test_uses_bundlename_add_bundlename(self):
        response = self.client.get(reverse("bundlename_add"))
        self.assertTemplateUsed(response, "bundlename_add.html")

    def test_passes_correct_profile_to_bundlename(self):
        profile = Profile.objects.create()
        response = self.client.get(reverse("bundlename_add"))
        self.assertNotEqual(response.context["profile"], profile)

    def test_displays_bundlename_name_form_for_bundlename_add(self):
        response = self.client.get(reverse("bundlename_add"))
        self.assertIsInstance(response.context["form"], ProfileBundleNameForm)
        self.assertContains(response, 'name="name"')

    def test_displays_only_bundlenames_for_that_profile(self):
        BundleName.objects.create(
            profile=self.user.profile, name="bundlename-name1", addresses=TEST_ADDRESS
        )
        BundleName.objects.create(
            profile=self.user.profile, name="bundlename-name2", addresses=TEST_ADDRESS2
        )
        other_profile = Profile.objects.create()
        BundleName.objects.create(
            name="bundlename-name3",
            addresses=TEST_ADDRESS3,
            profile=other_profile,
        )
        BundleName.objects.create(
            name="bundlename-name4",
            addresses=TEST_ADDRESS,
            profile=other_profile,
        )
        response = self.client.get(reverse("bundlename_add"))
        self.assertContains(response, "bundlename-name1")
        self.assertContains(response, "bundlename-name2")
        self.assertNotContains(response, "bundlename-name3")
        self.assertNotContains(response, "bundlename-name4")

    def test_bundlename_add_saving_a_post_request_to_an_existing_profile(self):
        self.client.post(
            reverse("bundlename_add"),
            data={"name": "bundlename-name5", "addresses": TEST_ADDRESS3},
        )
        self.assertTrue(
            any(
                bundlename.name == "bundlename-name5"
                and bundlename.profile == self.user.profile
                for bundlename in BundleName.objects.all()
            )
        )
        self.assertTrue(
            any(
                bundlename.addresses == TEST_ADDRESS3
                and bundlename.profile == self.user.profile
                for bundlename in BundleName.objects.all()
            )
        )

    def test_post_ends_in_bundlename_edit_page(self):
        response = self.client.post(
            reverse("bundlename_add"),
            data={"name": "bundlename-name10", "addresses": TEST_ADDRESS3},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRegex(response.url, "/.+")

    def test_adding_bundlename_redirects_to_subscriptions(self):
        BundleName.objects.create(
            name="BundleName namefirst",
            addresses=TEST_ADDRESS2,
            profile=self.user.profile,
        )
        self.user.profile.permission = 0
        self.user.profile.save()
        response = self.client.post(
            reverse("bundlename_add"),
            data={"name": "New bundlename name2", "addresses": TEST_ADDRESS2},
        )
        self.assertEqual(response.status_code, 302)
        self.assertRegex(response.url, "subscriptions")

    def test_bundlename_add_for_invalid_input_nothing_saved_to_db(self):
        count = BundleName.objects.count()
        self.post_invalid_input()
        self.assertEqual(BundleName.objects.count(), count)

    def test_for_invalid_input_renders_bundlename_add_bundlename(self):
        response = self.post_invalid_input()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bundlename_add.html")

    def test_bundlename_add_for_invalid_input_passes_form_to_bundlename(self):
        response = self.post_invalid_input()
        self.assertIsInstance(response.context["form"], ProfileBundleNameForm)

    def test_profiles_for_invalid_input_shows_errors_on_page(self):
        response = self.post_invalid_input()
        self.assertContains(response, escape(REQUIRED_BUNDLE_NAME_ERROR))

    def test_for_too_long_bundlename_name_shows_errors_on_page(self):
        response = self.client.post(
            reverse("bundlename_add"),
            data={"name": "xyz " * 15, "addresses": TEST_ADDRESS3},
        )
        self.assertContains(response, "Ensure this value has at most")

    def test_duplicate_addresses_validation_errors_end_up_on_bundlename_add_page(self):
        BundleName.objects.create(
            name="bundlename-name5",
            addresses=f"{TEST_ADDRESS2} {TEST_ADDRESS3}",
            profile=self.user.profile,
        )
        response = self.client.post(
            reverse("bundlename_add"),
            data={"name": "some name", "addresses": f"{TEST_ADDRESS2} {TEST_ADDRESS3}"},
        )
        expected_error = escape(DUPLICATE_BUNDLE_ERROR)
        self.assertContains(response, expected_error)
        self.assertTemplateUsed(response, "bundlename_add.html")

    def test_bundlename_in_collection_links_to_bundlename_edit_page(self):
        bundlename = BundleName.objects.create(
            name="bundlename-name9",
            addresses=f"{TEST_ADDRESS2} {TEST_ADDRESS3}",
            profile=self.user.profile,
        )
        response = self.client.get(reverse("bundlename_add"))
        self.assertContains(
            response, reverse("bundlename_edit", args=[bundlename.name])
        )


class BundleNameEditPageTest(TestCase):
    def setUp(self):
        self.user = user_model.objects.create(
            email="bundlenameedit1@testuser.com",
            username="bundlenameedit1",
        )
        self.user.set_password("12345o")
        self.user.save()
        self.bundlename = BundleName.objects.create(
            profile=self.user.profile, name="BundleName name", addresses=TEST_ADDRESS2
        )
        self.bundlename.save()
        with mock.patch("core.models.get_permission_provider") as mocked_provider:
            mocked_provider.return_value.votes_and_permission.return_value = [0, 0]
            self.client.login(username="bundlenameedit1", password="12345o")

    def post_invalid_input(self):
        return self.client.post(
            reverse("bundlename_edit", args=[self.bundlename.name]),
            data={"name": self.bundlename.name, "addresses": "foobar"},
        )

    def test_uses_bundlename_edit_bundlename(self):
        response = self.client.get(
            reverse("bundlename_edit", args=[self.bundlename.name])
        )
        self.assertTemplateUsed(response, "bundlename_edit.html")

    def test_displays_bundlename_name_form_for_edit_bundlename_data(self):
        response = self.client.get(
            reverse("bundlename_edit", args=[self.bundlename.name])
        )
        self.assertIsInstance(response.context["form"], ProfileBundleNameForm)
        self.assertContains(response, 'name="name"')

    def test_bundlename_edit_post_ends_in_bundlename_page(self):
        addresses = TEST_ADDRESS2
        response = self.client.post(
            reverse("bundlename_edit", args=[self.bundlename.name]),
            data={"name": self.bundlename.name, "addresses": addresses},
        )
        self.assertRedirects(
            response, reverse("bundlename_edit", args=[self.bundlename.name])
        )

    def test_bundlename_edit_for_invalid_input_nothing_saved_to_db(self):
        count = BundleName.objects.count()
        self.post_invalid_input()
        self.assertEqual(BundleName.objects.count(), count)

    def test_bundlename_edit_for_invalid_input_renders_bundlename_bundlename(self):
        response = self.post_invalid_input()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "bundlename_edit.html")

    def test_bundlename_edit_for_invalid_input_passes_form_to_bundlename(self):
        response = self.post_invalid_input()
        self.assertIsInstance(response.context["form"], ProfileBundleNameForm)


class BundleNameDeletePageTest(TestCase):
    def setUp(self):
        self.user = user_model.objects.create(
            email="bundlenamedelete1@testuser.com",
            username="bundlenamedelete1",
        )
        self.user.set_password("12345o")
        self.user.save()
        self.bundlename = BundleName.objects.create(
            profile=self.user.profile, name="BundleName name", addresses=TEST_ADDRESS2
        )
        self.bundlename.save()
        with mock.patch("core.models.get_permission_provider") as mocked_provider:
            mocked_provider.return_value.votes_and_permission.return_value = [0, 0]
            self.client.login(username="bundlenamedelete1", password="12345o")

    def test_bundlename_delete_uses_bundlename_delete_template(self):
        response = self.client.get(
            reverse("bundlename_delete", args=[self.bundlename.name])
        )
        self.assertTemplateUsed(response, "bundlename_delete.html")

    def test_bundlename_delete_displays_name_bundlename(self):
        """The page names the bundle and says the deletion is final.

        The wording changed on 2026-08-22 -- "Are you sure you want to delete
        this bundle name?" never said *which* one, on a page reached from a list
        of them. What is asserted now is the name and the finality, which is
        what the page is for; the sentence carrying them is copy.
        """
        response = self.client.get(
            reverse("bundlename_delete", args=[self.bundlename.name])
        )

        self.assertContains(response, self.bundlename.name)
        self.assertContains(response, "cannot be undone")

    def test_bundlename_delete_post_redirects_to_home_page(self):
        response = self.client.post(
            reverse("bundlename_delete", args=[self.bundlename.name])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual("/home/", response.url)


class BundleNamePageTest(TestCase):
    def setUp(self):
        self.user = user_model.objects.create(
            email="bundlename1@testuser.com",
            username="bundlename1",
        )
        self.user.set_password("12345o")
        self.user.save()
        self.bundlename = BundleName.objects.create(
            profile=self.user.profile,
            name="mybundle",
            addresses=f"{TEST_ADDRESS2} {TEST_ADDRESS3}",
        )
        with mock.patch("core.models.get_permission_provider") as mocked_provider:
            mocked_provider.return_value.votes_and_permission.return_value = [0, 0]
            self.client.login(username="bundlename1", password="12345o")

    def test_bundlename_redirects_to_home_page_for_no_bundle(self):
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Cluster"]
        self.user.profile.save()
        response = self.client.post(reverse("bundle_name", args=["foobar"]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual("/home/", response.url)

    def test_bundlename_redirects_to_bundle_page(self):
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Cluster"]
        self.user.profile.save()
        response = self.client.post(reverse("bundle_name", args=[self.bundlename.name]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(f"/{self.bundlename.bundle}", response.url)

    def test_bundlename_redirects_to_home_page_for_too_small_permission(self):
        BundleName.objects.create(
            profile=self.user.profile,
            name="mybundle1",
            addresses=f"{TEST_ADDRESS} {TEST_ADDRESS2}",
        )
        BundleName.objects.create(
            profile=self.user.profile,
            name="mybundle3",
            addresses=f"{TEST_ADDRESS} {TEST_ADDRESS3}",
        )
        BundleName.objects.create(
            profile=self.user.profile,
            name="mybundle4",
            addresses=f"{TEST_ADDRESS} {TEST_ADDRESS2} {TEST_ADDRESS3}",
        )
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Intro"]
        self.user.profile.save()
        response = self.client.post(reverse("bundle_name", args=[self.bundlename.name]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual("/home/", response.url)

    def test_bundlename_redirects_to_subscriptions_for_too_small_permission(self):
        self.user.profile.permission = 0
        self.user.profile.save()
        response = self.client.post(reverse("bundle_name", args=[self.bundlename.name]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual("/subscriptions/", response.url)


class LoginPageTest(TestCase):
    def post_invalid_input(self):
        return self.client.post(
            reverse("account_login"), data={"login": "logn", "password": "12345"}
        )

    def test_login_page_renders_login_template(self):
        response = self.client.get(reverse("account_login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/login.html")

    def test_login_view_renders_loginform(self):
        response = self.client.get(reverse("account_login"))
        self.assertIsInstance(response.context["form"], LoginForm)

    def test_for_invalid_input_renders_login_template(self):
        response = self.post_invalid_input()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/login.html")

    def test_login_page_for_invalid_input_passes_form_to_template(self):
        response = self.post_invalid_input()
        self.assertIsInstance(response.context["form"], LoginForm)

    def test_for_invalid_input_shows_errors_on_page(self):
        response = self.post_invalid_input()
        self.assertContains(
            response, "The username and/or password you specified are not correct."
        )

    def test_login_page_links_to_forget_password_page(self):
        response = self.client.get(reverse("account_login"))
        self.assertContains(response, reverse("account_reset_password"))


class SignupPageTest(TestCase):
    def post_invalid_input(self):
        return self.client.post(
            reverse("account_signup"),
            data={
                "email": "email@example.com",
                "password1": "12345",
                "password2": "1234",
            },
        )

    def test_signup_page_renders_signup_template(self):
        response = self.client.get(reverse("account_signup"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/signup.html")

    def test_signup_view_renders_customsignupform(self):
        response = self.client.get(reverse("account_signup"))
        self.assertIsInstance(response.context["form"], CustomSignupForm)

    def test_for_invalid_input_renders_signup_template(self):
        response = self.post_invalid_input()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "account/signup.html")

    def test_signup_page_for_invalid_input_passes_form_to_template(self):
        response = self.post_invalid_input()
        self.assertIsInstance(response.context["form"], CustomSignupForm)

    def test_signup_page_jsonld_script_haspart_elements(self):
        response = self.client.get(reverse("account_signup"))
        for part in ("login", "password/reset"):
            self.assertContains(
                response, '"url":"{}/accounts/{}/"'.format(settings.WEBSITE_URL, part)
            )


class ProfileSettingsPageTest(TestCase):
    """Testing class for :class:`core.views.ProfileSettingsView`."""

    def setUp(self):
        self.user = user_model.objects.create(
            email="settingspage@testuser.com",
            username="settingspage",
        )
        self.user.set_password("12345o")
        self.user.save()
        with mock.patch("core.models.get_permission_provider") as mocked_provider:
            mocked_provider.return_value.votes_and_permission.return_value = [0, 0]
            self.client.login(username="settingspage", password="12345o")

    def test_settings_page_uses_settings_template(self):
        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            response = self.client.get(reverse("profile_settings"))
        self.assertTemplateUsed(response, "profile_settings.html")

    def test_settings_page_post_valid_saves_preference(self):
        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            response = self.client.post(
                reverse("profile_settings"), data={"preferred_router": "folks"}
            )
        self.assertRedirects(response, reverse("profile_settings"))
        self.user.profile.refresh_from_db()
        assert self.user.profile.preferred_router == "folks"
        tags = [m.extra_tags for m in get_messages(response.wsgi_request)]
        assert tags == ["router"]

    def test_settings_page_post_invalid_rerenders_template(self):
        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            response = self.client.post(
                reverse("profile_settings"), data={"preferred_router": "absent"}
            )
        self.assertTemplateUsed(response, "profile_settings.html")

    def test_settings_page_liverefresh_post_saves_for_entitled_user(self):
        """**Opt-in, and off by default even for a reader who may have it.**

        A page that updates itself is not what everyone wants; the tier buys
        the choice rather than the behaviour.
        """
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
        self.user.profile.save()
        assert self.user.profile.live_refresh is False

        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            response = self.client.post(
                reverse("profile_settings"),
                data={"section": "liverefresh", "live_refresh": "on"},
            )

        self.assertRedirects(response, reverse("profile_settings"))
        self.user.profile.refresh_from_db()
        assert self.user.profile.live_refresh is True
        tags = [m.extra_tags for m in get_messages(response.wsgi_request)]
        assert tags == ["liverefresh"]

    def test_settings_page_liverefresh_post_can_be_turned_off_again(self):
        """A checkbox that cannot be cleared is a trap: an unchecked box sends
        no value at all, so the form has to read absence as False."""
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
        self.user.profile.live_refresh = True
        self.user.profile.save()

        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            self.client.post(
                reverse("profile_settings"), data={"section": "liverefresh"}
            )

        self.user.profile.refresh_from_db()
        assert self.user.profile.live_refresh is False

    def test_settings_page_liverefresh_post_saves_for_a_free_reader(self):
        """**The opt-in has to reach them or the allowance is unreachable.**

        This asserted a redirect to subscriptions, which was right while the
        bands admitted nobody below Asastatser. An allowance a reader cannot
        switch on is not an allowance, so the POST now saves and the limit is
        enforced per poll instead - see `liverefresh/allowance.py`.
        """
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Intro"]
        self.user.profile.save()

        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            self.client.post(
                reverse("profile_settings"),
                data={"section": "liverefresh", "live_refresh": "on"},
            )

        self.user.profile.refresh_from_db()
        assert self.user.profile.live_refresh is True

    def test_settings_page_liverefresh_post_redirects_when_the_manifest_refuses(
        self,
    ):
        """**The gate is the widget's manifest, not a tier written in the view.**

        On this deployment the free band admits everyone, so no permission
        reaches this branch - which is why it sat uncovered. It is not dead
        code: a fork hosting the widget on its own bands can exclude a reader,
        and `can_access_live_refresh` is what it would say so with. Mocking the
        gate is the only way to ask the view what it does when told no.
        """
        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            with mock.patch.object(
                type(self.user.profile), "can_access_live_refresh", return_value=False
            ):
                response = self.client.post(
                    reverse("profile_settings"),
                    data={"section": "liverefresh", "live_refresh": "on"},
                )

        self.assertRedirects(response, reverse("subscriptions"))
        self.user.profile.refresh_from_db()
        assert self.user.profile.live_refresh is False

    def test_settings_page_liverefresh_post_invalid_rerenders_bound_form(self):
        """**`is_valid` is mocked because nothing else can make it false.**

        The explorer section's equivalent test submits `"bogus"` and the
        `ChoiceField` rejects it. There is no such value here: Django gives a
        non-null model `BooleanField` a form field with `required=False`, which
        accepts an absent value, `"on"`, `""` and outright garbage alike, and
        `Profile` has neither a `clean()` nor a validator to fail instead. So
        this branch is unreachable through any request the site can receive.

        It is tested rather than deleted because what it pins is the *view's*
        contract, not the form's: an invalid form re-renders bound, so the
        reader sees the errors, instead of `form.save()` raising `ValueError`
        into a 500. Add a validator to `ProfileLiveRefreshForm` tomorrow and
        that promise still holds - which is the whole point of keeping the
        branch, and the reason it was worth a mock.
        """
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
        self.user.profile.save()

        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            with mock.patch.object(
                ProfileLiveRefreshForm, "is_valid", return_value=False
            ):
                response = self.client.post(
                    reverse("profile_settings"),
                    data={"section": "liverefresh", "live_refresh": "on"},
                )

        self.assertTemplateUsed(response, "profile_settings.html")
        assert response.status_code == 200
        # Bound, not a fresh form: the reader's submission comes back with it.
        assert response.context["liverefresh_form"].is_bound
        self.user.profile.refresh_from_db()
        assert self.user.profile.live_refresh is False

    def test_settings_page_liverefresh_names_the_daily_allowance(self):
        """**The upgrade prompt moved to where it means something.**

        This used to show the control disabled and name the tier, because below
        Asastatser a reader could not have it at all. They can now: every
        authenticated reader gets a daily allowance, and what a subscription
        buys is the limit coming off. So the control is live and the number is
        the prompt - told here rather than by the page quietly stopping later.
        """
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Intro"]
        self.user.profile.save()

        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            response = self.client.get(reverse("profile_settings"))

        content = response.content.decode()
        assert "30 minutes" in content
        assert reverse("subscriptions") in content
        assert "Real-time refresh is available from the" not in content

    def test_settings_page_liverefresh_says_nothing_about_limits_when_unlimited(self):
        """A subscriber has no number to be told, and a prompt to subscribe
        would be addressed to somebody who already has."""
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
        self.user.profile.save()

        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            response = self.client.get(reverse("profile_settings"))

        assert "minutes</span> of" not in response.content.decode()

    def test_settings_page_liverefresh_untiered_reader_gets_the_free_minutes(self):
        self.user.profile.permission = 0
        self.user.profile.save()

        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            response = self.client.get(reverse("profile_settings"))

        assert "15 minutes" in response.content.decode()

    def test_settings_page_explorer_post_saves_for_entitled_user(self):
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Intro"]
        self.user.profile.save()
        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            response = self.client.post(
                reverse("profile_settings"),
                data={"section": "explorer", "preferred_explorer": "lora"},
            )
        self.assertRedirects(response, reverse("profile_settings"))
        self.user.profile.refresh_from_db()
        assert self.user.profile.preferred_explorer == "lora"
        tags = [m.extra_tags for m in get_messages(response.wsgi_request)]
        assert tags == ["explorer"]

    def test_settings_page_explorer_post_redirects_unentitled_to_subscriptions(self):
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Intro"] - 1
        self.user.profile.save()
        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            response = self.client.post(
                reverse("profile_settings"),
                data={"section": "explorer", "preferred_explorer": "lora"},
            )
        self.assertRedirects(response, reverse("subscriptions"))
        self.user.profile.refresh_from_db()
        assert self.user.profile.preferred_explorer == ""

    def test_settings_page_explorer_post_invalid_rerenders_template(self):
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Intro"]
        self.user.profile.save()
        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            response = self.client.post(
                reverse("profile_settings"),
                data={"section": "explorer", "preferred_explorer": "bogus"},
            )
        self.assertTemplateUsed(response, "profile_settings.html")

    def _post_layout(self, layout):
        """POST the layout section and return the response.

        :param layout: the layout key to submit
        :type layout: str
        :return: :class:`HttpResponse`
        """
        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            return self.client.post(
                reverse("profile_settings"),
                data={"section": "layout", "preferred_layout": layout},
            )

    def test_settings_page_layout_post_saves_for_entitled_user(self):
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
        self.user.profile.save()
        response = self._post_layout("dynamic")
        self.assertRedirects(response, reverse("profile_settings"))
        self.user.profile.refresh_from_db()
        assert self.user.profile.preferred_layout == "dynamic"
        tags = [m.extra_tags for m in get_messages(response.wsgi_request)]
        assert tags == ["layout"]

    def test_settings_page_layout_post_redirects_unentitled_to_subscriptions(self):
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Intro"] - 1
        self.user.profile.save()
        response = self._post_layout("dynamic")
        self.assertRedirects(response, reverse("subscriptions"))
        self.user.profile.refresh_from_db()
        assert self.user.profile.preferred_layout == ""

    def test_settings_page_layout_post_above_tier_rerenders_rather_than_redirects(
        self,
    ):
        """Two different refusals, told apart.

        An Intro reader may use this section -- so a POST naming a layout they
        have not paid for is a wrong answer, not a closed door, and comes back
        as a form error on the page rather than as a trip to subscriptions.
        """
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Intro"]
        self.user.profile.save()
        response = self._post_layout("dynamic-compact")
        self.assertTemplateUsed(response, "profile_settings.html")
        self.user.profile.refresh_from_db()
        assert self.user.profile.preferred_layout == ""

    def test_settings_page_layout_post_invalid_rerenders_template(self):
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Intro"]
        self.user.profile.save()
        response = self._post_layout("bogus")
        self.assertTemplateUsed(response, "profile_settings.html")

    def test_settings_page_layout_post_saves_a_paid_layout_at_its_tier(self):
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
        self.user.profile.save()
        response = self._post_layout("dynamic")
        self.assertRedirects(response, reverse("profile_settings"))
        self.user.profile.refresh_from_db()
        assert self.user.profile.preferred_layout == "dynamic"

    def test_settings_page_offers_the_layout_section_to_entitled_user(self):
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Intro"]
        self.user.profile.save()
        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            response = self.client.get(reverse("profile_settings"))
        self.assertContains(response, 'id="id_save_layout"')
        self.assertContains(response, 'value="layout"')

    def test_settings_page_disables_the_layout_section_below_intro(self):
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Intro"] - 1
        self.user.profile.save()
        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            response = self.client.get(reverse("profile_settings"))
        self.assertNotContains(response, 'id="id_save_layout"')
        self.assertContains(response, 'id="id-section-layout"')

    def test_settings_page_names_the_layouts_the_reader_cannot_have(self):
        """A select with an unavailable option has to say why.

        The section is open at Intro and Dynamic is offered, while Dynamic
        compact is named with the tier that unlocks it.
        """
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Intro"]
        self.user.profile.save()
        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            response = self.client.get(reverse("profile_settings"))
        self.assertContains(response, "Dynamic")
        self.assertContains(response, "Asastatser")

    def test_settings_page_names_nothing_locked_when_all_unlocked(self):
        self.user.profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"]
        self.user.profile.save()
        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            response = self.client.get(reverse("profile_settings"))
        self.assertNotContains(response, "&mdash; from the")


class SwapEntryViewTest(TestCase):
    """Testing class for :class:`core.views.SwapEntryView`."""

    def setUp(self):
        self.address = "A" * 58
        self.url = reverse("swap_entry", args=[self.address])
        self.user = user_model.objects.create(
            email="swapentry@testuser.com", username="swapentry"
        )
        self.user.set_password("12345o")
        self.user.save()

    def _login(self):
        with mock.patch("core.models.get_permission_provider") as mocked_provider:
            mocked_provider.return_value.votes_and_permission.return_value = [0, 0]
            self.client.login(username="swapentry", password="12345o")

    def test_swap_entry_anonymous_renders_nothing(self):
        response = self.client.get(self.url)
        self.assertNotContains(response, "id-swap-enabled")

    def test_swap_entry_liverefresh_needs_the_tier_and_the_opt_in(self):
        """**Both halves, and neither implies the other.**

        The tier buys the *choice*; the setting is the reader taking it. A
        subscriber who never ticked the box wants the page they have, and a
        reader who ticked it before their tier lapsed must not keep a poll the
        deployment is no longer serving them.

        Asserted through the rendered marker rather than the context, because
        the marker is what `liverefresh.js` looks for and what `address.js`
        reads to decide whether to stand its own reload down.
        """
        self._login()
        profile = self.user.profile

        for live_refresh, permission, expected in (
            (False, SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], False),
            (False, 0, False),
            # Below Asastatser the marker is rendered now: the allowance is
            # spent per poll rather than withheld at the gate, and a reader with
            # no marker could never spend it.
            (True, SUBSCRIPTION_TIER_PERMISSIONS["Intro"], True),
            (True, 0, True),
            (True, SUBSCRIPTION_TIER_PERMISSIONS["Asastatser"], True),
        ):
            with self.subTest(live_refresh=live_refresh, permission=permission):
                profile.live_refresh = live_refresh
                profile.permission = permission
                profile.save()

                response = self.client.get(self.url)

                if expected:
                    self.assertContains(response, "id-liverefresh")
                else:
                    self.assertNotContains(response, "id-liverefresh")

    def test_swap_entry_liverefresh_is_absent_for_anonymous(self):
        """No profile, no opt-in, and nothing to poll on somebody's behalf."""
        response = self.client.get(self.url)

        self.assertNotContains(response, "id-liverefresh")

    def test_swap_entry_forbids_caching(self):
        """The one per-reader thing on a page whose own entry is shared.

        Django sends no cache headers of its own, which leaves a browser free
        to cache this *heuristically* -- and a stale copy is a reader looking
        at somebody else's answer to "which of these addresses are yours?".

        Content hashing does not cover it: the hash protects the asset, and
        what goes stale here is the HTML naming it, which then keeps loading
        the scripts it was built against. Asserted on the response rather than
        by reading the decorator, because the header is what a browser obeys.
        """
        self._login()
        with mock.patch("core.views.linked_addresses_for_user", return_value=set()):
            response = self.client.get(self.url)
        self.assertIn("no-store", response.headers.get("Cache-Control", ""))

    def test_swap_entry_linked_address_renders_swap_link(self):
        self._login()
        with mock.patch(
            "core.views.linked_addresses_for_user", return_value={self.address}
        ), mock.patch(
            "core.views.swap_entry_url", return_value="/widgets/folks/AAA"
        ) as mocked_url:
            response = self.client.get(self.url)
        self.assertContains(response, "/widgets/folks/AAA")
        mocked_url.assert_called_once()

    def test_swap_entry_carries_the_engine_endpoints_for_our_own_router(self):
        """The ASA Stats router quotes in our engine, so the modal has to know
        where to post.

        It did not carry these at all: the router's own shell page renders
        `data-quote-url`, so selecting it there worked, and selecting it on an
        address page answered "this deployment has no ASA Stats router
        endpoint" -- a message about configuration for what was two missing
        lines of context.
        """
        self._login()
        with mock.patch(
            "core.views.linked_addresses_for_user", return_value={self.address}
        ), mock.patch(
            "core.views.swap_entry_url", return_value="/widgets/asastats/AAA"
        ), mock.patch(
            "core.models.Profile.preferred_router_or_default",
            return_value="asastats",
        ):
            response = self.client.get(self.url)

        self.assertContains(response, 'data-quote-url="/widgets/asastats/quote"')
        self.assertContains(response, 'data-group-url="/widgets/asastats/group"')

    def test_swap_entry_leaves_the_endpoints_empty_for_a_vendor_router(self):
        """Every other router quotes in the browser against its own SDK, so
        there is nothing for it to post to us. `markerCfg` reads the empty
        string and that router's adapter never consults it."""
        self._login()
        with mock.patch(
            "core.views.linked_addresses_for_user", return_value={self.address}
        ), mock.patch(
            "core.views.swap_entry_url", return_value="/widgets/folks/AAA"
        ), mock.patch(
            "core.models.Profile.preferred_router_or_default", return_value="folks"
        ):
            response = self.client.get(self.url)

        self.assertContains(response, 'data-quote-url=""')
        self.assertContains(response, 'data-group-url=""')

    def test_swap_entry_linked_address_offers_the_dust_sweep(self):
        """The sweep's entry point, on the same gate and the same partial.

        Both are actions on an address the reader has proved they own, and
        neither may be rendered into the page itself - it is `cache_page`'d
        across users, so per-reader state there would be served to whoever
        warmed the entry.
        """
        self._login()
        with mock.patch(
            "core.views.linked_addresses_for_user", return_value={self.address}
        ), mock.patch("core.views.swap_entry_url", return_value="/widgets/folks/AAA"):
            response = self.client.get(self.url)
        self.assertContains(response, "id-dustsweep-open")
        self.assertContains(response, "dustsweep-modal")
        self.assertContains(response, self.address)

    def test_swap_entry_dust_sweep_survives_a_router_that_will_not_resolve(self):
        """Gated on linkage alone, and deliberately not on `swap_url`.

        A sweep needs an address the reader owns; a swap additionally needs a
        router that resolves. Hanging the sweep off the swap gate would hide it
        exactly when the router is misconfigured - which is when its close-out
        half is still perfectly usable, and carries most of the value anyway.
        """
        self._login()
        with mock.patch(
            "core.views.linked_addresses_for_user", return_value={self.address}
        ), mock.patch("core.views.swap_entry_url", return_value=""):
            response = self.client.get(self.url)
        self.assertNotContains(response, "id-swap-enabled")
        self.assertContains(response, "id-dustsweep-open")

    def test_swap_entry_anonymous_is_offered_no_sweep(self):
        response = self.client.get(self.url)
        self.assertNotContains(response, "id-dustsweep-open")

    def test_swap_entry_unlinked_renders_nothing(self):
        self._login()
        with mock.patch(
            "core.views.linked_addresses_for_user", return_value=set()
        ), mock.patch("core.views.swap_entry_url") as mocked_url:
            response = self.client.get(self.url)
        self.assertNotContains(response, "id-swap-enabled")
        mocked_url.assert_not_called()

    def test_swap_entry_bundle_resolves_addresses(self):
        self._login()
        bundle = "B" * 40
        with mock.patch(
            "core.views.check_bundle_addresses", return_value="ADDR1 ADDR2"
        ) as mocked_cba, mock.patch(
            "core.views.linked_addresses_for_user", return_value={"ADDR1"}
        ), mock.patch(
            "core.views.swap_entry_url", return_value="/widgets/folks/BBB"
        ):
            response = self.client.get(reverse("swap_entry", args=[bundle]))
        mocked_cba.assert_called_once_with(bundle)
        self.assertContains(response, "/widgets/folks/BBB")

    def test_swap_entry_bundle_publishes_every_owned_address_as_a_candidate(self):
        """One button on a bundle page, and every owned address behind it.

        A sweep is signed by one holder's key and a wallet has one active
        account, so at most one of a bundle's addresses is sweepable at any
        moment. This used to render a button *each*, which offered the reader
        several actions of which all but one built a group their wallet cannot
        sign - discovered at the signature prompt.

        Which one is sweepable is a browser fact, not a server one, so the
        server publishes the candidates and `dustsweep.js` picks. The button is
        rendered with no address and hidden until it has one.
        """
        self._login()
        second = "C" * 58
        with mock.patch(
            "core.views.check_bundle_addresses",
            return_value=f"{self.address} {second} {'D' * 58}",
        ), mock.patch(
            "core.views.linked_addresses_for_user",
            return_value={self.address, second},
        ), mock.patch("core.views.swap_entry_url", return_value=""):
            response = self.client.get(reverse("swap_entry", args=["B" * 40]))
        rendered = response.content.decode()
        assert rendered.count('class="dustsweep-open id-dustsweep-open"') == 1
        assert 'data-address=""' in rendered
        assert f'data-addresses="{self.address} {second}"' in rendered
        # Hidden until the browser says which of the two the wallet is on.
        assert 'class="dustsweep-toolbar" hidden' in rendered

    def test_swap_entry_never_offers_the_address_of_a_third_party(self):
        """A bundle address the reader does not own is not a candidate.

        The whole point of the candidate list is that it is the intersection of
        two facts. This is the server's half: only addresses the reader has
        proved they own reach the browser at all, so a wallet connected to
        somebody else's address that happens to be in this bundle still gets no
        button.
        """
        self._login()
        stranger = "D" * 58
        with mock.patch(
            "core.views.check_bundle_addresses",
            return_value=f"{self.address} {stranger}",
        ), mock.patch(
            "core.views.linked_addresses_for_user", return_value={self.address}
        ), mock.patch("core.views.swap_entry_url", return_value=""):
            response = self.client.get(reverse("swap_entry", args=["B" * 40]))
        assert response.context["dustsweep_addresses"] == [self.address]
        assert f'data-addresses="{self.address}"' in response.content.decode()

    def test_swap_entry_a_single_owned_address_gets_one_unlabelled_button(self):
        """The common case must not grow furniture it does not need.

        One button needs no address on it, so the label is not rendered at all
        rather than rendered and hidden.
        """
        self._login()
        with mock.patch(
            "core.views.linked_addresses_for_user", return_value={self.address}
        ), mock.patch("core.views.swap_entry_url", return_value=""):
            response = self.client.get(self.url)
        assert response.content.decode().count("id-dustsweep-open") == 1
        self.assertNotContains(response, "dustsweep-open-address")

    def test_swap_entry_opens_on_the_profiles_primary_address(self):
        """Which account the swap marker and the modal open on.

        The primary is the address the user authorised and the one their
        permission hangs off, so it is far and away the likeliest to be the
        one connected in the wallet. Alphabetical order - the previous rule -
        correlates with nothing.
        """
        self._login()
        first, primary = "A" * 58, "Z" * 58
        self.user.profile.address = primary
        self.user.profile.save()
        with mock.patch(
            "core.views.check_bundle_addresses", return_value=f"{first} {primary}"
        ), mock.patch(
            "core.views.linked_addresses_for_user", return_value={first, primary}
        ), mock.patch("core.views.swap_entry_url", return_value="/widgets/folks/BBB"):
            response = self.client.get(reverse("swap_entry", args=["B" * 40]))
        assert response.context["swap_address"] == primary
        assert response.context["dustsweep_address"] == primary
        # and every owned address is still offered a sweep of its own
        assert response.context["dustsweep_addresses"] == [first, primary]

    def test_swap_entry_falls_back_when_the_primary_is_not_on_the_page(self):
        """A stable wrong guess beats one that moves between page loads."""
        self._login()
        first, second = "A" * 58, "Z" * 58
        self.user.profile.address = "Q" * 58
        self.user.profile.save()
        with mock.patch(
            "core.views.check_bundle_addresses", return_value=f"{first} {second}"
        ), mock.patch(
            "core.views.linked_addresses_for_user", return_value={first, second}
        ), mock.patch("core.views.swap_entry_url", return_value="/widgets/folks/BBB"):
            response = self.client.get(reverse("swap_entry", args=["B" * 40]))
        assert response.context["swap_address"] == first

    def test_swap_marker_carries_every_address_the_reader_owns(self):
        """The guess is not enough on a bundle, so the candidates ride along.

        The marker used to carry the chosen address alone, and `swap.js` opened
        the panel on it whatever the wallet was connected to -- so a reader on
        the bundle's other address read the primary's holdings and balances.
        The browser can only correct that if it is told what the alternatives
        are, which is what `data-addresses` is for. Same shape, and the same
        reasoning, as the sweep's candidate list.
        """
        self._login()
        first, primary = "A" * 58, "Z" * 58
        self.user.profile.address = primary
        self.user.profile.save()
        with mock.patch(
            "core.views.check_bundle_addresses", return_value=f"{first} {primary}"
        ), mock.patch(
            "core.views.linked_addresses_for_user", return_value={first, primary}
        ), mock.patch("core.views.swap_entry_url", return_value="/widgets/folks/BBB"):
            response = self.client.get(reverse("swap_entry", args=["B" * 40]))

        assert response.context["swap_addresses"] == [first, primary]
        rendered = response.content.decode()
        marker = rendered.split('id="id-swap-enabled"', 1)[1].split("</span>", 1)[0]
        assert f'data-addresses="{first} {primary}"' in marker
        # the guess stays, as the no-wallet fallback
        assert f'data-address="{primary}"' in marker

    def test_the_asastats_router_names_no_sdk_bundle(self):
        """The production 500, from the console log of a real session.

        Every vendor router ships `<id>/<id>-sdk.bundle.js`; ours quotes in the
        engine, so its adapter is inside `swap/swap.js` and there is no bundle.
        The view built the path unconditionally and the template emitted
        `{% static %}` for it -- which *raises* under production's
        `ManifestStaticFilesStorage` and merely 404s under development's. So
        `/swap-entry/<address>/` answered 500 in production only, taking the
        marker, the modal, `swap.js` and the Dust Sweep with it, and the Swap
        button fell through to its no-JS href and reloaded the page.
        """
        self._login()
        self.user.profile.preferred_router = "asastats"
        self.user.profile.save()
        with mock.patch(
            "core.views.linked_addresses_for_user", return_value={self.address}
        ), mock.patch("core.views.swap_entry_url", return_value="/widgets/asastats/AAA"):
            response = self.client.get(self.url)

        assert response.status_code == 200
        assert response.context["swap_sdk_static"] == ""
        # and the tag is skipped rather than rendered empty, which would be a
        # request for the page's own URL
        assert "-sdk.bundle.js" not in response.content.decode()

    def test_a_router_that_ships_a_bundle_still_loads_it(self):
        """The other half: skipping must not skip the routers that need one."""
        self._login()
        self.user.profile.preferred_router = "folks"
        self.user.profile.save()
        with mock.patch(
            "core.views.linked_addresses_for_user", return_value={self.address}
        ), mock.patch("core.views.swap_entry_url", return_value="/widgets/folks/AAA"):
            response = self.client.get(self.url)

        assert response.context["swap_sdk_static"] == "folks/folks-sdk.bundle.js"
        assert "folks-sdk.bundle.js" in response.content.decode()

    def test_swap_marker_never_offers_an_address_the_reader_does_not_own(self):
        """The server's half of the gate, on the swap side this time.

        `swap.js` opens on the connected account only when it is one of these,
        so a stranger's address in the bundle must not reach the marker even
        though the page displays it.
        """
        self._login()
        stranger = "D" * 58
        with mock.patch(
            "core.views.check_bundle_addresses",
            return_value=f"{self.address} {stranger}",
        ), mock.patch(
            "core.views.linked_addresses_for_user", return_value={self.address}
        ), mock.patch("core.views.swap_entry_url", return_value="/widgets/folks/BBB"):
            response = self.client.get(reverse("swap_entry", args=["B" * 40]))

        assert response.context["swap_addresses"] == [self.address]
        assert stranger not in response.content.decode()


class SwapSourceRedirectViewTest(TestCase):
    """Testing class for :class:`core.views.SwapSourceRedirectView`."""

    def setUp(self):
        self.address = "A" * 58
        self.url = reverse("swap_source", args=[self.address, 31566704])
        self.user = user_model.objects.create(
            email="swapsrc@testuser.com", username="swapsrc"
        )
        self.user.set_password("12345o")
        self.user.save()

    def _login(self):
        with mock.patch("core.models.get_permission_provider") as mocked_provider:
            mocked_provider.return_value.votes_and_permission.return_value = [0, 0]
            self.client.login(username="swapsrc", password="12345o")

    def test_swap_source_anonymous_redirects(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            (
                "/accounts/login/?next=/swap/"
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA/31566704/"
            ),
        )

    def test_swap_source_linked_redirects_with_from(self):
        self._login()
        with mock.patch(
            "core.views.linked_addresses_for_user", return_value={self.address}
        ), mock.patch("core.views.swap_entry_url", return_value="/widgets/folks/AAA"):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/widgets/folks/AAA?from=31566704")

    def test_swap_source_linked_referer_without_query_string(self):
        self._login()
        referer = "http://testserver/some/address/path/"

        with mock.patch(
            "core.views.linked_addresses_for_user", return_value={self.address}
        ):
            # Pass the referer in the header
            response = self.client.get(self.url, HTTP_REFERER=referer)

        self.assertEqual(response.status_code, 302)
        # Because there was no '?' in the referer, it should use '?'
        self.assertEqual(response.url, f"{referer}?swap_open=31566704")

    def test_swap_source_linked_referer_with_existing_query_string(self):
        self._login()
        referer = "http://testserver/some/address/path/?filter=all"

        with mock.patch(
            "core.views.linked_addresses_for_user", return_value={self.address}
        ):
            response = self.client.get(self.url, HTTP_REFERER=referer)

        self.assertEqual(response.status_code, 302)
        # Because there was already a '?' in the referer, it should use '&'
        self.assertEqual(response.url, f"{referer}&swap_open=31566704")

    def test_swap_source_unlinked_404(self):
        self._login()
        with mock.patch("core.views.linked_addresses_for_user", return_value=set()):
            self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_swap_source_unlinked_referer_without_query_string(self):
        self._login()
        referer = "http://testserver/some/address/path/"

        with mock.patch("core.views.linked_addresses_for_user", return_value=set()):
            # Pass the referer in the header
            response = self.client.get(self.url, HTTP_REFERER=referer)

        self.assertEqual(response.status_code, 302)
        # Because there was no '?' in the referer, it should use '?'
        self.assertEqual(response.url, f"{referer}?swap_error=unlinked")

    def test_swap_source_unlinked_referer_with_existing_query_string(self):
        self._login()
        referer = "http://testserver/some/address/path/?filter=all"

        with mock.patch("core.views.linked_addresses_for_user", return_value=set()):
            response = self.client.get(self.url, HTTP_REFERER=referer)

        self.assertEqual(response.status_code, 302)
        # Because there was already a '?' in the referer, it should use '&'
        self.assertEqual(response.url, f"{referer}&swap_error=unlinked")

    def test_swap_source_no_router_404(self):
        self._login()
        with mock.patch(
            "core.views.linked_addresses_for_user", return_value={self.address}
        ), mock.patch("core.views.swap_entry_url", return_value=""):
            self.assertEqual(self.client.get(self.url).status_code, 404)


class AlertsAllowanceTest(TestCase):
    """Testing class for :py:func:`core.views._alerts_allowance`.

    **The guard is the point of this class.** The alerts widget lives in the
    widgets repo, which syncs separately, so "the frontend is newer than the
    widgets" is an ordinary state of the world for minutes at a time. A
    module-level import of it made `api.views` unimportable on 2026-09-20 and
    500'd every page on the site; the function-level import with an
    `ImportError` guard is what stops that recurring, and it is worth a test
    because nothing else would notice it being "tidied" back to the top.
    """

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="allow@example.com", email="allow@example.com", password="x"
        )

    def test_alerts_allowance_reads_the_readers_tier(self):
        from core.views import _alerts_allowance
        from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS

        profile = self.user.profile
        profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Professional"]
        profile.save()

        self.assertEqual(_alerts_allowance(self.user), (25, 0))

    def test_alerts_allowance_skips_the_query_below_the_tier(self):
        """Zero rules allowed means the count is never shown, so asking for it
        would be a query run and discarded on every address page."""
        from core.views import _alerts_allowance

        self.assertEqual(_alerts_allowance(self.user), (0, 0))

    def test_alerts_allowance_survives_a_widgets_repo_that_is_behind(self):
        """**The outage this exists to prevent.**

        With the widget unimportable the reader loses the alerts control and
        nothing else - rather than every page on the site returning 500.
        """
        from core.views import _alerts_allowance
        from utils.constants.users import SUBSCRIPTION_TIER_PERMISSIONS

        profile = self.user.profile
        profile.permission = SUBSCRIPTION_TIER_PERMISSIONS["Cluster"]
        profile.save()

        # `None` in sys.modules is what makes `from … import …` raise
        # ImportError, which is the shape a half-synced checkout produces.
        with mock.patch.dict(
            "sys.modules", {"widgets.inhouse.alerts.models": None}
        ):
            allowed, kept = _alerts_allowance(self.user)

        self.assertEqual((allowed, kept), (0, 0))

    def test_alerts_allowance_says_so_in_the_log(self):
        """A control vanishing silently is a bug report rather than a log line.
        The warning is how the skew is diagnosed instead of guessed at."""
        from core.views import _alerts_allowance

        with mock.patch.dict(
            "sys.modules", {"widgets.inhouse.alerts.tiers": None}
        ):
            with self.assertLogs("core.views", level="WARNING") as captured:
                _alerts_allowance(self.user)

        self.assertIn("alerts control unavailable", captured.output[0])
