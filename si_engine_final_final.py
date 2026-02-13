#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SI 3.2 / SI 3.4 / 10-10 — FULL MANUAL MARKET ENGINE (FINAL-FINAL)
==================================================================

What this is:
- Manual-input market structure engine (NO chart access required)
- Keeps your ORIGINAL base dependency chain formula as the spine
- Adds: SI 3.4 gates + psychology patch (reflex/pilot) + 10/10 selection (fatigue)
- Outputs:
  - Selection: GREEN / YELLOW / RED
  - SI Call: HIGH / LOW / LATE
  - Path probs: Range / Flush / Impulse
  - Optional: p(tag L*) and p(extract L*) + time window + falsifier

What this is NOT:
- Not financial advice
- Not a promise of outcomes
- Not “market access” code

USAGE
-----
1) Print the copy/paste AI prompt:
   python si_engine_final_final.py prompt

2) Run manual numbers:
   python si_engine_final_final.py manual \
     --asset GOOGL --event OTHER \
     --p0 320 --p5 322 --p15 321 --p30 325 \
     --touches 1 --rho 0.35 --E 0.8 --TA 0.5 --f_exec 0.7 \
     --target 327 --t_remaining 45 --teff 0.7 --phi 0.7

Inputs you need during trading:
- P0, P5, P15, P30 (optional P60)
- touches (48h) integer
- rho (0..1) reflex index (wicky -> closer to 1)
- E (0..1) exit quality
- TA (0..1) trauma activation
- f_exec (0..1) execution friction
Optional:
- target (L*) + minutes remaining
- teff, phi proxies (0..1 each)
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import math


# ============================================================
# 0) YOUR BASE FORMULA (kept explicitly as the master spine)
# ============================================================

BASE_FORMULA_TEXT = r"""
P_real = [ E * ( ω * (SQo / (1 + SQi)) ) *
          ( (((Rv * K) * (SI * (IQ + EQ) * C)) / (αL + βA + N + H)) ^ ℓ )
         ] + W − M
"""


# ============================================================
# 1) PARAMETERS
# ============================================================

@dataclass(frozen=True)
class Params:
    # SI 3.4 thresholds
    reflex_threshold: float = 0.0005      # 0.05%: defines direction from r5
    reverse_threshold: float = 0.0008     # 0.08%: reversal invalidates
    hold_threshold: float = 0.0002        # 0.02%: must hold in direction
    late_reclaim: float = 0.0006          # 0.06%: reclaim strength for LATE

    # Trend label for scoring only (optional)
    trend_threshold_60m: float = 0.004    # 0.40%

    # Extraction modifiers
    tau_time_decay: float = 0.015         # conceptual decay per minute

    # Probability clamps
    p_floor: float = 0.05
    p_ceiling: float = 0.95


# ============================================================
# 2) CALIBRATION PRIORS
# ============================================================

CALIBRATION: Dict[str, Dict[str, float]] = {
    "DEFAULT": {"HIGH": 0.905, "LOW": 0.10, "LATE": 0.50},
    "CPI":     {"HIGH": 0.92,  "LOW": 0.08, "LATE": 0.55},
    "NFP":     {"HIGH": 0.88,  "LOW": 0.12, "LATE": 0.45},
    "FOMC":    {"HIGH": 0.85,  "LOW": 0.15, "LATE": 0.50},
}


# ============================================================
# 3) CORE HELPERS
# ============================================================

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))

def sigmoid(x: float) -> float:
    if x >= 60:
        return 1.0
    if x <= -60:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))

def ret(p0: float, p1: float) -> float:
    return (p1 - p0) / p0


# ============================================================
# 4) BASE FORMULA AS AN OPERATIONAL SPINE (structural scalars)
# ============================================================

@dataclass(frozen=True)
class BaseVars:
    # Multipliers / gates
    E: float = 0.8
    omega: float = 0.7
    Rv: float = 0.7
    K: float = 0.7
    SI: float = 0.7
    IQ: float = 0.7
    EQ: float = 0.7
    C: float = 0.7

    # Orientation / inflation
    SQo: float = 0.7
    SQi: float = 0.4

    # Drags
    L: float = 0.6
    A: float = 0.6
    N: float = 0.6
    H: float = 0.6

    # Weights + load
    alpha: float = 0.6
    beta: float = 0.4
    ell: float = 1.0

    # Floor / cost
    W: float = 0.2
    M: float = 0.2

def p_real_proxy(v: BaseVars) -> float:
    """
    Faithful structural rendering of your dependency chain.
    Output clamped to 0..1 for stability.
    """
    def c01(x: float) -> float:
        return clamp(x, 0.0, 1.0)

    def cpos(x: float, floor: float = 1e-6) -> float:
        return max(float(x), floor)

    E = c01(v.E)
    omega = c01(v.omega)
    SQo = cpos(v.SQo)
    SQi = max(0.0, float(v.SQi))

    Rv = c01(v.Rv)
    K = c01(v.K)
    SI = c01(v.SI)
    IQ = c01(v.IQ)
    EQ = c01(v.EQ)
    C = c01(v.C)

    alpha = cpos(v.alpha)
    beta = cpos(v.beta)
    L = max(0.0, float(v.L))
    A = max(0.0, float(v.A))
    N = max(0.0, float(v.N))
    H = max(0.0, float(v.H))

    ell = cpos(v.ell, 0.1)
    W = max(0.0, float(v.W))
    M = max(0.0, float(v.M))

    orientation_block = omega * (SQo / (1.0 + SQi))
    numerator = (Rv * K) * (SI * (IQ + EQ) * C)
    denom = (alpha * L) + (beta * A) + N + H
    core = cpos(numerator) / cpos(denom)

    powered = core ** ell
    p_real = (E * orientation_block * powered) + W - M

    return clamp(p_real, 0.0, 1.0)


# ============================================================
# 5) SI 3.4 EVENT-GATE CLASSIFIER (manual prices)
# ============================================================

def direction_from_r5(r5: float, p: Params) -> int:
    if abs(r5) < p.reflex_threshold:
        return 0
    return 1 if r5 > 0 else -1

def gate_state(r: float, direction: int, p: Params) -> str:
    if direction == 0:
        return "CHOP"

    if direction == 1:
        if r <= -p.reverse_threshold:
            return "BROKEN"
        if r >= p.hold_threshold:
            return "HELD"
        return "CHOP"

    if direction == -1:
        if r >= p.reverse_threshold:
            return "BROKEN"
        if r <= -p.hold_threshold:
            return "HELD"
        return "CHOP"

    return "CHOP"

def si34_call(g1: str, g2: str, direction: int, r30: float, r60: Optional[float], p: Params, strict_late: bool = False) -> str:
    """
    strict_late=False: if no P60, LATE is provisional (still returned as LATE).
    strict_late=True:  if no P60, LATE is downgraded to LOW.
    """
    if g1 == "HELD" and g2 == "HELD":
        return "HIGH"

    if direction != 0 and g1 != "HELD" and g2 == "HELD" and abs(r30) >= p.late_reclaim:
        if r60 is None:
            return "LOW" if strict_late else "LATE"
        return "LATE" if gate_state(r60, direction, p) == "HELD" else "LOW"

    return "LOW"

def calibrated_prob(event_type: str, call: str) -> float:
    et = str(event_type).upper()
    table = CALIBRATION.get(et, CALIBRATION["DEFAULT"])
    return float(table.get(call, CALIBRATION["DEFAULT"][call]))


# ============================================================
# 6) PSYCHOLOGY PATCH (observable-only)
# ============================================================

def omega_from_rho(rho: float) -> float:
    return clamp(1.0 - rho, 0.0, 1.0)

def pilot_penalized_prob(base_prob: float, omega_m: float, p: Params) -> float:
    prob = base_prob * (omega_m + 0.10)
    return clamp(prob, p.p_floor, p.p_ceiling)


# ============================================================
# 7) 10/10 SELECTION LAYER (fatigue)
# ============================================================

def fatigue_lambda_from_touches(touches: int) -> float:
    t = max(0, int(touches))
    mapping = {0: 1.00, 1: 1.00, 2: 0.90, 3: 0.75, 4: 0.60, 5: 0.45}
    return clamp(mapping.get(t, 0.30), 0.30, 1.00)

def selection_gate_green(pi: float, lam: float, rho: float) -> str:
    # RED = unsafe / low integrity
    if pi < 0.50 or lam < 0.60 or rho > 0.70:
        return "RED"
    # YELLOW = cautious / partial integrity
    if pi < 0.62 or lam < 0.75 or rho > 0.55:
        return "YELLOW"
    # GREEN = healthiest structure
    return "GREEN"


# ============================================================
# 8) SI 3.2 PATH PROBABILITIES (exactly 3 paths)
# ============================================================

def normalize3(a: float, b: float, c: float) -> Tuple[float, float, float]:
    s = max(a + b + c, 1e-9)
    return a / s, b / s, c / s

def path_probs(
    pi: float,
    g1: str,
    g2: str,
    direction: int,
    omega_m: float,
    E: float,
    TA: float
) -> Tuple[float, float, float]:
    """
    Returns probabilities for exactly 3 paths:
      - Range / digestion
      - Flush / cascade
      - Impulse / reprice

    Fixes applied:
    - No walrus operator.
    - direction is actually used (impulse penalty when unclear).
    """
    # base rates prevent fantasy
    base_range, base_flush, base_impulse = 0.50, 0.30, 0.20

    fit_impulse = 1.00 if (g1 == "HELD" and g2 == "HELD" and direction != 0) else 0.35
    fit_flush   = 1.00 if (g1 == "BROKEN" or g2 == "BROKEN") else 0.40
    fit_range   = 1.00 if (g1 == "CHOP" and g2 == "CHOP") else 0.55

    strength_range = pi * base_range   * fit_range   * (0.75 + 0.25 * (1 - omega_m))
    strength_flush = pi * base_flush   * fit_flush   * (0.60 + 0.40 * (1 - E)) * (0.70 + 0.30 * TA)
    strength_imp   = pi * base_impulse * fit_impulse * (0.60 + 0.40 * omega_m) * (0.70 + 0.30 * E)

    # penalty when direction is unclear (prevents false impulse confidence)
    if direction == 0:
        strength_imp *= 0.65

    return normalize3(strength_range, strength_flush, strength_imp)


# ============================================================
# 9) TAG + EXTRACTION PROBABILITIES (target L*)
# ============================================================

def tag_probability(p_impulse: float, pi: float, teff_delta: float, phi_delta: float, rvh: float) -> float:
    # conceptual “readiness” score
    x = pi * teff_delta * phi_delta * rvh
    # squash; threshold around 0.25; scale 8 for sharper discrimination
    return clamp(p_impulse * sigmoid(8.0 * (x - 0.25)), 0.0, 1.0)

def extraction_probability(p_tag: float, tau: float, minutes_remaining: float, f_exec: float, p: Params) -> float:
    t_rem = max(0.0, float(minutes_remaining))
    elapsed = max(0.0, 60.0 - t_rem)
    decay = math.exp(-tau * elapsed)
    p_ex = p_tag * decay * clamp(f_exec, 0.0, 1.0)
    return clamp(p_ex, p.p_floor, p.p_ceiling)


# ============================================================
# 10) ONE MANUAL RUN (live use)
# ============================================================

@dataclass(frozen=True)
class ManualRunInput:
    asset: str
    event: str

    p0: float
    p5: float
    p15: float
    p30: float
    p60: Optional[float]

    touches_48h: int
    rho: float          # 0..1
    E: float            # 0..1
    TA: float           # 0..1
    f_exec: float       # 0..1

    target: Optional[float]
    minutes_remaining: float

    teff_delta: float   # 0..1
    phi_delta: float    # 0..1

    strict_late: bool   # whether LATE requires P60 confirmation

def reason_sentence(select: str, call: str, g1: str, g2: str, rho: float, lam: float) -> str:
    if select == "RED":
        return f"Structure is not healthy enough (Λ={lam:.2f} and/or ρ={rho:.2f}), so skip even if it looks active."
    if call == "HIGH":
        return "The move survived the first reversal attempt (15m) and still holds at 30m, so the tape is structurally valid."
    if call == "LATE":
        return "The first move didn’t hold, but a strong reclaim exists by 30m, so continuation is possible but lower-integrity."
    if g1 == "BROKEN" or g2 == "BROKEN":
        return "The move reversed hard versus the first direction, which is classic trap/whipsaw structure."
    return "The first 30 minutes did not form a stable hold, so the tape is not giving a clean structure."

def run_manual(inp: ManualRunInput, p: Params = Params()) -> str:
    # returns
    r5  = ret(inp.p0, inp.p5)
    r15 = ret(inp.p0, inp.p15)
    r30 = ret(inp.p0, inp.p30)
    r60 = ret(inp.p0, inp.p60) if inp.p60 is not None else None

    # gates
    direction_int = direction_from_r5(r5, p)
    direction_txt = "Unclear" if direction_int == 0 else ("Up" if direction_int == 1 else "Down")
    g1 = gate_state(r15, direction_int, p)
    g2 = gate_state(r30, direction_int, p)
    call = si34_call(g1, g2, direction_int, r30, r60, p, strict_late=inp.strict_late)

    # psychology
    rho = clamp(inp.rho, 0.0, 1.0)
    omega_m = omega_from_rho(rho)

    # calibration prob × pilot
    base_prob = calibrated_prob(inp.event, call)
    prob_trend = pilot_penalized_prob(base_prob, omega_m, p)

    # fatigue
    lam = fatigue_lambda_from_touches(inp.touches_48h)

    # proxies mapping to base spine
    rv_proxy = 1.0 if (g1 == "HELD" and g2 == "HELD") else (0.65 if g2 == "HELD" else 0.40)
    k_proxy = clamp((1.0 - rho) * (0.75 + 0.25 * rv_proxy), 0.0, 1.0)
    sqi_proxy = clamp(0.30 + 0.50 * rho + (1.0 - lam) * 0.40, 0.0, 1.5)

    base = BaseVars(
        E=clamp(inp.E, 0.0, 1.0),
        omega=omega_m,
        Rv=rv_proxy,
        K=k_proxy,
        # neutral constants in market mode (you can expose as args later if you want)
        SI=0.7, IQ=0.7, EQ=0.7, C=0.8,
        SQo=0.7,
        SQi=sqi_proxy,
        L=0.6, A=0.5, N=0.6, H=clamp(inp.TA, 0.0, 1.0),
        alpha=0.6, beta=0.4,
        ell=1.0,
        W=0.2, M=0.2
    )
    P_real = p_real_proxy(base)

    # Predictability Π
    pi = clamp(prob_trend * lam * P_real * (1.0 - 0.50 * rho), 0.0, 1.0)

    # selection
    select = selection_gate_green(pi, lam, rho)

    # paths
    pr, pf, pim = path_probs(
        pi=pi, g1=g1, g2=g2, direction=direction_int, omega_m=omega_m,
        E=clamp(inp.E, 0.0, 1.0), TA=clamp(inp.TA, 0.0, 1.0)
    )

    # optional target module
    tag_out = None
    extract_out = None
    window = None
    falsifier = None

    if inp.target is not None:
        rvh = rv_proxy
        teff = clamp(inp.teff_delta, 0.0, 1.0)
        phi  = clamp(inp.phi_delta, 0.0, 1.0)

        p_tag = tag_probability(pim, pi, teff, phi, rvh)
        p_ex  = extraction_probability(p_tag, p.tau_time_decay, inp.minutes_remaining, inp.f_exec, p)

        tag_out = p_tag
        extract_out = p_ex

        if pim >= max(pr, pf):
            window = "Early window (next 15–45 min) if it’s going to print."
        elif pr >= max(pf, pim):
            window = "No clean window (likely range). Any print is usually late / noisy."
        else:
            window = "Danger window (flush risk). Any print is unstable."

        falsifier = "If the move cannot stay HELD into the next gate (30m), treat the thesis as invalid for this window."

    # format output
    lines = []
    lines.append("=== SI 3.2 / SI 3.4 / 10-10 — MANUAL RUN (FINAL-FINAL) ===")
    lines.append(f"Asset: {inp.asset} | Event: {inp.event.upper()}")
    lines.append("")
    lines.append(f"BASE FORMULA (spine): {BASE_FORMULA_TEXT.strip()}")
    lines.append("")
    lines.append(f"Selection (10/10): {select}   (Π={pi:.3f} | P_real={P_real:.3f} | Λ={lam:.2f} | ρ={rho:.2f})")
    lines.append("")
    lines.append(f"SI Call: {call}")
    lines.append(f"Direction: {direction_txt}")
    lines.append(f"Gate1 (T+15): {g1}")
    lines.append(f"Gate2 (T+30): {g2}")
    lines.append("")
    rline = f"Returns: r5={r5*100:.2f}% | r15={r15*100:.2f}% | r30={r30*100:.2f}%"
    if r60 is not None:
        rline += f" | r60={r60*100:.2f}%"
    lines.append(rline)
    lines.append(f"Pilot (ωᵐ): {omega_m:.2f} | Reflex (ρ): {rho:.2f} | Fatigue (Λ): {lam:.2f}")
    lines.append(f"Prob(next hour trendable): {prob_trend*100:.1f}%  (calibration × pilot)")
    lines.append("")
    lines.append(f"Path probs: Range {pr*100:.1f}% / Flush {pf*100:.1f}% / Impulse {pim*100:.1f}%")

    if inp.target is not None and tag_out is not None and extract_out is not None:
        lines.append("")
        lines.append(f"Target L*: {inp.target}")
        lines.append(f"p(tag L*): {tag_out*100:.1f}%")
        lines.append(f"p(extract L*): {extract_out*100:.1f}%   (tag × time-decay × execution)")
        lines.append(f"Most likely time window: {window}")
        lines.append(f"Falsifier: {falsifier}")

    lines.append("")
    lines.append("Reason: " + reason_sentence(select, call, g1, g2, rho, lam))
    return "\n".join(lines)


# ============================================================
# 11) COPY/PASTE PROMPT GENERATOR
# ============================================================

def generate_ai_prompt() -> str:
    p = Params()
    return f"""COPY/PASTE: SI 3.2 / SI 3.4 / 10-10 — MANUAL EVENT ENGINE (AI PROMPT)

ROLE
You are a market structure classifier. You do NOT give financial advice.
You do NOT tell me to buy/sell. You only classify the tape and output probabilities.

BASE SPINE (DO NOT REMOVE)
{BASE_FORMULA_TEXT.strip()}

INPUT I WILL PROVIDE
Asset:
Event type: CPI / NFP / FOMC / OTHER
Prices: P0, P5, P15, P30 (optional P60)
Touches (48h): integer
Reflex index ρ (0..1): 0=solid bodies, 1=wicky machine tape (if unknown, use 0.50)
Exit quality E (0..1): if unknown, use 0.80
Trauma activation TA (0..1): if unknown, use 0.50
Execution friction F_exec (0..1): if unknown, use 0.70
Optional: Target L* and minutes remaining in the window
Optional proxies: ΔTeff (0..1) and ΔΦ (0..1) (if unknown, use 0.70 / 0.70)

PARAMETERS (DO NOT CHANGE)
reflex_threshold={p.reflex_threshold}
reverse_threshold={p.reverse_threshold}
hold_threshold={p.hold_threshold}
late_reclaim={p.late_reclaim}
tau_time_decay={p.tau_time_decay}

CALIBRATION PRIORS
DEFAULT: HIGH 0.905 | LOW 0.10 | LATE 0.50
CPI: HIGH 0.92 | LOW 0.08 | LATE 0.55
NFP: HIGH 0.88 | LOW 0.12 | LATE 0.45
FOMC: HIGH 0.85 | LOW 0.15 | LATE 0.50

STEPS
1) Returns:
r5=(P5-P0)/P0
r15=(P15-P0)/P0
r30=(P30-P0)/P0
r60=(P60-P0)/P0 if provided

2) Direction from r5:
If abs(r5) < reflex_threshold -> direction=0 (Unclear)
Else direction=+1 if r5>0 else -1

3) GateState(rX):
If direction=0 -> CHOP
If direction=+1:
  if rX <= -reverse_threshold -> BROKEN
  elif rX >= hold_threshold -> HELD
  else CHOP
If direction=-1:
  if rX >= reverse_threshold -> BROKEN
  elif rX <= -hold_threshold -> HELD
  else CHOP

Gate1=GateState(r15)
Gate2=GateState(r30)

4) SI 3.4 Call:
If Gate1=HELD and Gate2=HELD -> HIGH
Else if Gate1!=HELD and Gate2=HELD and abs(r30)>=late_reclaim:
  if P60 provided: LATE only if GateState(r60)=HELD else LOW
  if P60 not provided: LATE (provisional) OR LOW if you are using strict mode
Else LOW

5) Psychology (observable):
ωm = 1 - ρ

6) Fatigue:
Λ by touches:
0/1->1.00, 2->0.90, 3->0.75, 4->0.60, 5->0.45, 6+->0.30

7) Trend probability:
base_prob = calibration[event][CALL]
prob_trend = base_prob * (ωm + 0.10), clamped 5%..95%

8) Map to base spine (market proxies):
Rv_proxy = 1.0 if HELD/HELD else 0.65 if Gate2 HELD else 0.40
K_proxy = (1-ρ) * (0.75 + 0.25*Rv_proxy)
SQi_proxy = 0.30 + 0.50*ρ + (1-Λ)*0.40
Compute P_real from the base equation (structural scalars).

9) Predictability Π:
Π = prob_trend * Λ * P_real * (1 - 0.50*ρ)

10) 10/10 Selection verdict:
RED if Π<0.50 or Λ<0.60 or ρ>0.70
YELLOW if Π<0.62 or Λ<0.75 or ρ>0.55
GREEN otherwise

11) Path probs (exactly 3):
Range / Flush / Impulse using Π + gate fit + ωm + E + TA
(use base rates 50/30/20 then weight by fit, then normalize)

12) If Target L* given:
Rv_h = Rv_proxy
p(tag)=p(Impulse)*σ(Π*ΔTeff*ΔΦ*Rv_h)
p(extract)=p(tag)*exp(-tau*(60-min_remaining))*F_exec
Output most likely window + 1 falsifier sentence.

OUTPUT FORMAT (STRICT)
Selection: GREEN/YELLOW/RED + (Π, P_real, Λ, ρ)
Call: HIGH/LOW/LATE
Direction: Up/Down/Unclear
Gate1: HELD/BROKEN/CHOP
Gate2: HELD/BROKEN/CHOP
Returns: r5 r15 r30 (r60 if provided) as %
Prob(next hour trendable): __%
Path probs: Range __% / Flush __% / Impulse __%
If target given: p(tag) __% | p(extract) __% | window | falsifier
One-sentence reason (gate-based only)
"""


# ============================================================
# 12) CLI
# ============================================================

def cmd_prompt(_: argparse.Namespace) -> None:
    print(generate_ai_prompt())

def cmd_manual(args: argparse.Namespace) -> None:
    inp = ManualRunInput(
        asset=args.asset,
        event=args.event,
        p0=float(args.p0),
        p5=float(args.p5),
        p15=float(args.p15),
        p30=float(args.p30),
        p60=float(args.p60) if args.p60 is not None else None,
        touches_48h=int(args.touches),
        rho=float(args.rho),
        E=float(args.E),
        TA=float(args.TA),
        f_exec=float(args.f_exec),
        target=float(args.target) if args.target is not None else None,
        minutes_remaining=float(args.t_remaining),
        teff_delta=float(args.teff),
        phi_delta=float(args.phi),
        strict_late=bool(args.strict_late),
    )
    print(run_manual(inp))

def build_cli() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="SI 3.2/3.4/10-10 Manual Market Engine (Final-Final)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("prompt", help="Print the copy/paste AI prompt protocol")
    p1.set_defaults(func=cmd_prompt)

    m = sub.add_parser("manual", help="Run manual gates from your P0/P5/P15/P30 numbers")
    m.add_argument("--asset", required=True)
    m.add_argument("--event", required=True, choices=["CPI", "NFP", "FOMC", "OTHER"])
    m.add_argument("--p0", required=True, type=float)
    m.add_argument("--p5", required=True, type=float)
    m.add_argument("--p15", required=True, type=float)
    m.add_argument("--p30", required=True, type=float)
    m.add_argument("--p60", required=False, type=float, default=None)

    m.add_argument("--touches", required=False, type=int, default=1, help="touches of the level in last 48h")
    m.add_argument("--rho", required=False, type=float, default=0.50, help="reflex index 0..1 (wickiness)")
    m.add_argument("--E", required=False, type=float, default=0.80, help="exit quality 0..1")
    m.add_argument("--TA", required=False, type=float, default=0.50, help="trauma activation 0..1")
    m.add_argument("--f_exec", required=False, type=float, default=0.70, help="execution friction 0..1")

    m.add_argument("--target", required=False, type=float, default=None, help="optional target L*")
    m.add_argument("--t_remaining", required=False, type=float, default=45.0, help="minutes remaining in your window")
    m.add_argument("--teff", required=False, type=float, default=0.70, help="ΔTeff proxy 0..1")
    m.add_argument("--phi", required=False, type=float, default=0.70, help="ΔΦ proxy 0..1")

    m.add_argument("--strict_late", required=False, action="store_true", help="require P60 confirmation for LATE")

    m.set_defaults(func=cmd_manual)
    return ap

def main() -> None:
    ap = build_cli()
    args = ap.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()


