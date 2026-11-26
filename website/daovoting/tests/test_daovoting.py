"""Tests of the daovoting app: summaries, filters, views and providers."""

import base64
import hashlib
from unittest import mock

import pytest
from algosdk.encoding import decode_address
from django.contrib.auth import get_user_model
from django.test import Client, override_settings

from core.dao_provider import DaoProvider, get_dao_provider
from daovoting import panel, summary
from daovoting.templatetags.dao_tags import (
    grouped,
    markdown,
    micro,
    short_address,
    utc_time,
)
from daovoting.tests import fakes
from walletauth.models import LinkedAddress

FAKE = "daovoting.tests.fakes.FakeProvider"
MAINNET_FAKE = "daovoting.tests.fakes.MainnetFakeProvider"
pytestmark = pytest.mark.django_db


def _session(**values):
    return fakes._session(**values)


class TestDaovotingSummaryPhase:
    @pytest.mark.parametrize(
        "values,current_round,expected",
        [
            ({"status": 2}, 1, "passed"),
            ({"status": 3}, 1, "failed"),
            ({"status": 1}, 1, "sealed"),
            ({"status": 0}, 1999, "upcoming"),
            ({"status": 0}, None, "upcoming"),
            ({"status": 0}, 2000, "voting"),
            ({"status": 0}, 9000, "voting"),
            ({"status": 0}, 9001, "weighing"),
        ],
    )
    def test_daovoting_summary_phase(self, values, current_round, expected):
        assert summary.phase(_session(**values), current_round) == expected


class TestDaovotingSummaryHelpers:
    def test_daovoting_summary_countdown(self):
        assert summary.countdown(1000, None) is None
        assert summary.countdown(1000, 1000) is None
        assert summary.countdown(64_800, 1000) == {"rounds": 63_800, "days": 2.0}

    def test_daovoting_summary_potential_weight(self):
        assert summary.potential_weight(5_000_000, 10) == 5_000_000
        assert summary.potential_weight(50_000_000, 10) == 10_000_000

    def test_daovoting_summary_hash_check(self):
        digest = hashlib.sha256(b"x").hexdigest()
        assert summary.hash_check(b"x", summary.EMPTY_HASH) == "unset"
        assert summary.hash_check(None, digest) == "missing"
        assert summary.hash_check(b"x", digest) == "match"
        assert summary.hash_check(b"y", digest) == "differs"

    def test_daovoting_summary_period_file(self):
        result = summary.period_file(fakes.SOFAR_2)
        assert result["end_round"] == 67_100_000
        assert result["end_timestamp"] == 1_795_280_000
        assert result["seats"][fakes.SEAT_B] == {
            "total": 40_000_000,
            "venues": {"wallet": 40_000_000},
        }
        assert summary.period_file(
            b'{"end_round": 5, "seats": {"A": {"total": 1, "venues": {}}}}'
        ) == {
            "end_round": 5,
            "end_timestamp": 0,
            "seats": {"A": {"total": 1, "venues": {}}},
        }

    @pytest.mark.parametrize(
        "content",
        [None, b"not json", b"{}", b'{"end_round": 1, "seats": []}', b"[1]"],
    )
    def test_daovoting_summary_period_file_unreadable(self, content):
        assert summary.period_file(content) is None

    def test_daovoting_summary_ballot_rows(self):
        votes = {fakes.SEAT_A: 300, fakes.SEAT_B: 20, fakes.SEAT_C: 5}
        rows = summary.ballot_rows(
            fakes.BALLOTS[4], votes, {fakes.SEAT_A: 1, fakes.SEAT_B: 7_000_000}
        )
        assert [row["address"] for row in rows] == [
            fakes.SEAT_A,
            fakes.SEAT_B,
            fakes.SEAT_C,
        ]
        assert rows[0] == {  # the written final amount wins over the so-far one
            "address": fakes.SEAT_A,
            "voted": True,
            "option": 0,
            "max_votes": 300,
            "final": True,
            "amount": 10_000_000,
            "weight": 10_000_000,
        }
        assert (rows[1]["final"], rows[1]["amount"], rows[1]["weight"]) == (
            False,
            7_000_000,
            7_000_000,
        )
        assert rows[2]["voted"] is False and rows[2]["weight"] == 0
        unknown = summary.ballot_rows(fakes.BALLOTS[2], votes, None)
        assert [(row["amount"], row["weight"]) for row in unknown] == [(None, None)] * 3

    def test_daovoting_summary_session_summary_with_sofar(self):
        result = summary.session_summary(
            2,
            fakes.SESSIONS[2],
            fakes.BALLOTS[2],
            {fakes.SEAT_A: 300, fakes.SEAT_B: 20, fakes.SEAT_C: 5},
            5000,
            summary.period_file(fakes.SOFAR_2),
        )
        assert result["phase"] == "voting"
        assert result["provisional"] is True
        assert result["sofar_round"] == 67_100_000
        assert result["sofar_timestamp"] == 1_795_280_000
        assert result["seats"] == 3 and result["voters"] == 1
        assert result["turnout"] == 50_000_000
        assert result["possible"] == 70_000_000
        assert result["turnout_share"] == 71.43
        assert result["quorum_share"] == 50.0
        assert result["has_abstain"] is True
        assert result["to_end"] == {"rounds": 4001, "days": 0.1}
        assert result["options"] == [
            {
                "index": 0,
                "abstain": False,
                "total": 50_000_000,
                "share": 100.0,
                "winner": False,
            },
            {"index": 1, "abstain": False, "total": 0, "share": 0.0, "winner": False},
            {"index": 2, "abstain": True, "total": 0, "share": 0.0, "winner": False},
        ]

    def test_daovoting_summary_session_summary_without_sofar(self):
        result = summary.session_summary(
            2, fakes.SESSIONS[2], fakes.BALLOTS[2], {fakes.SEAT_A: 300}, 5000
        )
        assert result["turnout"] is None and result["possible"] is None
        assert result["provisional"] is False and result["sofar_round"] is None
        assert result["turnout_share"] == 0 and result["quorum_share"] == 0
        assert [option["total"] for option in result["options"]] == [None] * 3

    def test_daovoting_summary_session_summary_on_chain_totals(self):
        weighing = summary.session_summary(
            4,
            fakes.SESSIONS[4],
            fakes.BALLOTS[4],
            {fakes.SEAT_A: 300, fakes.SEAT_B: 20},
            5000,
            summary.period_file(fakes.SOFAR_2),  # ignored once amounts are written
        )
        assert weighing["phase"] == "weighing"
        assert weighing["provisional"] is False and weighing["sofar_round"] is None
        assert weighing["turnout"] == 10_000_000 and weighing["weighed"] == 1
        assert weighing["to_seal"] == {"rounds": 1000, "days": 0.0}
        passed = summary.session_summary(1, fakes.SESSIONS[1], {}, {}, 5000)
        assert [option["winner"] for option in passed["options"]] == [True, False, False]
        assert passed["possible"] is None and passed["turnout_share"] == 0
        no_abstain = summary.session_summary(
            1, _session(abstain=255, status=1, totals=[0, 0, 0]), {}, {}, 5000
        )
        assert no_abstain["has_abstain"] is False
        assert [option["share"] for option in no_abstain["options"]] == [0, 0, 0]

    def test_daovoting_summary_governor_rows(self):
        rows = summary.governor_rows(
            {fakes.SEAT_A: 300, fakes.SEAT_B: 20, fakes.SEAT_C: 5}, fakes.BALLOTS
        )
        assert [row["address"] for row in rows] == [
            fakes.SEAT_A,
            fakes.SEAT_B,
            fakes.SEAT_C,
        ]
        assert rows[0]["voted"] == [1, 2, 4]
        assert rows[1]["voted"] == [1, 4]
        assert rows[2]["voted"] == []


class TestDaovotingFilters:
    def test_daovoting_filters_micro(self):
        assert micro(None) == "-"
        assert micro(0) == "0"
        assert micro(1_234_567_890_000) == "1,234,567.89"
        assert micro(1) == "0.000001"

    def test_daovoting_filters_grouped(self):
        assert grouped(None) == "-"
        assert grouped(0) == "0"
        assert grouped(7298923) == "7,298,923"

    def test_daovoting_filters_markdown(self):
        html = markdown(
            "# Title\n\nText **bold**\n\n- a\n\n1. b\n\n> q\n\n"
            "| x |\n|---|\n| 1 |\n\n```\ncode\n```\n\n    indented\n\n"
            "[ok](https://asastats.com) [bad](javascript:alert(1)) <script>x</script>"
        )
        assert '<h1 class="mt-6 mb-3">Title</h1>' in html
        assert '<p class="mt-3">Text <strong>bold</strong></p>' in html
        assert '<ul class="list-disc pl-6 mt-3">' in html
        assert '<ol class="list-decimal pl-6 mt-3">' in html
        assert '<blockquote class="border-l-4' in html
        assert '<table class="table mt-3">' in html
        assert html.count('class="block bg-base-200') == 2
        assert (
            '<a href="https://asastats.com" class="link" rel="nofollow noopener">ok</a>'
            in html
        )
        assert "javascript:" in html and 'href="javascript' not in html
        assert "&lt;script&gt;" in html and "<script>" not in html
        assert markdown(None) == ""

    def test_daovoting_filters_utc_time(self):
        assert utc_time(1_795_280_000) == "2026-11-21 16:53 UTC"
        assert utc_time(0) == "" and utc_time(None) == ""

    def test_daovoting_filters_short_address(self):
        assert short_address(fakes.SEAT_A) == "VW55KZ…K3CBSU"
        assert short_address("SHORT") == "SHORT"


class TestDaovotingProviderDefault:
    def test_daovoting_default_provider_degrades_safely(self):
        provider = DaoProvider()
        assert provider.available() is False
        assert provider.current_round() is None
        assert provider.session_count() == 0
        assert provider.session(1) is None
        assert provider.ballots(1) == {}
        assert provider.seat_votes() == {}
        assert provider.document(1, "proposal.md") is None
        assert provider.vote_method() is None
        assert provider.permission_app_id is None

    @override_settings(DAO_PROVIDER="")
    def test_daovoting_get_dao_provider_without_setting(self):
        assert type(get_dao_provider()) is DaoProvider

    @override_settings(DAO_PROVIDER=FAKE)
    def test_daovoting_get_dao_provider_with_setting(self):
        assert isinstance(get_dao_provider(), fakes.FakeProvider)


class TestDaovotingViewsUnavailable:
    @override_settings(DAO_PROVIDER="")
    @pytest.mark.parametrize("url", ["/dao/", "/dao/governors/"])
    def test_daovoting_pages_without_provider(self, url):
        response = Client().get(url)
        assert response.status_code == 200
        assert b'id="id-dao-unavailable"' in response.content

    @override_settings(DAO_PROVIDER="")
    def test_daovoting_session_without_provider_is_404(self):
        assert Client().get("/dao/session/1/").status_code == 404


class TestDaovotingViews:
    @pytest.fixture(autouse=True)
    def _fake(self, settings):
        settings.DAO_PROVIDER = FAKE

    def test_daovoting_index_lists_newest_first(self):
        response = Client().get("/dao/")
        assert [s["id"] for s in response.context["sessions"]] == [4, 3, 2, 1]
        assert [s["phase"] for s in response.context["sessions"]] == [
            "weighing",
            "upcoming",
            "voting",
            "passed",
        ]
        content = response.content.decode()
        assert "Voting starts in 4000 rounds" in content
        assert "Voting ends in 4001 rounds" in content
        assert "sealing possible in 1000 rounds" in content
        assert "at most 50 of 70 possible weight (71.43 %)" in content
        assert "0 seats voted; weights are known after voting ends." in content

    def test_daovoting_index_skips_missing_session(self):
        with mock.patch.object(fakes.FakeProvider, "session_count", return_value=5):
            response = Client().get("/dao/")
        assert [s["id"] for s in response.context["sessions"]] == [4, 3, 2, 1]

    def test_daovoting_index_without_sessions(self):
        with mock.patch.object(fakes.FakeProvider, "session_count", return_value=0):
            response = Client().get("/dao/")
        assert b'id="id-dao-no-sessions"' in response.content

    def test_daovoting_session_page_while_voting(self):
        response = Client().get("/dao/session/2/")
        assert response.status_code == 200
        assert response.context["proposal_check"] == "match"
        assert response.context["final_check"] == "unset"
        assert response.context["venues_source"] == "sofar"
        content = response.content.decode()
        assert 'id="id-proposal-text"><p class="mt-3">Raise the fee.</p>' in content
        assert 'hx-trigger="every 30s"' in content
        assert "lowest amounts up to mainnet round 67100000 (2026-11-21 16:53 UTC)" in (
            content
        )
        assert "(mainnet holdings, at the same times" in content
        assert 'id="id-dao-provisional"' in content
        assert "Option 2 (Abstain) counts toward the turnout and the quorum" in content
        assert "<td>Option 2 (Abstain)</td>" in content
        assert f'data-seat="{fakes.SEAT_C}"' in content
        assert '<span class="text-base-content/60">at most</span> 50</td>' in content
        assert "/" + fakes.SEAT_A + '"' not in content

    def test_daovoting_session_page_live_partial(self):
        response = Client().get("/dao/session/2/?live=1")
        assert b"<html" not in response.content
        assert b'id="id-dao-live"' in response.content
        assert b"<h1" not in response.content

    def test_daovoting_session_page_without_sofar(self):
        with mock.patch.dict(fakes.DOCUMENTS, {2: {"proposal.md": fakes.PROPOSAL}}):
            content = Client().get("/dao/session/2/").content.decode()
        assert 'id="id-dao-no-totals"' in content
        assert "Weights are known after voting ends, or once weights so far" in content
        assert 'id="id-dao-sofar"' not in content

    def test_daovoting_session_page_upcoming(self):
        response = Client().get("/dao/session/3/")
        assert response.context["proposal_check"] == "missing"
        content = response.content.decode()
        assert "hx-trigger" not in content
        assert "Voting starts in 4000 rounds" in content
        assert "Weights are known after voting ends.</p>" in content

    def test_daovoting_session_page_weighing(self):
        content = Client().get("/dao/session/4/").content.decode()
        assert "sealing possible in 1000 rounds" in content
        assert "Final amounts written for 1 of 2 voters." in content
        assert 'id="id-dao-provisional"' not in content
        assert 'id="id-dao-sofar"' not in content

    def test_daovoting_session_page_passed(self):
        response = Client().get("/dao/session/1/")
        assert response.context["final_check"] == "match"
        content = response.content.decode()
        assert "The final file as published" in content
        assert "winner" in content
        assert "Quorum 100; an option wins" in content
        assert "Quorum 100 % reached.</p>" in content
        assert "No quorum" not in content
        with mock.patch.object(fakes.FakeProvider, "document", return_value=b"edited"):
            response = Client().get("/dao/session/1/")
        assert response.context["proposal_check"] == "differs"
        assert response.context["final_check"] == "differs"

    def test_daovoting_pages_without_quorum(self):
        sessions = {
            **fakes.SESSIONS,
            1: {**fakes.SESSIONS[1], "quorum": 0, "abstain": 255},
        }
        with mock.patch.dict(fakes.SESSIONS, sessions):
            index = Client().get("/dao/").content.decode()
            page = Client().get("/dao/session/1/").content.decode()
        assert index.count("No quorum.") == 1
        assert index.count("% reached.") == 2
        assert (
            "No quorum; an option wins with more than 1/2 of the votes cast.</p>" in page
        )
        assert "Abstain" not in page
        assert "No quorum.</p>" in page
        assert "% reached." not in page

    def test_daovoting_session_missing_is_404(self):
        assert Client().get("/dao/session/9/").status_code == 404

    def test_daovoting_document(self):
        response = Client().get("/dao/session/1/proposal.md")
        assert response.status_code == 200
        assert response.content == fakes.PROPOSAL
        assert response["Content-Type"] == "text/markdown; charset=utf-8"
        response = Client().get("/dao/session/1/final.json")
        assert response["Content-Type"] == "application/json; charset=utf-8"
        assert Client().get("/dao/session/2/sofar.json").content == fakes.SOFAR_2

    @pytest.mark.parametrize(
        "url",
        [
            "/dao/session/3/proposal.md",
            "/dao/session/1/x.txt",
            "/dao/session/1/snapshot.json",
        ],
    )
    def test_daovoting_document_missing_is_404(self, url):
        assert Client().get(url).status_code == 404

    def test_daovoting_governors(self):
        response = Client().get("/dao/governors/")
        assert response.context["session_count"] == 4
        assert len(response.context["rows"]) == 3
        content = response.content.decode()
        assert "not voted yet" in content
        assert "3 of 4" in content


@override_settings(DAO_PROVIDER=MAINNET_FAKE)
def test_daovoting_mainnet_seats_link_to_address_pages():
    response = Client().get("/dao/session/2/")
    assert f'href="/{fakes.SEAT_A}"'.encode() in response.content
    response = Client().get("/dao/governors/")
    assert f'href="/{fakes.SEAT_C}"'.encode() in response.content


class TestDaovotingVotingDappProvider:
    @pytest.fixture
    def module(self):
        return pytest.importorskip("core.dao_providers.votingdapp")

    @pytest.fixture
    def provider(self, module, settings):
        settings.DAO_NETWORK = "testnet"
        settings.DAO_CACHE_SECONDS = 30
        settings.DAO_DOCUMENTS_DIR = ""
        return module.VotingDappProvider()

    def test_daovoting_votingdapp_provider_network_and_app(self, module, settings):
        settings.DAO_NETWORK = "testnet"
        provider = module.VotingDappProvider()
        assert provider.available() and provider.app_id == module.VOTING_APP_ID_TESTNET
        settings.DAO_NETWORK = "mainnet"
        with mock.patch.object(module, "VOTING_APP_ID", None):
            provider = module.VotingDappProvider()
        assert not provider.available()
        assert provider.session_count() == 0
        assert provider.session(1) is None
        assert provider.ballots(1) == {}

    def test_daovoting_votingdapp_provider_algod_built_once(self, module, provider):
        env = {"algod_token_testnet": None, "algod_address_testnet": "http://node"}
        with (
            mock.patch.object(module, "environment_variables", return_value=env),
            mock.patch.object(module, "AlgodClient") as client,
        ):
            assert provider._algod() is provider._algod()
        client.assert_called_once_with("", "http://node")

    @staticmethod
    def _boxes(*names):
        return {"boxes": [{"name": base64.b64encode(name).decode()} for name in names]}

    def test_daovoting_votingdapp_provider_reads_are_cached(self, module, provider):
        client = mock.MagicMock()
        client.status.return_value = {"last-round": 77}
        provider._client = client
        prefix = b"v" + (2).to_bytes(8, "big")
        seat = decode_address(fakes.SEAT_A)
        client.application_boxes.side_effect = lambda app_id: (
            self._boxes(prefix + seat)
            if app_id == provider.app_id
            else self._boxes(decode_address(fakes.SEAT_A), decode_address(fakes.SEAT_B))
        )
        ballot = bytes([1]) + bytes(25)
        values = {
            prefix + seat: ballot,
            decode_address(fakes.SEAT_A): b"permission A",
            decode_address(fakes.SEAT_B): b"permission B",
        }
        rows = {"permission A": [3, 0], "permission B": [0, 5]}
        with (
            mock.patch.object(
                module, "app_global_state", return_value={"session_count": 2}
            ) as state,
            mock.patch.object(
                module, "session_values", return_value={"status": 0}
            ) as session,
            mock.patch.object(
                module, "_box_value", side_effect=lambda c, a, name: values[name]
            ) as box,
            mock.patch.object(
                module, "deserialize_values_data", side_effect=rows.get
            ) as decode,
        ):
            for _ in range(2):
                assert provider.current_round() == 77
                assert provider.session_count() == 2
                assert provider.session(2) == {"status": 0}
                assert provider.session(3) is None
                assert provider.ballots(2) == {
                    fakes.SEAT_A: {
                        "option": 1,
                        "max_votes": 0,
                        "eligible": 0,
                        "weight": 0,
                        "weighed": False,
                    }
                }
                assert provider.seat_votes() == {fakes.SEAT_A: 3}
        client.status.assert_called_once()
        state.assert_called_once_with(client, provider.app_id)
        session.assert_called_once_with(client, provider.app_id, 2)
        assert client.application_boxes.call_count == 2
        assert box.call_count == 3
        assert decode.call_count == 2

    def test_daovoting_votingdapp_provider_box_values(self, module, provider):
        client = mock.MagicMock()
        provider._client = client
        client.application_boxes.return_value = self._boxes(b"va", b"vb", b"vc", b"s1")
        raw = {b"va": b"1", b"vb": None, b"vc": b"3"}  # vb deleted meanwhile
        with mock.patch.object(
            module, "_box_value", side_effect=lambda c, a, name: raw[name]
        ) as box:
            assert provider._box_values(5, b"v") == {b"va": b"1", b"vc": b"3"}
        assert sorted(call.args[2] for call in box.call_args_list) == [
            b"va",
            b"vb",
            b"vc",
        ]
        client.application_boxes.return_value = self._boxes(b"s1")
        assert provider._box_values(5, b"v") == {}

    def test_daovoting_votingdapp_provider_seat_votes_without_boxes(
        self, module, provider
    ):
        provider._client = mock.MagicMock()
        provider._client.application_boxes.return_value = {"boxes": []}
        assert provider.seat_votes() == {}

    def test_daovoting_votingdapp_provider_sealed_ballots_follow_the_session_box(
        self, module, provider, settings
    ):
        settings.DAO_SEALED_BALLOTS_CACHE_SECONDS = 86400
        provider = module.VotingDappProvider()
        sealed = {"status": 1, "voters_count": 1, "totals": [5, 0]}
        with (
            mock.patch.object(provider, "session", return_value=sealed),
            mock.patch.object(provider, "_box_values", return_value={}) as read,
            mock.patch.object(module.cache, "set", wraps=module.cache.set) as cache_set,
        ):
            provider.ballots(1)
            provider.ballots(1)
            assert read.call_count == 1
            assert cache_set.call_args.args[2] == 86400
            sealed.update(voters_count=2, totals=[5, 7])  # a vote
            provider.ballots(1)
            assert read.call_count == 2
            assert cache_set.call_args.args[0].endswith("ballots:1:1:2:5,7")

    def test_daovoting_votingdapp_provider_open_session_ballots_use_short_cache(
        self, module, provider
    ):
        with (
            mock.patch.object(provider, "session", return_value={"status": 0}),
            mock.patch.object(provider, "_box_values", return_value={}),
            mock.patch.object(module.cache, "set") as cache_set,
        ):
            provider.ballots(4)
        assert cache_set.call_args.args[0].endswith(":ballots:4")
        assert cache_set.call_args.args[2] == 30

    def test_daovoting_votingdapp_provider_permission_app_and_vote_method(
        self, module, provider, settings
    ):
        assert provider.permission_app_id == module.permission_dapp_id("testnet")
        assert provider.vote_method() == "vote(uint64,uint64)void"
        with mock.patch.object(module, "read_json") as read_json:
            assert provider.vote_method() == "vote(uint64,uint64)void"
        read_json.assert_not_called()
        settings.DAO_NETWORK = "mainnet"
        assert module.VotingDappProvider().permission_app_id == module.permission_dapp_id(
            "mainnet"
        )

    def test_daovoting_votingdapp_provider_document(
        self, module, provider, settings, tmp_path
    ):
        assert provider.document(1, "proposal.md") is None
        settings.DAO_DOCUMENTS_DIR = str(tmp_path)
        (tmp_path / "1").mkdir()
        (tmp_path / "1" / "proposal.md").write_bytes(b"text")
        assert provider.document(1, "proposal.md") == b"text"
        assert provider.document(1, "final.json") is None
        assert provider.document(1, "snapshot.json") is None
        assert provider.document(1, "../secret") is None


def _user_with(*rows):
    user = get_user_model().objects.create_user(username="governor", password="x")
    for address, chain in rows:
        LinkedAddress.objects.create(
            profile=user.profile,
            address=address,
            canonical_address=address if chain == "algorand" else f"C{address[1:]}",
            chain=chain,
            auth_method="algorand_wallet" if chain == "algorand" else "evm_xchain",
        )
    return user


class TestDaovotingPanel:
    def test_daovoting_panel_linked_seats(self):
        votes = {fakes.SEAT_A: 300, fakes.SEAT_B: 0, fakes.SEAT_C: 5}
        assert panel.linked_seats(mock.MagicMock(is_authenticated=False), votes) == []
        user = _user_with(
            (fakes.SEAT_C, "algorand"),
            (fakes.SEAT_A, "algorand"),
            (fakes.SEAT_B, "algorand"),
            ("0xabc", "evm"),
        )
        assert panel.linked_seats(user, {**votes, "0xabc": 9}) == [
            fakes.SEAT_C,
            fakes.SEAT_A,
        ]

    def test_daovoting_panel_linked_seats_authorized_profile_address(self):
        votes = {fakes.SEAT_A: 300, fakes.SEAT_C: 5}
        user = _user_with()
        profile = user.profile
        profile.address = fakes.SEAT_A
        profile.save()
        assert panel.linked_seats(user, votes) == []
        profile.authorized = "nonce"
        profile.save()
        assert panel.linked_seats(user, votes) == [fakes.SEAT_A]
        LinkedAddress.objects.create(
            profile=profile,
            address=fakes.SEAT_A,
            canonical_address=fakes.SEAT_A,
            chain="algorand",
            auth_method="algorand_wallet",
            is_primary=True,
            login_enabled=True,
        )
        assert panel.linked_seats(user, votes) == [fakes.SEAT_A]

    def test_daovoting_panel_linked_seats_without_profile(self):
        user = mock.MagicMock(is_authenticated=True, profile=None)
        with mock.patch.object(panel.LinkedAddress.objects, "filter") as filt:
            filt.return_value.values_list.return_value = [fakes.SEAT_C]
            assert panel.linked_seats(user, {fakes.SEAT_C: 5}) == [fakes.SEAT_C]

    def test_daovoting_panel_venue_label(self):
        assert panel.venue_label("wallet") == "Wallet"
        assert panel.venue_label("lp 1234") == "LP token 1234"
        assert panel.venue_label("gat 1047879402") == "gat 1047879402"

    def test_daovoting_panel_vote_cards(self):
        votes = {fakes.SEAT_A: 300, fakes.SEAT_B: 20, fakes.SEAT_C: 5}
        rows = summary.ballot_rows(fakes.BALLOTS[4], votes, {fakes.SEAT_B: 90_000_000})
        venues = {fakes.SEAT_A: {"wallet": 10_000_000}}
        cards = panel.vote_cards(
            [fakes.SEAT_A, fakes.SEAT_B, "UNKNOWN"], rows, {**votes, "UNKNOWN": 1}, venues
        )
        assert cards[0] == {
            "address": fakes.SEAT_A,
            "votes": 300,
            "amount": 10_000_000,
            "weight": 10_000_000,
            "final": True,
            "below_max": True,
            "voted_option": 0,
            "venues": [{"name": "Wallet", "amount": 10_000_000}],
        }
        assert (cards[1]["weight"], cards[1]["final"], cards[1]["below_max"]) == (
            20_000_000,
            False,
            False,
        )
        assert cards[1]["voted_option"] == 2 and cards[1]["venues"] == []
        assert cards[2] == {
            "address": "UNKNOWN",
            "votes": 1,
            "amount": None,
            "weight": None,
            "final": False,
            "below_max": False,
            "voted_option": None,
            "venues": [],
        }


class TestDaovotingVotePanelViews:
    @pytest.fixture(autouse=True)
    def _fake(self, settings):
        settings.DAO_PROVIDER = FAKE

    @pytest.fixture
    def client(self):
        client = Client()
        client.force_login(
            _user_with((fakes.SEAT_A, "algorand"), (fakes.SEAT_C, "algorand"))
        )
        return client

    def test_daovoting_vote_panel_open_session(self, client):
        response = client.get("/dao/session/2/")
        vote_panel = response.context["vote_panel"]
        assert vote_panel["can_vote"] is True
        assert list(vote_panel["options"]) == [0, 1, 2]
        assert vote_panel["abstain"] == 2
        assert response.context["venues_source"] == "sofar"
        assert [card["address"] for card in vote_panel["cards"]] == [
            fakes.SEAT_C,
            fakes.SEAT_A,
        ]
        content = response.content.decode()
        assert 'id="id-dao-vote-panel"' in content
        assert 'data-permission-app-id="750094865"' in content
        assert 'data-vote-method="vote(uint64,uint64)void"' in content
        assert 'data-network="testnet"' in content
        assert content.count("data-vote-option=") == 6  # both seats can vote
        assert "gat 1047879402" in content and "LP token 1234" in content
        assert "Where the lowest amount was found (so far)" in content
        assert "data-vote-below-max" in content
        assert "Keep the ASASTATS on the seat address until voting ends." in content
        assert '<h2 id="vote">Your seat</h2>' in content
        assert "data-vote-votes>300</dd>" in content
        assert "Lowest ASASTATS so far</dt>" in content
        assert "data-vote-weight>at most 50</dd>" in content
        assert "data-vote-amount>0</dd>" in content  # seat C holds nothing so far
        assert '<span class="badge badge-success" data-vote-current>Option 0</span>' in (
            content
        )
        assert "data-vote-chosen>Option 0 (your vote)</button>" in content
        assert '">Change to Option 1</button>' in content
        assert '">Vote Option 0</button>' in content  # seat C hasn't voted

    def test_daovoting_vote_panel_without_sofar(self, client):
        with mock.patch.dict(fakes.DOCUMENTS, {2: {"proposal.md": fakes.PROPOSAL}}):
            response = client.get("/dao/session/2/")
        assert response.context["venues_source"] is None
        content = response.content.decode()
        assert "not measured yet" in content
        assert "known after voting ends</span>" in content
        assert "Where the lowest amount" not in content

    def test_daovoting_vote_panel_final_venues(self, client):
        response = client.get("/dao/session/1/")
        assert response.context["venues_source"] == "final"
        content = response.content.decode()
        assert "Where the lowest amount was found</summary>" in content
        assert "Lowest ASASTATS</dt>" in content
        assert "data-vote-weight>300</dd>" in content

    def test_daovoting_vote_panel_closed_and_upcoming(self, client):
        response = client.get("/dao/session/1/")
        assert response.context["vote_panel"]["can_vote"] is False
        assert b"data-vote-option=" not in response.content
        assert b"data-vote-wallets" not in response.content
        response = client.get("/dao/session/3/")
        assert b"Voting has not started yet." in response.content

    def test_daovoting_vote_panel_without_seats(self):
        client = Client()
        client.force_login(_user_with((fakes.SEAT_B, "evm")))
        response = client.get("/dao/session/2/")
        assert response.context["vote_panel"]["cards"] == []
        assert b"holds a governor seat" in response.content

    def test_daovoting_vote_panel_not_for_visitors_or_the_live_partial(self, client):
        response = Client().get("/dao/session/2/")
        assert response.context["vote_panel"] is None
        assert b'id="id-dao-sign-in"' in response.content
        assert b'id="id-dao-sign-in"' not in Client().get("/dao/session/1/").content
        response = client.get("/dao/session/2/?live=1")
        assert b"id-dao-vote-panel" not in response.content
