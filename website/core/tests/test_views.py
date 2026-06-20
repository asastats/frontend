"""Testing module for :py:mod:`website.core.views` module."""

import re
from unittest import mock

from allauth.account.forms import LoginForm
from captcha.models import CaptchaStore
from django.conf import settings
from django.contrib.auth import get_user_model
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
    UpdateUserForm,
)
from core.models import BundleName, Profile
from utils.constants.core import INVALID_ADDRESS_TEXT
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
        response = self.client.get(
            reverse("bundlename_delete", args=[self.bundlename.name])
        )
        self.assertContains(
            response, "Are you sure you want to delete this bundle name?"
        )

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

    def test_settings_page_post_invalid_rerenders_template(self):
        with mock.patch("core.forms.swap_routers", return_value=[("folks", "Folks")]):
            response = self.client.post(
                reverse("profile_settings"), data={"preferred_router": "absent"}
            )
        self.assertTemplateUsed(response, "profile_settings.html")


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
        self.assertNotContains(response, "id-swap-entry")

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

    def test_swap_entry_unlinked_renders_nothing(self):
        self._login()
        with mock.patch(
            "core.views.linked_addresses_for_user", return_value=set()
        ), mock.patch("core.views.swap_entry_url") as mocked_url:
            response = self.client.get(self.url)
        self.assertNotContains(response, "id-swap-entry")
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
