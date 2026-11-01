"""Independent Poisson goals with shrunk strengths, chronological Elo and form.
All feature rows precede kickoff. Predictions are immutable pre-match snapshots.
"""

import json
import math
from collections import defaultdict
from datetime import timedelta
from sqlalchemy import select
from backend.models.entities import Match, Prediction, Setting, Team, now

OUTCOMES = ("Home", "Draw", "Away")
BASE_VERSION = "poisson-elo-v1"


def outcome(h, a):
    return "Home" if h > a else "Away" if a > h else "Draw"


def goals(lam):
    # 0..24 retains effectively all mass for capped means <= 4.5.
    values = [math.exp(-lam)]
    for k in range(1, 25):
        values.append(values[-1] * lam / k)
    return values


def calculate(home_id, away_id, history, elo_weight=0.18):
    ratings = defaultdict(lambda: 1500.0)
    for m in history:
        expected = 1 / (
            1 + 10 ** ((ratings[m.away_id] - ratings[m.home_id] - 65) / 400)
        )
        actual = (
            1
            if m.home_goals > m.away_goals
            else 0
            if m.home_goals < m.away_goals
            else 0.5
        )
        change = 24 * (actual - expected)
        ratings[m.home_id] += change
        ratings[m.away_id] -= change
    n = len(history)
    home_mean = (sum(m.home_goals for m in history) + 1.45 * 20) / (n + 20)
    away_mean = (sum(m.away_goals for m in history) + 1.15 * 20) / (n + 20)
    league_mean = (home_mean + away_mean) / 2

    def team_stats(tid):
        rows = [m for m in history if tid in (m.home_id, m.away_id)][-10:]
        gf = ga = points = 0
        form = []
        for m in rows:
            g, c = (
                (m.home_goals, m.away_goals)
                if m.home_id == tid
                else (m.away_goals, m.home_goals)
            )
            gf += g
            ga += c
            points += 3 if g > c else 1 if g == c else 0
            form.append("W" if g > c else "D" if g == c else "L")
        # Five pseudo-matches shrink small samples to league average.
        return (
            (gf + 5 * league_mean) / (len(rows) + 5) / league_mean,
            (ga + 5 * league_mean) / (len(rows) + 5) / league_mean,
            (points + 5 * 1.35) / (len(rows) + 5),
            form[-5:],
            len(rows),
        )

    ha, hd, hp, hform, hn = team_stats(home_id)
    aa, ad, ap, aform, an = team_stats(away_id)
    elo_edge = max(-0.4, min(0.4, (ratings[home_id] - ratings[away_id]) / 800))
    form_edge = max(-0.12, min(0.12, (hp - ap) * 0.055))
    h2h = [m for m in history if {m.home_id, m.away_id} == {home_id, away_id}][-5:]
    edge = 0
    for m in h2h:
        edge += (
            (m.home_goals - m.away_goals)
            if m.home_id == home_id
            else (m.away_goals - m.home_goals)
        )
    h2h_edge = max(-0.06, min(0.06, edge / (len(h2h) + 5) * 0.03))
    xh = home_mean * ha * ad * math.exp(elo_weight * elo_edge + form_edge + h2h_edge)
    xa = away_mean * aa * hd * math.exp(-elo_weight * elo_edge - form_edge - h2h_edge)
    xh = max(0.2, min(4.5, xh))
    xa = max(0.2, min(4.5, xa))
    ph, pa = goals(xh), goals(xa)
    probs = dict.fromkeys(OUTCOMES, 0.0)
    over15 = over25 = over35 = btts = total = 0.0
    best = (0, 0, 0.0)
    for h, hprob in enumerate(ph):
        for a, aprob in enumerate(pa):
            p = hprob * aprob
            total += p
            probs[outcome(h, a)] += p
            if h + a > 1:
                over15 += p
            if h + a > 2:
                over25 += p
            if h + a > 3:
                over35 += p
            if h > 0 and a > 0:
                btts += p
            if p > best[2]:
                best = (h, a, p)
    probs = {k: v / total for k, v in probs.items()}
    winner = max(probs, key=probs.get)
    confidence = (
        "Higher"
        if probs[winner] >= 0.65 and min(hn, an) >= 8
        else "Moderate"
        if probs[winner] >= 0.48 and min(hn, an) >= 5
        else "Low"
    )
    return {
        "probabilities": probs,
        "expected_goals": {"home": xh, "away": xa},
        "scoreline": f"{best[0]}–{best[1]}",
        "scoreline_probability": best[2] / total,
        "goal_lines": {
            "over_1_5": over15 / total,
            "under_1_5": 1 - over15 / total,
            "over_2_5": over25 / total,
            "under_2_5": 1 - over25 / total,
            "over_3_5": over35 / total,
            "under_3_5": 1 - over35 / total,
        },
        "over25": over25 / total,
        "under25": 1 - over25 / total,
        "btts": btts / total,
        "outcome": winner,
        "confidence": confidence,
        "home_form": hform,
        "away_form": aform,
        "elo": {"home": round(ratings[home_id]), "away": round(ratings[away_id])},
        "sample_sizes": {"home": hn, "away": an, "league": n, "head_to_head": len(h2h)},
        "explanation": [
            f"League scoring baseline is {home_mean:.2f} home and {away_mean:.2f} away goals; this includes home advantage.",
            f"Recent scoring and conceding strengths use up to ten matches per team, shrunk toward the league average with five pseudo-matches.",
            f"Elo ratings are {ratings[home_id]:.0f} versus {ratings[away_id]:.0f}; form points per match are {hp:.2f} versus {ap:.2f}.",
            f"{len(h2h)} earlier head-to-head meetings contribute a capped adjustment of {h2h_edge:+.3f}.",
            f"The independent Poisson model estimates {xh:.2f} and {xa:.2f} goals. {winner} is the largest outcome probability ({probs[winner]:.1%}).",
            f"Most likely exact score: {best[0]}–{best[1]} ({best[2] / total:.1%}); goal-line probabilities come from the full score distribution.",
            "Confidence is a probability-and-sample-size label, not a calibrated guarantee. Injuries, lineups and red cards are not modeled.",
        ],
        "assumptions": "Independent goals; stable recent strength; league priors 1.45 home / 1.15 away for sparse data.",
    }


def history_for(db, m):
    return list(
        db.scalars(
            select(Match)
            .where(
                Match.league_id == m.league_id,
                Match.source == m.source,
                Match.status == "FINISHED",
                Match.kickoff < m.kickoff,
                Match.kickoff >= m.kickoff - timedelta(days=730),
            )
            .order_by(Match.kickoff, Match.id)
        )
    )


def get_prediction(db, m, retrospective=False):
    p = db.scalar(select(Prediction).where(Prediction.match_id == m.id))
    if p:
        return p
    config = db.get(Setting, "model")
    settings = (
        json.loads(config.value)
        if config
        else {"elo_weight": 0.18, "version": BASE_VERSION}
    )
    data = calculate(m.home_id, m.away_id, history_for(db, m), settings["elo_weight"])
    eligible = m.status == "SCHEDULED" and m.kickoff > now() and not retrospective
    p = Prediction(
        match_id=m.id,
        payload=json.dumps(data),
        model_version=settings["version"],
        eligible=eligible,
    )
    db.add(p)
    db.flush()
    return p


def evaluate(db, m):
    p = db.scalar(select(Prediction).where(Prediction.match_id == m.id))
    if not p or m.status != "FINISHED":
        return
    data = json.loads(p.payload)
    actual = outcome(m.home_goals, m.away_goals)
    p.correct = data["outcome"] == actual
    p.brier = sum(
        (data["probabilities"][k] - (1 if k == actual else 0)) ** 2 for k in OUTCOMES
    )


def retrain(db):
    # Walk-forward grid calibration on past results; future fixtures never enter training.
    rows = list(
        db.scalars(
            select(Match)
            .where(
                Match.status == "FINISHED",
                Match.kickoff < now(),
                Match.source != "sample",
            )
            .order_by(Match.kickoff, Match.id)
        )
    )
    scored = []
    for weight in (0.0, 0.18, 0.4):
        losses = []
        for i, m in enumerate(rows):
            past = [
                x
                for x in rows[:i]
                if x.league_id == m.league_id
                and x.source == m.source
                and x.kickoff < m.kickoff
            ]
            if len(past) < 20:
                continue
            pred = calculate(m.home_id, m.away_id, past, weight)
            losses.append(
                sum(
                    (
                        pred["probabilities"][k]
                        - (k == outcome(m.home_goals, m.away_goals))
                    )
                    ** 2
                    for k in OUTCOMES
                )
            )
        if losses:
            scored.append((sum(losses) / len(losses), weight, len(losses)))
    if not scored:
        return {
            "message": "Need at least 21 earlier results within a league and source. Existing model retained."
        }
    loss, weight, n = min(scored)
    report = {
        "elo_weight": weight,
        "version": BASE_VERSION + "-" + now().strftime("%Y%m%d%H%M%S"),
        "walk_forward_brier": loss,
        "validation_matches": n,
        "note": "Tuning-set walk-forward score, not independent test accuracy. Existing snapshots remain unchanged.",
    }
    setting = db.get(Setting, "model")
    if setting:
        setting.value = json.dumps(report)
    else:
        db.add(Setting(key="model", value=json.dumps(report)))
    return report
