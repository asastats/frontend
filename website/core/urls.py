"""Module containing core app's URL configurations."""

from django.conf import settings
from django.urls import re_path

from core import views as core_views
from utils.constants.users import BUNDLENAME_REGEX

urlpatterns = [
    # bots' pages
    re_path(
        r"^(?P<filename>(robots.txt|{}))$".format(settings.GOOGLE_OWNERSHIP_FILE),
        core_views.index_file,
        name="index_file",
    ),
    # html files
    re_path(
        r"^(?P<filename>(auth_privacy\.html|auth_terms\.html))$",
        core_views.html_file,
        name="html_file",
    ),
    re_path(
        rf"^(?P<suffix>({ settings.WEBSITE_SHORT_NAME }.png|"
        rf"{ settings.WEBSITE_SHORT_NAME }-dark.png|colors.png|icon.png"
        "|logo.png|logo-dark.png|logo.svg|logo400.png|whitepaper.pdf"
        "|transparency-report-202[1-6]-(?:1[012]|0?[1-9]).pdf))$",
        core_views.assets_file,
        name="assets_file",
    ),
    # serve social icons for use in emails
    re_path(
        r"^(?P<suffix>(discord24.png|twitter24.png|reddit24.png|github24.png))$",
        core_views.social_icons,
        name="social_icons",
    ),
    re_path(r"^$", core_views.IndexView.as_view(), name="index"),
    # user pages
    re_path(r"^home/$", core_views.HomePageView.as_view(), name="home"),
    re_path(r"^profile/$", core_views.ProfileEditView.as_view(), name="profile"),
    re_path(
        r"^profile/account/$",
        core_views.ProfileAccountView.as_view(),
        name="profile_account",
    ),
    re_path(
        r"^profile/deactivate/$",
        core_views.DeactivateProfileView.as_view(),
        name="deactivate_profile",
    ),
    re_path(r"^profile/api/$", core_views.ProfileApiView.as_view(), name="profile_api"),
    re_path(
        r"^profile/authorize/$",
        core_views.ProfileAuthorizeView.as_view(),
        name="profile_authorize",
    ),
    re_path(
        r"^profile/authorize/check/$",
        core_views.ProfileAuthorizeCheckView.as_view(),
        name="profile_authorize_check",
    ),
    re_path(
        r"^profile/addresses/$",
        core_views.ProfileAddressesView.as_view(),
        name="profile_addresses",
    ),
    re_path(
        r"^profile/addresses/link/$",
        core_views.ProfileLinkAddressView.as_view(),
        name="profile_link_address",
    ),
    re_path(
        r"^profile/permission/fetch/$",
        core_views.ProfilePermissionFetchView.as_view(),
        name="profile_permission_fetch",
    ),
    re_path(
        r"^profile/add-bundle$",
        core_views.BundleNameAddView.as_view(),
        name="bundlename_add",
    ),
    re_path(
        r"^profile/{}/delete/$".format(BUNDLENAME_REGEX),
        core_views.BundleNameDeleteView.as_view(),
        name="bundlename_delete",
    ),
    re_path(
        r"^profile/{}/$".format(BUNDLENAME_REGEX),
        core_views.BundleNameEditView.as_view(),
        name="bundlename_edit",
    ),
    # address
    re_path(
        r"^(MVEKYHFLJ63UKDYGNKCJD7WO5KFJZFVFMJPSDAWLDIDP4LUP575YDOW6GI)$",
        core_views.AddressViewCustom.as_view(),
        name="custom_address1",
    ),
    re_path(r"^([0-9A-Za-z]{58})$", core_views.AddressView.as_view(), name="address"),
    re_path(r"^([0-9A-Za-z]{40})$", core_views.AddressView.as_view(), name="bundle"),
    re_path(
        r"^([-\w]+\.(algo|Algo|ALGO))/(ans|Ans|ANS)$",
        core_views.AnsView.as_view(),
        name="ans",
    ),
    re_path(
        r"^([-\w]*\.*[-\w]+\.(algo|Algo|ALGO))/(nfd|Nfd|NFD)$",
        core_views.NfdView.as_view(),
        name="nfd",
    ),
    re_path(
        r"^([-\w]*\.*[-\w]+\.(algo|Algo|ALGO))$",
        core_views.NameServiceView.as_view(),
        name="name_service",
    ),
    re_path(r"^about/$", core_views.AboutView.as_view(), name="about"),
    re_path(r"^tokenomics/$", core_views.TokenomicsView.as_view(), name="tokenomics"),
    re_path(r"^faq/$", core_views.FaqView.as_view(), name="faq"),
    re_path(r"^disclaimer/$", core_views.DisclaimerView.as_view(), name="disclaimer"),
    re_path(r"^asm-privacy/$", core_views.ASMPrivacyView.as_view(), name="asm_privacy"),
    re_path(r"^features/$", core_views.FeaturesView.as_view(), name="features"),
    re_path(
        r"^subscriptions/$",
        core_views.SubscriptionsView.as_view(),
        name="subscriptions",
    ),
    ## EXPORT
    re_path(
        r"^export/([0-9A-Za-z]{58})/$",
        core_views.ExportView.as_view(),
        name="export_address",
    ),
    re_path(
        r"^export/([0-9A-Za-z]{40})/$",
        core_views.ExportView.as_view(),
        name="export_bundle",
    ),
    re_path(r"^export/download/$", core_views.export_download, name="export_download"),
    # bundle names
    re_path(
        r"^([\.\w\s-]{1,50})$", core_views.BundleNameView.as_view(), name="bundle_name"
    ),
]
