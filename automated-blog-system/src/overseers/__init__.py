"""Overseer layer (PR #21).

A supervisory control plane over the automated blog platform. Six
specialist overseers each embody one business function from the
income-stream blueprint, plus a Chief that runs the loop:

==========  ==================================  ==============================
overseer    function embodied                    watches
==========  ==================================  ==============================
chief       orchestration + budget               burn rate vs. $100 cap
systems     Custom Bot Development               crashes, stuck runs, config,
                                                 unmetered spend, dead code
content     Programmatic Content Agency          review queue, axis rejects,
                                                 freshness, thin pages
market      Automated E-commerce Research        MSRP floor, affiliate links,
                                                 niche pipeline health
revenue     Affiliate Funnel Management          monetization, attribution,
                                                 revenue signal, winners
audience    24/7 Lead Generation                 indexing, distribution
compliance  cross-cutting                        publish gate, disclosures,
                                                 paid-ad routing
==========  ==================================  ==============================

See ``docs/OVERSEER_LAYER.md``.
"""
from src.overseers.chief import ChiefOverseer, default_roster, run_cycle

__all__ = ["ChiefOverseer", "default_roster", "run_cycle"]
