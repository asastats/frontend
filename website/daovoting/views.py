"""Read-only DAO voting pages; the on-chain `vote` is the sole authority."""

from django.http import Http404, HttpResponse
from django.shortcuts import render

from core.dao_provider import get_dao_provider
from daovoting.panel import linked_seats, vote_cards
from daovoting.summary import (
    governor_rows,
    hash_check,
    period_file,
    session_summary,
)

CONTENT_TYPES = {
    "proposal.md": "text/markdown",
    "final.json": "application/json",
    "sofar.json": "application/json",
}


def _base_context(provider):
    """Return the context every DAO page shares.

    :param provider: DAO provider instance
    :type provider: :class:`core.dao_provider.DaoProvider`
    :return: dict
    """
    return {
        "available": provider.available(),
        "network": provider.network,
        "app_id": provider.app_id,
    }


def _summary(provider, session_id, current_round, seat_votes):
    """Return the summary of one session, None if there is no such session.

    :param provider: DAO provider instance
    :type provider: :class:`core.dao_provider.DaoProvider`
    :param session_id: voting session identifier
    :type session_id: int
    :param current_round: latest round
    :type current_round: int
    :param seat_votes: maximum votes keyed by seat address
    :type seat_votes: dict
    :return: dict
    """
    session = provider.session(session_id)
    if session is None:
        return None
    sofar = provider.document(session_id, "sofar.json")
    return session_summary(
        session_id,
        session,
        provider.ballots(session_id),
        seat_votes,
        current_round,
        period_file(sofar) if sofar else None,
    )


def _vote_panel(user, provider, summary, venues):
    """Return the vote panel's context for a signed-in user, None for a visitor.

    :param user: requesting user
    :type user: :class:`django.contrib.auth.models.User`
    :param provider: DAO provider instance
    :type provider: :class:`core.dao_provider.DaoProvider`
    :param summary: the session's summary
    :type summary: dict
    :param venues: venues keyed by seat from the file that applies, {} for none
    :type venues: dict
    :return: dict
    """
    if not getattr(user, "is_authenticated", False):
        return None
    seat_votes = provider.seat_votes()
    return {
        "cards": vote_cards(
            linked_seats(user, seat_votes), summary["rows"], seat_votes, venues
        ),
        "can_vote": summary["phase"] == "voting",
        "options": range(summary["session"]["options_count"]),
        "abstain": summary["session"]["abstain"],
        "permission_app_id": provider.permission_app_id,
        "vote_method": provider.vote_method(),
    }


def dao_index(request):
    """Render every session, newest first, with its totals and quorum progress.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :return: :class:`django.http.HttpResponse`
    """
    provider = get_dao_provider()
    context = _base_context(provider)
    sessions = []
    if context["available"]:
        current_round = provider.current_round()
        seat_votes = provider.seat_votes()
        for session_id in range(provider.session_count(), 0, -1):
            summary = _summary(provider, session_id, current_round, seat_votes)
            if summary is not None:
                sessions.append(summary)
        context["current_round"] = current_round
    context["sessions"] = sessions
    return render(request, "daovoting/index.html", context)


def dao_session(request, session_id):
    """Render one session; `?live=1` renders only the polled totals and ballots.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :param session_id: voting session identifier
    :type session_id: int
    :return: :class:`django.http.HttpResponse`
    """
    provider = get_dao_provider()
    context = _base_context(provider)
    current_round = provider.current_round() if context["available"] else None
    summary = (
        _summary(provider, session_id, current_round, provider.seat_votes())
        if context["available"]
        else None
    )
    if summary is None:
        raise Http404("There is no such voting session.")

    session = summary["session"]
    proposal = provider.document(session_id, "proposal.md")
    final = provider.document(session_id, "final.json")
    final_check = hash_check(final, session["final_hash"])
    if final_check == "match":
        venues_file, venues_source = period_file(final), "final"
    else:
        sofar = provider.document(session_id, "sofar.json")
        venues_file, venues_source = (
            (period_file(sofar), "sofar") if sofar else (None, None)
        )
    venues = (
        {address: seat["venues"] for address, seat in venues_file["seats"].items()}
        if venues_file
        else {}
    )
    context.update(
        {
            "s": summary,
            "current_round": current_round,
            "proposal_text": proposal.decode("utf-8", "replace") if proposal else None,
            "proposal_check": hash_check(proposal, session["proposal_hash"]),
            "final_check": final_check,
            "final_published": final is not None,
            "venues_source": venues_source if venues else None,
        }
    )
    template = "daovoting/session.html"
    if request.GET.get("live"):
        template += "#live"
    else:
        context["vote_panel"] = _vote_panel(request.user, provider, summary, venues)
    return render(request, template, context)


def dao_document(request, session_id, name):
    """Return a session's published file as is, for checking its hash.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :param session_id: voting session identifier
    :type session_id: int
    :param name: file name, a key of :data:`CONTENT_TYPES`
    :type name: str
    :return: :class:`django.http.HttpResponse`
    """
    content = get_dao_provider().document(session_id, name)
    if name not in CONTENT_TYPES or content is None:
        raise Http404("This file is not published here.")
    response = HttpResponse(content, content_type=f"{CONTENT_TYPES[name]}; charset=utf-8")
    response["Content-Disposition"] = f'inline; filename="session-{session_id}-{name}"'
    return response


def dao_governors(request):
    """Render every seat: maximum votes and the sessions it voted in.

    :param request: Django request object
    :type request: :class:`django.http.HttpRequest`
    :return: :class:`django.http.HttpResponse`
    """
    provider = get_dao_provider()
    context = _base_context(provider)
    rows = []
    if context["available"]:
        sessions_ballots = {
            session_id: provider.ballots(session_id)
            for session_id in range(1, provider.session_count() + 1)
        }
        rows = governor_rows(provider.seat_votes(), sessions_ballots)
        context["session_count"] = len(sessions_ballots)
    context["rows"] = rows
    return render(request, "daovoting/governors.html", context)
