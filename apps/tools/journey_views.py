"""apps/tools/journey_views.py — Journey narrative views."""
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from config.journeys import JOURNEYS, get_journey
from apps.tools.models import Tool, ToolCategory


def journey_list_view(request):
    """The 'Choose Your Path' landing page — all journeys."""
    # Enrich each journey with live tool counts from DB
    enriched = []
    for j in JOURNEYS:
        slugs = [s["tool_slug"] for s in j["steps"]]
        available = Tool.objects.filter(slug__in=slugs, is_active=True).count()
        enriched.append({**j, "tools_available": available, "total_steps": len(j["steps"])})

    # Session: last journey the user was on
    last_journey_slug = request.session.get("last_journey")
    last_journey = get_journey(last_journey_slug) if last_journey_slug else None

    return render(request, "journeys/list.html", {
        "journeys": enriched,
        "last_journey": last_journey,
        "page_title": "Choose Your Path — LamGen AI Journeys",
        "meta_description": "Pick a goal-driven journey and let LamGen guide you step by step through the right AI tools — no more guessing what to use next.",
    })


def journey_detail_view(request, journey_slug):
    """Individual journey page — story steps with tool cards."""
    journey = get_journey(journey_slug)
    if not journey:
        raise Http404

    # Track last visited journey in session
    request.session["last_journey"] = journey_slug
    request.session.modified = True

    # Enrich steps with live DB tool data
    enriched_steps = []
    for step in journey["steps"]:
        tool = Tool.objects.filter(slug=step["tool_slug"], is_active=True).select_related("category").first()
        enriched_steps.append({**step, "tool": tool})

    # Suggest next journey (cycle order)
    journey_slugs = [j["slug"] for j in JOURNEYS]
    current_idx = journey_slugs.index(journey_slug)
    next_journey = JOURNEYS[(current_idx + 1) % len(JOURNEYS)]

    return render(request, "journeys/detail.html", {
        "journey": journey,
        "steps": enriched_steps,
        "next_journey": next_journey,
        "all_journeys": JOURNEYS,
        "page_title": f"{journey['name']} — LamGen Journey",
        "meta_description": journey["problem"][:155],
    })
