from __future__ import annotations

from typing import Any

from paisapal.analysis.models import AnalysisInput, AnalysisResult
from paisapal.providers.base import EvidenceSnapshot, utc_iso


def build_vcp_summary_from_analysis(data: AnalysisInput, result: AnalysisResult) -> dict[str, Any]:
    return {
        "ticker": data.ticker,
        "vcp_score": result.vcp_score,
        "vcp_stage": _stage_label(result.vcp_score),
        "tech_output": _tech_output_label(result.vcp_score, result.vcp_rating),
        "vcp_rating": result.vcp_rating,
    }


def build_vcp_summary_from_report(
    report: dict,
    evidence: list[EvidenceSnapshot] | None = None,
) -> dict[str, Any]:
    analysis = report.get("analysis") if isinstance(report.get("analysis"), dict) else {}
    ticker = str(report.get("ticker") or analysis.get("ticker") or "Unknown").upper()
    evidence = _coerce_evidence_snapshots(evidence or [])
    profile = _best_vcp_profile(evidence)
    vcp_score = _float_or_none(report.get("vcp_score"))
    if vcp_score is None:
        vcp_score = _float_or_none(analysis.get("vcp_score"))
    if vcp_score is None:
        vcp_score = _proxy_vcp_score_from_evidence(report, evidence, profile)
    tech_output = (
        report.get("vcp_rating")
        or analysis.get("vcp_rating")
        or report.get("vcp_rating")
        or report.get("technical_rating")
        or analysis.get("context_rating")
        or analysis.get("technical_rating")
        or report.get("context_rating")
        or "Missing"
    )
    return {
        "ticker": ticker,
        "vcp_score": vcp_score,
        "vcp_stage": _stage_label(vcp_score, profile),
        "tech_output": _tech_output_label(vcp_score, tech_output, profile),
        "vcp_rating": report.get("vcp_rating") or analysis.get("vcp_rating") or "Missing",
    }


def _proxy_vcp_score_from_evidence(
    report: dict,
    evidence: list[EvidenceSnapshot],
    profile: dict[str, Any] | None = None,
) -> float:
    profile = profile or _best_vcp_profile(evidence)
    if profile is not None:
        score = _score_vcp_profile(profile)
        if score > 0:
            return score

    technical = _technical_structure(evidence)
    price = _float_or_none(report.get("current_price"))
    if technical and price is not None:
        score = 0.0
        sma_20 = technical.get("sma_20")
        sma_50 = technical.get("sma_50")
        range_high = technical.get("range_high")
        range_low = technical.get("range_low")

        if sma_20 is not None:
            score += 2.0 if price >= sma_20 else 0.5
        if sma_50 is not None:
            score += 2.0 if price >= sma_50 else 0.5
        if sma_20 is not None and sma_50 is not None and sma_20 >= sma_50:
            score += 1.0
        if range_high is not None and price >= range_high * 0.95:
            score += 1.0
        if range_low is not None and range_high is not None and price >= (range_low + (range_high - range_low) * 0.5):
            score += 1.0
        return round(min(score, 10.0) * 2) / 2

    technical_rating = str(report.get("technical_rating") or "").lower()
    vcp_rating = str(report.get("vcp_rating") or "").lower()
    if "high-quality" in vcp_rating or "breakout" in technical_rating:
        return 7.5
    if "watchlist" in vcp_rating or "constructive" in technical_rating:
        return 5.0
    if "weak" in vcp_rating or "missing" in vcp_rating:
        return 2.0
    return 0.0


def _best_vcp_profile(evidence: list[EvidenceSnapshot]) -> dict[str, Any] | None:
    best_profile: dict[str, Any] | None = None
    best_weight = -1
    for item in evidence:
        if item.status != "fresh" or item.source_type not in {"technicals", "market"}:
            continue
        profile = _technical_profile(item)
        if profile is None:
            continue
        weight = len(profile.get("bars") or []) * 2
        weight += 3 if profile.get("sma_50") is not None else 0
        weight += 3 if profile.get("range_high") is not None else 0
        weight += 2 if profile.get("sma_20") is not None else 0
        weight += 1 if profile.get("price") is not None else 0
        if weight > best_weight:
            best_profile = profile
            best_weight = weight
    return best_profile


def _technical_profile(item: EvidenceSnapshot) -> dict[str, Any] | None:
    payload = item.payload
    if not isinstance(payload, dict):
        return None
    session = payload.get("session", {})
    if not isinstance(session, dict):
        session = {}
    bars = [bar for bar in payload.get("bars") or [] if isinstance(bar, dict)]
    profile = {
        "source_type": item.source_type,
        "price": _float_or_none(session.get("price") or payload.get("latest_close") or payload.get("price")),
        "sma_20": _float_or_none(payload.get("sma_20")),
        "sma_50": _float_or_none(payload.get("sma_50")),
        "sma_200": _float_or_none(payload.get("sma_200")),
        "range_low": _float_or_none(payload.get("range_low")),
        "range_high": _float_or_none(payload.get("range_high")),
        "bars": bars,
    }
    if profile["price"] is None and not bars and all(profile[field] is None for field in ("sma_20", "sma_50", "sma_200", "range_low", "range_high")):
        return None
    return profile


def _score_vcp_profile(profile: dict[str, Any]) -> float:
    price = _float_or_none(profile.get("price"))
    bars = [bar for bar in profile.get("bars") or [] if isinstance(bar, dict)]
    closes = [_float_or_none(bar.get("close")) for bar in bars]
    closes = [value for value in closes if value is not None]
    highs = [_float_or_none(bar.get("high")) for bar in bars]
    highs = [value for value in highs if value is not None]
    lows = [_float_or_none(bar.get("low")) for bar in bars]
    lows = [value for value in lows if value is not None]
    volumes = [_float_or_none(bar.get("volume")) for bar in bars]
    volumes = [value for value in volumes if value is not None]

    if price is None:
        return 0.0

    recent_window = 20 if len(closes) >= 20 else len(closes)
    prior_window = 20 if len(closes) >= 40 else max(len(closes) - recent_window, 0)
    recent_closes = closes[-recent_window:] if recent_window else []
    prior_closes = closes[-(recent_window + prior_window) : -recent_window] if prior_window else []
    recent_highs = highs[-recent_window:] if recent_window else []
    recent_lows = lows[-recent_window:] if recent_window else []
    prior_lows = lows[-(recent_window + prior_window) : -recent_window] if prior_window else []
    recent_volumes = volumes[-recent_window:] if recent_window else []
    prior_volumes = volumes[-(recent_window + prior_window) : -recent_window] if prior_window else []

    sma_20 = _float_or_none(profile.get("sma_20"))
    sma_50 = _float_or_none(profile.get("sma_50"))
    sma_200 = _float_or_none(profile.get("sma_200"))
    long_ma = sma_200
    if long_ma is None and len(closes) >= 100:
        long_ma = _moving_average(closes, 100)
    if long_ma is None and len(closes) >= 50:
        long_ma = _moving_average(closes, 50)

    recent_avg_close = _average_metric(recent_closes)
    prior_avg_close = _average_metric(prior_closes)
    recent_avg_range = _average_bar_range(bars[-recent_window:]) if recent_window else None
    prior_avg_range = _average_bar_range(bars[-(recent_window + prior_window) : -recent_window]) if prior_window else None
    recent_avg_volume = _average_metric(recent_volumes)
    prior_avg_volume = _average_metric(prior_volumes)
    recent_high = max(recent_highs) if recent_highs else _float_or_none(profile.get("range_high"))
    recent_low = min(recent_lows) if recent_lows else _float_or_none(profile.get("range_low"))
    pivot = _float_or_none(profile.get("range_high")) or recent_high

    score = 0.0
    if sma_50 is not None and price >= sma_50:
        score += 1.0
    if long_ma is not None and price >= long_ma:
        score += 1.0
    if sma_20 is not None and price >= sma_20:
        score += 1.0
    if sma_20 is not None and sma_50 is not None and sma_20 >= sma_50:
        score += 1.0
    if sma_50 is not None and long_ma is not None and sma_50 >= long_ma:
        score += 1.0
    if recent_avg_close is not None and prior_avg_close is not None and recent_avg_close >= prior_avg_close * 1.01:
        score += 1.0
    if recent_avg_range is not None and prior_avg_range is not None and recent_avg_range <= prior_avg_range * 0.92:
        score += 1.0
    if recent_lows and prior_lows and _average_metric(recent_lows) >= _average_metric(prior_lows):
        score += 1.0
    if recent_avg_volume is not None and prior_avg_volume is not None and recent_avg_volume <= prior_avg_volume * 0.92:
        score += 1.0
    if recent_high is not None and price >= recent_high * 0.92:
        score += 1.0
    if pivot is not None and price >= pivot * 0.95:
        score += 1.0
    if recent_avg_volume is not None and recent_volumes:
        latest_volume = recent_volumes[-1]
        if latest_volume >= recent_avg_volume * 1.1 and pivot is not None and price >= pivot * 0.98:
            score += 1.0
        elif latest_volume >= recent_avg_volume:
            score += 0.5

    # Pullback compression and price behavior can contribute a little when we have enough bars.
    pullback = _pullback_percent(price, recent_high or pivot)
    if pullback is not None and 2 <= pullback <= 8 and score < 10:
        score += 0.5
    if recent_low is not None and pivot is not None and price >= recent_low + (pivot - recent_low) * 0.6 and score < 10:
        score += 0.5

    return round(min(score, 10.0) * 2) / 2


def _pullback_percent(price: float | None, reference_high: float | None) -> float | None:
    if price is None or reference_high is None or reference_high <= 0:
        return None
    if price > reference_high:
        return 0.0
    return round((reference_high - price) / reference_high * 100, 2)


def _stage_label(vcp_score: float | int | None, profile: dict[str, Any] | None = None) -> str:
    score = vcp_score or 0
    if profile is not None:
        price = _float_or_none(profile.get("price"))
        highs = [_float_or_none(bar.get("high")) for bar in profile.get("bars") or [] if isinstance(bar, dict)]
        highs = [value for value in highs if value is not None]
        reference_high = max(highs[-10:]) if len(highs) >= 10 else (max(highs) if highs else None)
        if reference_high is None:
            reference_high = _float_or_none(profile.get("range_high"))
        pullback = _pullback_percent(price, reference_high)
        if pullback is not None:
            if pullback <= 5:
                return "Stage 2"
            if pullback <= 8:
                return "Stage 3"
            if pullback <= 15:
                return "Stage 4"
            return "Stage 5"
    if score >= 7:
        return "Stage 2"
    if score >= 5:
        return "Stage 3"
    if score >= 3:
        return "Stage 4"
    return "Stage 5"


def _tech_output_label(
    vcp_score: float | int | None,
    fallback: str,
    profile: dict[str, Any] | None = None,
) -> str:
    score = vcp_score or 0
    if profile is not None and _confirmed_breakout(profile):
        return "Confirmed breakout"
    if score >= 7.5:
        return "Strong VCP watchlist candidate"
    if score >= 5:
        return "VCP watchlist candidate"
    if score >= 3:
        return "Constructive base"
    if score > 0:
        return "Weak technical setup"
    return fallback or "Avoid"


def _technical_structure(evidence: list[EvidenceSnapshot]) -> dict[str, Any] | None:
    for item in evidence:
        if item.status != "fresh" or item.source_type not in {"technicals", "market"}:
            continue
        payload = item.payload
        if not isinstance(payload, dict):
            continue
        structure = {
            "sma_20": _float_or_none(payload.get("sma_20")),
            "sma_50": _float_or_none(payload.get("sma_50")),
            "range_low": _float_or_none(payload.get("range_low")),
            "range_high": _float_or_none(payload.get("range_high")),
            "bars": payload.get("bars"),
        }
        if any(value is not None for value in structure.values()):
            return structure
    return None


def _confirmed_breakout(profile: dict[str, Any]) -> bool:
    price = _float_or_none(profile.get("price"))
    if price is None:
        return False
    pivot = _float_or_none(profile.get("range_high"))
    if pivot is None:
        highs = [_float_or_none(bar.get("high")) for bar in profile.get("bars") or [] if isinstance(bar, dict)]
        highs = [value for value in highs if value is not None]
        pivot = max(highs) if highs else None
    if pivot is None or price <= pivot:
        return False
    volumes = [_float_or_none(bar.get("volume")) for bar in profile.get("bars") or [] if isinstance(bar, dict)]
    volumes = [value for value in volumes if value is not None]
    recent_avg_volume = _average_metric(volumes[-20:]) if len(volumes) >= 20 else _average_metric(volumes)
    latest_volume = volumes[-1] if volumes else None
    if recent_avg_volume is None or latest_volume is None:
        return False
    return latest_volume >= recent_avg_volume * 1.1


def _coerce_evidence_snapshots(items: list[Any]) -> list[EvidenceSnapshot]:
    snapshots: list[EvidenceSnapshot] = []
    for item in items:
        if isinstance(item, EvidenceSnapshot):
            snapshots.append(item)
            continue
        if isinstance(item, dict):
            payload = item.get("payload", {})
            if not isinstance(payload, dict):
                payload = {}
            warnings = item.get("warnings", [])
            if not isinstance(warnings, list):
                warnings = []
            snapshots.append(
                EvidenceSnapshot(
                    provider=str(item.get("provider", "")),
                    source_type=str(item.get("source_type", "")),
                    status=str(item.get("status", "")),
                    label=str(item.get("label", "")),
                    payload=payload,
                    url=item.get("url"),
                    warnings=[str(warning) for warning in warnings],
                    retrieved_at=str(item.get("retrieved_at") or utc_iso()),
                )
            )
    return snapshots


def _float_or_none(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _average_metric(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _average_bar_range(rows: list[dict[str, Any]]) -> float | None:
    ranges = []
    for row in rows:
        high = _float_or_none(row.get("high"))
        low = _float_or_none(row.get("low"))
        if high is None or low is None:
            continue
        ranges.append(high - low)
    return _average_metric(ranges)


def _moving_average(values: list[float], window: int) -> float | None:
    if len(values) < window:
        return None
    return _average_metric(values[-window:])
