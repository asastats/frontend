from math import isclose

import pytest
from selenium.webdriver.common.by import By

from .base import FunctionalTest
from .helpers import asset_holder


class AmmLinksTest(FunctionalTest):
    """"""

    # @pytest.mark.skip()
    def test_address_page_balance_distribution(self):
        asset_id, holder_balance, holder_address = asset_holder()
        # asset_id, holder_balance, holder_address = (
        #     793124631,
        #     169925,
        #     "MZVYCCDCTORHV3PYSI6XGT54UJXCL2I33LA5GF7IWOF6D4356XSKJ5TMPU",
        # )

        self.browser.get(self.server_url + "/" + holder_address)

        address = self.find_elem_by_tag("h4")
        self.assertIn(holder_address, address.text)

        self.find_elem_by_id(f"f{asset_id}").click()
        self.sleep()

        asset_section = self.find_elem_by_id(f"{asset_id}")

        span_decimals = asset_section.find_element(
            By.XPATH, ".//span[contains(., 'Decimals:')]"
        )
        decimals = int(span_decimals.text.split(" ")[1])
        label_balance = asset_section.find_element(By.CLASS_NAME, "balance")
        span_balance = label_balance.find_element(By.XPATH, "./following-sibling::span")
        balance = float(span_balance.text.split(" ")[0]) * 10**decimals

        assert isclose(balance, holder_balance, abs_tol=100)
