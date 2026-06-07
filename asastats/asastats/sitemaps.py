from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib import sitemaps
from django.urls import reverse

PUBLISHING_DATE = datetime(2022, 2, 5)


class StaticViewSitemap(sitemaps.Sitemap):
    """Static pages sitemap creator class.

    Priority 1.0 means higher priority relative to site.

    :var StaticViewSitemap.priority: defaults to 0.5
    :var StaticViewSitemap.protocol: presented protocol ('https' or 'http')
    :var changefreq: defines frequency for crawlers, "daily", "weekly", ...
    """

    priority = 0.5
    protocol = settings.SITEMAP_PROTOCOL
    changefreq = "daily"

    def items(self):
        """Set static pages names to include in sitemap file.

        Add a datetime object as the third value in tuple for pubdate
        different than PUBLISHING_DATE-

        :return: tuple of page names
        """
        items = [
            ("about", ()),
            ("tokenomics", ()),
            ("faq", ()),
            ("features", ()),
            ("subscriptions", ()),
            ("disclaimer", ()),
            ("html_file", ["auth_privacy.html"]),
            ("html_file", ["auth_terms.html"]),
            ("asm_privacy", ()),
            ("account_signup", ()),
            ("account_login", ()),
            ("account_reset_password", ()),
            ("assets_file", ["whitepaper.pdf"]),
        ]
        start = datetime(2021, 11, 1, 0, 0, 0)
        current = start + relativedelta(months=0)
        months = 0
        while True:
            year = current.year
            month = current.month
            items.append(
                (
                    "assets_file",
                    [f"transparency-report-{year}-{str(month).zfill(2)}.pdf"],
                )
            )
            months += 1
            current = start + relativedelta(months=months)
            if current > datetime.today() + relativedelta(months=-1):
                break

        return items

    def location(self, args):
        """Return reversed url for given page slug and eventual argument.

        :param args: name, (args)
        :type args: string, (string,)
        :return: page url
        """

        if len(args[1]) > 0:
            return reverse(args[0], args=args[1])
        return reverse(args[0])

    def lastmod(self, args):
        """Return date when page in args changed.

        We set it to constant value if date isn't set in args. If there's a
        third element in tuple we return it if it's a datetime object.

        :return: datetime
        """
        if len(args) > 2 and isinstance(args[2], datetime):
            return args[2]
        return PUBLISHING_DATE


class PrioritizedStaticViewSitemap(StaticViewSitemap):
    """Static pages sitemap creator class for pages with highest priority.

    Add a datetime object as the third value in tuple for pubdate
    different than PUBLISHING_DATE-

    :var PrioritizedStaticViewSitemap.priority: defaults to highest priority
    :var PrioritizedStaticViewSitemap.protocol: defines presented protocol
    """

    priority = 1.0
    protocol = settings.SITEMAP_PROTOCOL

    def items(self):
        """Sets static pages names to include in sitemap file.

        :return: list of page names
        """
        return [
            ("index", ()),
        ]
