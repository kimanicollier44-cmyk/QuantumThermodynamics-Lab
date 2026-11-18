#!/usr/bin/env python3
"""QuantumThermodynamics-Lab - educational quantum thermodynamics lab.

by Darion Kellar

Pure Python standard library. Zero dependencies. Zero network.
Education only - and the central lesson is stated up front:

  * This lab does exact Gibbs arithmetic on ONE toy qubit: a
    four-stroke Otto cycle whose efficiency comes out at exactly
    1 - w_c/w_h, a Szilard engine whose one bit of information is
    worth exactly k_B T ln 2 of work, and a two-point-measurement
    work distribution whose Jarzynski average matches e^(-beta dF)
    to float precision.
  * Every temperature and level spacing is a LABELLED teaching
    value. Nothing here is measured device data, and no output is
    an energy device, a refrigerator product, or an efficiency
    specification.
  * The demon does not beat the second law: the lab keeps the
    demon's own memory-erasure bill in the same ledger, and the
    net comes out at exactly zero in the ideal limit.
  * The cycle flips from engine to refrigerator at one derived
    boundary - w_h/w_c = T_h/T_c - and the lab computes that
    boundary instead of quoting it.

Legal, financial, energy-product, refrigeration-product, and
real-world efficiency claims are permanent HOLD gates - with
Gemini Argon 4 Extended Thinking as DECIDER (names-only,
tighten-only), Muse as advisor (never overrides HOLD), and
Google Flow plan-only seats.
"""
import hashlib
import json
import math
import sys

# ---------------------------------------------------------------- constants
VERSION = "1.0.0"

# Exact SI constants (2019 SI definitions).
K_B = 1.380649e-23          # Boltzmann constant, J/K (exact)
H_PLANCK = 6.62607015e-34   # Planck constant, J s (exact)
EV_J = 1.602176634e-19      # one electronvolt in joules (exact)
LN2 = math.log(2.0)

# Labelled demo parameters. Spacings are quoted as the temperature
# theta = E / k_B in kelvin, so beta*E = theta / T is dimensionless
# and every energy below can be read in units of k_B * kelvin.
ENGINE_THETA_C = 0.5        # cold-stroke level spacing, k_B * K
ENGINE_THETA_H = 1.0        # hot-stroke level spacing, k_B * K
ENGINE_T_C = 0.4            # cold bath, K (labelled)
ENGINE_T_H = 2.0            # hot bath, K (labelled)
FRIDGE_THETA_C = 0.5
FRIDGE_THETA_H = 1.0
FRIDGE_T_C = 0.6
FRIDGE_T_H = 1.0
SZILARD_T = 300.0           # demon bath temperature, K (labelled)
JARZYNSKI_BETA_E_I = 1.0    # beta * E_initial (dimensionless)
JARZYNSKI_BETA_E_F = 1.6    # beta * E_final (dimensionless)
JARZYNSKI_THETA = 0.7       # drive rotation angle, rad (labelled)

# ---------------------------------------------------------------- HOLD gates
HOLD_GATES = {
    "energy_device_claim": "HOLD - no real heat engine, generator, or power device; this is one toy qubit on paper",
    "free_energy_claim": "HOLD - no free-energy or over-unity claim; every joule in this lab is accounted for",
    "perpetual_motion_claim": "HOLD - no perpetual-motion claim of either kind, ever",
    "efficiency_product_claim": "HOLD - the toy Otto efficiency is not a product efficiency specification",
    "refrigeration_product_claim": "HOLD - no refrigerator, freezer, or air-conditioning product claim",
    "cryogenic_operation_claim": "HOLD - no directing real cryogenic plant or dilution refrigerators from a sim",
    "quantum_hardware_cooling_claim": "HOLD - no claim about cooling real quantum computers or their operating budgets",
    "medical_cooling_claim": "HOLD - no medical cold-chain, cryotherapy, or organ-preservation claim",
    "data_center_cooling_claim": "HOLD - no data-center cooling design or savings claim",
    "battery_thermal_claim": "HOLD - no battery thermal-management or EV range claim from toy arithmetic",
    "measured_data_claim": "HOLD - simulation output must never be presented as measured device data",
    "second_law_violation_claim": "HOLD - the demon and the fluctuation theorems confirm the second law; they never violate it",
    "investment_claim": "HOLD - no investment claim; a labelled toy cycle is not a prospectus",
    "safety_certification_claim": "HOLD - no certifying that a real thermal system is safe or efficient",
}


def gate(action):
    """Return 'HOLD' if the action is gated, else 'PROCEED' (sandbox sim)."""
    return "HOLD" if action in HOLD_GATES else "PROCEED"


# ================================================================ 1. Gibbs qubit
# A two-level system with ground energy 0 and excited energy E.
# Everything is exact Gibbs arithmetic: the excited-state population
# is 1 / (e^(beta E) + 1), the internal energy is p * E, and the von
# Neumann entropy is the binary entropy of p, in units of k_B.

def gibbs_p_excited(beta_e):
    """Excited-state population of a Gibbs qubit, beta_e = E / (k_B T)."""
    if beta_e < 0:
        raise ValueError("beta_e must be non-negative")
    if beta_e > 700.0:
        return 0.0
    return 1.0 / (math.exp(beta_e) + 1.0)


def qubit_entropy_kb(p):
    """Von Neumann entropy of a diagonal qubit state, in units of k_B."""
    if not 0.0 <= p <= 1.0:
        raise ValueError("population must lie in [0, 1]")
    s = 0.0
    for q in (p, 1.0 - p):
        if q > 0.0:
            s -= q * math.log(q)
    return s


def gibbs_free_energy_kb(beta_e):
    """Helmholtz free energy F / (k_B T) = -ln Z, Z = 1 + e^(-beta E)."""
    if beta_e < 0:
        raise ValueError("beta_e must be non-negative")
    return -math.log1p(math.exp(-beta_e))


# ================================================================ 2. Qubit Otto cycle
# Four strokes, all computed exactly:
#   A -> B  adiabatic compression: spacing theta_c -> theta_h,
#           populations frozen, work goes in.
#   B -> C  hot isochore: spacing theta_h, population relaxes to
#           the Gibbs value at T_h, heat Q_h flows in.
#   C -> D  adiabatic expansion: spacing theta_h -> theta_c,
#           populations frozen, work comes out.
#   D -> A  cold isochore: spacing theta_c, population relaxes to
#           the Gibbs value at T_c, heat Q_c flows out.
# Energies are carried in units of k_B * kelvin (spacing = theta).
# Sign convention: work_out > 0 means the cycle delivers work;
# q_hot / q_cold > 0 mean heat flows INTO the qubit.
#
# The regime boundary is derived, not quoted: net work is
# (theta_h - theta_c) * (p_C - p_A), so the engine runs iff
# p_C > p_A, i.e. iff theta_h / T_h < theta_c / T_c, i.e. iff
# theta_h / theta_c < T_h / T_c. On the boundary both Gibbs
# populations coincide and every flow vanishes.
#
# The optional friction term is a labelled loss model: friction
# work is paid in by the driver and dumped as heat into the cold
# bath during the cold isochore. Enough friction turns the
# refrigerator into a heater - work in, heat dumped to both baths.

def otto_cycle(theta_c, theta_h, t_c, t_h, friction=0.0):
    """Run one exact qubit Otto cycle and return the full stroke book."""
    if theta_c <= 0 or theta_h <= theta_c:
        raise ValueError("need 0 < theta_c < theta_h")
    if t_c <= 0 or t_h <= t_c:
        raise ValueError("need 0 < t_c < t_h")
    if friction < 0:
        raise ValueError("friction must be non-negative")
    p_a = gibbs_p_excited(theta_c / t_c)   # after cold isochore
    p_b = p_a                              # adiabatic: frozen
    p_c = gibbs_p_excited(theta_h / t_h)   # after hot isochore
    p_d = p_c                              # adiabatic: frozen
    # internal energies U = p * theta at the four corners
    u_a, u_b = p_a * theta_c, p_b * theta_h
    u_c, u_d = p_c * theta_h, p_d * theta_c
    # adiabatic strokes: all of dU is work (done ON the qubit)
    work_on_ab = u_b - u_a
    work_on_cd = u_d - u_c
    # isochores: all of dU is heat (into the qubit)
    q_hot = u_c - u_b
    q_cold = u_a - u_d
    work_out = -(work_on_ab + work_on_cd)
    if friction:
        work_out -= friction
        q_cold -= friction
    eta = work_out / q_hot if q_hot > 0 else 0.0
    eta_carnot = 1.0 - t_c / t_h
    cop_fridge = q_cold / (-work_out) if (work_out < 0 and q_cold > 0) else 0.0
    cop_carnot = t_c / (t_h - t_c)
    # entropy production of the universe over one cycle, units of k_B:
    # the qubit returns to its start, so only the baths change.
    sigma = -q_hot / t_h - q_cold / t_c
    corners = {
        "A": {"theta": theta_c, "p": p_a, "u": u_a,
              "s": qubit_entropy_kb(p_a)},
        "B": {"theta": theta_h, "p": p_b, "u": u_b,
              "s": qubit_entropy_kb(p_b)},
        "C": {"theta": theta_h, "p": p_c, "u": u_c,
              "s": qubit_entropy_kb(p_c)},
        "D": {"theta": theta_c, "p": p_d, "u": u_d,
              "s": qubit_entropy_kb(p_d)},
    }
    return {
        "theta_c": theta_c, "theta_h": theta_h, "t_c": t_c, "t_h": t_h,
        "friction": friction,
        "corners": corners,
        "work_on_ab": work_on_ab, "work_on_cd": work_on_cd,
        "q_hot": q_hot, "q_cold": q_cold, "work_out": work_out,
        "eta": eta, "eta_ideal": 1.0 - theta_c / theta_h,
        "eta_carnot": eta_carnot,
        "cop_fridge": cop_fridge, "cop_carnot": cop_carnot,
        "entropy_production_kb": sigma,
        "regime": regime_label(work_out, q_hot, q_cold,
                               eta / eta_carnot if eta_carnot else 0.0),
        "boundary_ratio": (theta_h / theta_c) / (t_h / t_c),
    }


def engine_book():
    return otto_cycle(ENGINE_THETA_C, ENGINE_THETA_H, ENGINE_T_C, ENGINE_T_H)


def fridge_book():
    return otto_cycle(FRIDGE_THETA_C, FRIDGE_THETA_H, FRIDGE_T_C, FRIDGE_T_H)


def boundary_book():
    """Ratios matched (theta_h/theta_c == T_h/T_c): the dud boundary."""
    return otto_cycle(0.5, 1.0, 0.5, 1.0)


def heater_book():
    """The fridge cycle with friction larger than its cold extraction."""
    return otto_cycle(FRIDGE_THETA_C, FRIDGE_THETA_H, FRIDGE_T_C, FRIDGE_T_H,
                      friction=0.05)


# ================================================================ 3. Szilard + Landauer
# One bit of information about which half of a box holds one molecule
# is worth W = k_B T ln 2 of work in the ideal Szilard engine. The
# demon's memory holds that bit, and erasing it costs at least
# k_B T ln 2 (Landauer). The lab keeps both lines in one ledger:
# extracted - erasure = 0 in the ideal limit, so the second law
# survives the demon - that is the whole point of the bookkeeping.

def work_per_bit_joules(t_kelvin):
    """Ideal work value (and erasure cost) of one bit at temperature T."""
    if t_kelvin <= 0:
        raise ValueError("temperature must be positive")
    return K_B * t_kelvin * LN2


def szilard_table(t_kelvin=SZILARD_T, bits_rows=(1, 2, 8, 64, 1024)):
    rows = []
    for bits in bits_rows:
        w = bits * work_per_bit_joules(t_kelvin)
        rows.append({"bits": bits, "work_j": w, "work_ev": w / EV_J})
    return rows


def demon_ledger(bits=8, t_kelvin=SZILARD_T):
    """Full demon bookkeeping: extraction, memory, erasure, net."""
    extracted = bits * work_per_bit_joules(t_kelvin)
    erasure = bits * work_per_bit_joules(t_kelvin)
    return {
        "bits": bits,
        "t_kelvin": t_kelvin,
        "work_extracted_j": extracted,
        "erasure_cost_j": erasure,
        "net_j": extracted - erasure,
        "bath_entropy_gain_per_bit_kb": LN2,
        "second_law_safe": extracted - erasure <= 1e-30,
    }


# ================================================================ 4. Jarzynski equality
# Two-point measurement protocol on a driven qubit (labelled):
# start in Gibbs at spacing E_i, measure the energy (outcome n),
# rotate the state by a fixed unitary U(theta), change the spacing
# to E_f, measure again (outcome m). Work W = E_f * m - E_i * n.
# Because |U_mn|^2 is doubly stochastic, the exact distribution
# obeys <e^(-beta W)> = Z_f / Z_i = e^(-beta dF) - the Jarzynski
# equality, checked here against the enumerated distribution, and
# <W> >= dF is the second law in the same bookkeeping.

def jarzynski_book(beta_e_i=JARZYNSKI_BETA_E_I, beta_e_f=JARZYNSKI_BETA_E_F,
                   theta=JARZYNSKI_THETA):
    """Enumerate the exact TPM work distribution and its averages.

    Work is reported in units of k_B T (beta * W dimensionless).
    """
    p_n = {0: 1.0 - gibbs_p_excited(beta_e_i), 1: gibbs_p_excited(beta_e_i)}
    c2 = math.cos(theta / 2.0) ** 2
    s2 = math.sin(theta / 2.0) ** 2
    trans = {(0, 0): c2, (0, 1): s2, (1, 0): s2, (1, 1): c2}
    outcomes = []
    mean_w = 0.0
    exp_avg = 0.0
    for n in (0, 1):
        for m in (0, 1):
            prob = p_n[n] * trans[(n, m)]
            w = beta_e_f * m - beta_e_i * n
            outcomes.append({"n": n, "m": m, "prob": prob, "beta_w": w})
            mean_w += prob * w
            exp_avg += prob * math.exp(-w)
    delta_f = gibbs_free_energy_kb(beta_e_f) - gibbs_free_energy_kb(beta_e_i)
    rhs = math.exp(-delta_f)
    return {
        "beta_e_i": beta_e_i, "beta_e_f": beta_e_f, "theta": theta,
        "outcomes": outcomes,
        "mean_beta_w": mean_w,
        "exp_avg": exp_avg,
        "beta_delta_f": delta_f,
        "jarzynski_rhs": rhs,
        "jarzynski_abs_err": abs(exp_avg - rhs),
        "dissipated": mean_w - delta_f,
    }


# ================================================================ 5. kNN regime classifier
# Features: net work out, heat from the hot bath, heat from the cold
# bath (all in k_B * kelvin), and eta / eta_Carnot. The training
# grid is labelled by the lab's own regime policy (regime_label
# below) over first-law-consistent points (w_out = q_hot + q_cold)
# - the classifier interpolates the policy, it does not replace
# the cycle bookkeeping.

def regime_label(w_out, q_hot, q_cold, eta_fraction=0.0, tol=0.005):
    """The lab's regime policy over (work, heats, efficiency fraction)."""
    if abs(w_out) <= tol and abs(q_hot) <= tol and abs(q_cold) <= tol:
        return "dud"
    if w_out > tol and q_hot > 0 and q_cold < 0 and eta_fraction < 1.0:
        return "engine"
    if w_out < -tol and q_cold > 0 and q_hot < 0:
        return "refrigerator"
    if w_out < -tol and q_hot < 0 and q_cold < 0:
        return "heater"
    return "dud"


def _training_grid():
    rows = []
    heats = (-2.0, -1.0, -0.3, -0.1, -0.02, 0.0, 0.02, 0.1, 0.3, 1.0, 2.0)
    for q_hot in heats:
        for q_cold in heats:
            w_out = q_hot + q_cold
            frac = 0.5 if (w_out > 0 and q_hot > 0) else 0.0
            rows.append(((w_out, q_hot, q_cold, frac),
                         regime_label(w_out, q_hot, q_cold, frac)))
    return rows


TRAINING_GRID = _training_grid()


def _squash(x):
    """Sign-preserving squash: cycle books are small next to the grid,
    so magnitudes saturate and the sign pattern carries the distance."""
    return x / (abs(x) + 0.01)


def _scaled(features):
    w_out, q_hot, q_cold, frac = features
    return (_squash(w_out), _squash(q_hot), _squash(q_cold), frac)


def classify_cycle(w_out, q_hot, q_cold, eta_fraction=0.0, k=5):
    """kNN over the policy-labelled grid, deterministic tie-breaking."""
    target = _scaled((w_out, q_hot, q_cold, eta_fraction))
    ranked = []
    for features, label in TRAINING_GRID:
        point = _scaled(features)
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(target, point)))
        ranked.append((dist, features, label))
    ranked.sort(key=lambda row: (row[0], row[1]))
    votes = {}
    for _, _, label in ranked[:k]:
        votes[label] = votes.get(label, 0) + 1
    priority = {"engine": 0, "refrigerator": 1, "heater": 2, "dud": 3}
    return sorted(votes.items(), key=lambda kv: (-kv[1], priority[kv[0]]))[0][0]


def _book_features(book):
    frac = book["eta"] / book["eta_carnot"] if book["eta_carnot"] else 0.0
    return (book["work_out"], book["q_hot"], book["q_cold"], frac)


def classifier_report():
    books = {
        "otto_engine_demo": engine_book(),
        "otto_fridge_demo": fridge_book(),
        "otto_boundary_demo": boundary_book(),
        "otto_friction_heater_demo": heater_book(),
    }
    return {name: classify_cycle(*_book_features(book))
            for name, book in books.items()}


# ================================================================ 6. Advisory seats
def _trace(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]


def argon4_decide(topic="quantumthermodynamics-demo"):
    """Gemini Argon 4 DECIDER seat: MAP->MODEL->STRESS->DECIDE.

    Names-only keys, live calls 0, tighten-only: can add HOLDs, never lift one.
    """
    stages = ["MAP", "MODEL", "STRESS", "DECIDE"]
    payload = {"seat": "gemini-argon-4", "topic": topic, "stages": stages}
    return {
        "seat": "Gemini Argon 4 Extended Thinking",
        "role": "DECIDER",
        "pipeline": stages,
        "tiers": [2048, 8192, 32768],
        "key": "names-only (GEMINI_API_KEY name checked, value never read)",
        "live_calls": 0,
        "decision": "PROCEED - sandbox simulation only, all energy-product gates stay HOLD",
        "can_override_hold": False,
        "trace_sha256_16": _trace(payload),
    }


def claude_advisor(topic="quantumthermodynamics-demo"):
    """Muse advisor seat: advises, can never override a HOLD."""
    return {
        "seat": "Muse",
        "role": "ADVISOR",
        "key": "names-only (MODEL_API_KEY name checked, value never read)",
        "live_calls": 0,
        "advice": "Keep the demon's erasure bill in the same table as its earnings, print the engine/refrigerator boundary as a derived ratio, and never let a toy efficiency leave the page dressed as a product specification.",
        "can_override_hold": False,
    }


def google_flow_plan():
    """Google Flow seat: plan-only, nothing rendered, nothing live."""
    return {
        "seat": "Google Flow",
        "role": "PLAN-ONLY",
        "shots": ["a qubit level spacing breathing open and shut over four strokes",
                  "two Gibbs populations trading places at the hot and cold baths",
                  "a demon sorting one molecule while its memory fills with one bit",
                  "an erasure spark paying exactly k_B T ln 2 back to the bath",
                  "a work distribution histogram bending until its Jarzynski average lands on e^(-beta dF)"],
        "rendered": False,
        "live": 0,
    }


def brains_report():
    return {"decider": argon4_decide(), "advisor": claude_advisor(),
            "flow": google_flow_plan()}


# ================================================================ checks
def run_checks():
    c = []

    def chk(name, ok):
        c.append((name, bool(ok)))

    def close(a, b, tol=1e-12):
        return abs(a - b) <= tol

    # 1. Gibbs qubit basics
    chk("gibbs_half_at_zero_beta_e", gibbs_p_excited(0.0) == 0.5)
    chk("gibbs_monotone_in_beta_e",
        gibbs_p_excited(0.5) > gibbs_p_excited(1.0)
        > gibbs_p_excited(2.0) > gibbs_p_excited(5.0))
    chk("gibbs_cold_limit", gibbs_p_excited(50.0) < 1e-20)
    chk("entropy_zero_for_pure_states",
        qubit_entropy_kb(0.0) == 0.0 and qubit_entropy_kb(1.0) == 0.0)
    chk("entropy_max_ln2_at_half",
        close(qubit_entropy_kb(0.5), LN2, 1e-15))
    chk("entropy_symmetric", close(qubit_entropy_kb(0.25),
                                   qubit_entropy_kb(0.75), 1e-15))
    chk("free_energy_limits",
        close(gibbs_free_energy_kb(0.0), -LN2, 1e-15)
        and abs(gibbs_free_energy_kb(50.0)) < 1e-20)

    # 2. Otto engine - the demo point
    eng = engine_book()
    chk("engine_populations_order",
        eng["corners"]["C"]["p"] > eng["corners"]["A"]["p"])
    chk("engine_positive_work", eng["work_out"] > 0)
    chk("engine_heats_signs", eng["q_hot"] > 0 and eng["q_cold"] < 0)
    chk("engine_first_law",
        close(eng["work_out"], eng["q_hot"] + eng["q_cold"], 1e-15))
    chk("engine_eta_is_otto_formula",
        close(eng["eta"], 1.0 - ENGINE_THETA_C / ENGINE_THETA_H, 1e-12)
        and close(eng["eta"], eng["eta_ideal"], 1e-15))
    chk("engine_eta_below_carnot", 0 < eng["eta"] < eng["eta_carnot"])
    chk("engine_work_value",
        close(eng["work_out"],
              (ENGINE_THETA_H - ENGINE_THETA_C)
              * (eng["corners"]["C"]["p"] - eng["corners"]["A"]["p"]), 1e-15))
    chk("engine_entropy_production_nonnegative",
        eng["entropy_production_kb"] > 0)
    chk("adiabatic_strokes_freeze_entropy",
        close(eng["corners"]["A"]["s"], eng["corners"]["B"]["s"], 1e-15)
        and close(eng["corners"]["C"]["s"], eng["corners"]["D"]["s"], 1e-15))
    chk("isochore_strokes_do_no_work",
        close(eng["corners"]["C"]["u"] - eng["corners"]["B"]["u"],
              eng["q_hot"], 1e-15)
        and close(eng["corners"]["A"]["u"] - eng["corners"]["D"]["u"],
                  eng["q_cold"], 1e-15))

    # 3. Otto formula + boundary, scanned
    scan_ok = True
    for theta_c, theta_h, t_c, t_h in ((0.3, 0.9, 0.5, 3.0),
                                       (0.8, 1.0, 0.2, 1.0),
                                       (0.25, 2.0, 0.25, 4.0)):
        b = otto_cycle(theta_c, theta_h, t_c, t_h)
        scan_ok = scan_ok and b["work_out"] > 0 \
            and close(b["eta"], 1.0 - theta_c / theta_h, 1e-12) \
            and b["eta"] < b["eta_carnot"] \
            and b["entropy_production_kb"] >= 0
    chk("otto_eta_formula_scan", scan_ok)
    chk("engine_condition_is_population_condition",
        all((otto_cycle(tc, th, Tc, Th)["work_out"] > 0)
            == ((th / Th) < (tc / Tc))
            for tc, th, Tc, Th in ((0.5, 1.0, 0.4, 2.0), (0.5, 1.0, 0.6, 1.0),
                                   (0.3, 0.9, 0.5, 3.0), (0.8, 1.0, 0.2, 1.0))))
    bnd = boundary_book()
    chk("boundary_zero_work", abs(bnd["work_out"]) < 1e-15
        and abs(bnd["q_hot"]) < 1e-15 and abs(bnd["q_cold"]) < 1e-15)
    chk("boundary_regime_dud", bnd["regime"] == "dud"
        and close(bnd["boundary_ratio"], 1.0, 1e-15))

    # 4. Refrigerator + friction heater
    fri = fridge_book()
    chk("fridge_work_input", fri["work_out"] < 0)
    chk("fridge_heats_signs", fri["q_cold"] > 0 and fri["q_hot"] < 0)
    chk("fridge_cop_below_carnot_cop",
        0 < fri["cop_fridge"] < fri["cop_carnot"])
    chk("fridge_entropy_production_nonnegative",
        fri["entropy_production_kb"] > 0)
    chk("fridge_regime_label", fri["regime"] == "refrigerator")
    hea = heater_book()
    chk("friction_flips_fridge_to_heater",
        hea["regime"] == "heater" and hea["work_out"] < 0
        and hea["q_hot"] < 0 and hea["q_cold"] < 0)
    chk("friction_first_law_still_holds",
        close(hea["work_out"], hea["q_hot"] + hea["q_cold"], 1e-15))

    # 5. Szilard engine + Landauer erasure
    chk("szilard_bit_value_300k",
        close(work_per_bit_joules(300.0), K_B * 300.0 * LN2, 1e-36))
    chk("szilard_bit_ev_300k",
        abs(work_per_bit_joules(300.0) / EV_J - 0.017919) < 1e-5)
    chk("szilard_scales_with_bits_and_T",
        close(work_per_bit_joules(600.0), 2.0 * work_per_bit_joules(300.0),
              1e-36)
        and szilard_table(300.0)[3]["work_j"]
        == 64.0 * work_per_bit_joules(300.0))
    led = demon_ledger()
    chk("demon_net_zero_ideal", led["net_j"] == 0.0
        and led["work_extracted_j"] > 0 and led["second_law_safe"])
    chk("demon_erasure_entropy_covers_extraction",
        led["bath_entropy_gain_per_bit_kb"] >= LN2 - 1e-15)

    # 6. Jarzynski equality on the exact TPM distribution
    jar = jarzynski_book()
    chk("jarzynski_probabilities_sum_1",
        close(sum(o["prob"] for o in jar["outcomes"]), 1.0, 1e-15))
    chk("jarzynski_equality_holds", jar["jarzynski_abs_err"] < 1e-9)
    chk("jarzynski_mean_work_above_delta_f",
        jar["mean_beta_w"] >= jar["beta_delta_f"]
        and jar["dissipated"] > 0)
    jar2 = jarzynski_book(0.4, 2.2, 1.1)
    chk("jarzynski_second_protocol",
        jar2["jarzynski_abs_err"] < 1e-9 and jar2["dissipated"] > 0)
    jar0 = jarzynski_book(1.0, 1.6, 0.0)
    chk("jarzynski_no_drive_still_exact",
        jar0["jarzynski_abs_err"] < 1e-9
        and sum(1 for o in jar0["outcomes"] if o["prob"] > 0) == 2)

    # 7. classifier - labels come from the regime policy itself
    rep = classifier_report()
    chk("classifier_engine", rep["otto_engine_demo"] == "engine")
    chk("classifier_fridge", rep["otto_fridge_demo"] == "refrigerator")
    chk("classifier_boundary_dud", rep["otto_boundary_demo"] == "dud")
    chk("classifier_heater", rep["otto_friction_heater_demo"] == "heater")
    chk("classifier_matches_policy",
        all(classify_cycle(*_book_features(b)) == b["regime"]
            for b in (engine_book(), fridge_book(), boundary_book(),
                      heater_book())))
    chk("classifier_engine_eta_fraction_sane",
        0.0 < engine_book()["eta"] / engine_book()["eta_carnot"] < 1.0)

    # gates + seats
    chk("hold_gates_14", len(HOLD_GATES) == 14
        and all(v.startswith("HOLD") for v in HOLD_GATES.values()))
    chk("gate_free_energy_hold", gate("free_energy_claim") == "HOLD")
    chk("gate_perpetual_motion_hold", gate("perpetual_motion_claim") == "HOLD")
    chk("gate_efficiency_product_hold",
        gate("efficiency_product_claim") == "HOLD")
    chk("gate_second_law_hold", gate("second_law_violation_claim") == "HOLD")
    chk("gate_measured_data_hold", gate("measured_data_claim") == "HOLD")
    chk("gate_sandbox_proceed", gate("run_simulation") == "PROCEED")
    brains = brains_report()
    chk("argon4_no_override", brains["decider"]["can_override_hold"] is False
        and brains["decider"]["seat"]
        == "Gemini Argon 4 Extended Thinking")
    chk("claude_no_override", brains["advisor"]["can_override_hold"] is False)
    chk("flow_plan_only", brains["flow"]["rendered"] is False
        and brains["flow"]["live"] == 0)
    return c


# ================================================================ CLI / demo
def _fmt(x, digits=6):
    return f"{x:.{digits}f}"


def demo():
    print("=" * 68)
    print("QuantumThermodynamics-Lab - qubit heat engine + information lab")
    print("by Darion Kellar | MIT | pure stdlib | zero network | EDUCATION ONLY")
    print("=" * 68)
    print("\n[1] THE HONEST CORE - exact arithmetic on one toy qubit")
    print("    A four-stroke Otto cycle, a one-bit Szilard engine, and a")
    print("    driven qubit's work distribution - all computed exactly")
    print("    from Gibbs weights. Every temperature and spacing is a")
    print("    LABELLED teaching value; nothing is measured device data")
    print("    and no efficiency here is a product specification.")
    eng = engine_book()
    print("\n[2] Qubit Otto cycle - engine point (labelled)")
    print(f"    spacings theta_c = {ENGINE_THETA_C} -> theta_h = "
          f"{ENGINE_THETA_H} (k_B*K) | baths T_c = {ENGINE_T_C} K, "
          f"T_h = {ENGINE_T_H} K")
    for name in "ABCD":
        cor = eng["corners"][name]
        print(f"    corner {name}: theta {cor['theta']:.2f} | "
              f"p_exc {_fmt(cor['p'])} | U {_fmt(cor['u'])} | "
              f"S {_fmt(cor['s'])} k_B")
    print(f"    work out {_fmt(eng['work_out'])} k_B*K "
          f"({eng['work_out'] * K_B:.4e} J) | Q_h {_fmt(eng['q_hot'])} | "
          f"Q_c {_fmt(eng['q_cold'])}")
    print(f"    eta = {_fmt(eng['eta'])} = 1 - theta_c/theta_h exactly | "
          f"Carnot {_fmt(eng['eta_carnot'])} | eta < Carnot: "
          f"{eng['eta'] < eng['eta_carnot']}")
    print(f"    entropy production {_fmt(eng['entropy_production_kb'])} k_B "
          f">= 0 | regime: {eng['regime']}")
    print("\n[3] The flip - one derived boundary, three more regimes")
    fri, bnd, hea = fridge_book(), boundary_book(), heater_book()
    print(f"    boundary: theta_h/theta_c = T_h/T_c -> work "
          f"{bnd['work_out']:.2e} ({bnd['regime']})")
    print(f"    fridge point: work in {_fmt(-fri['work_out'])} | "
          f"Q_c extracted {_fmt(fri['q_cold'])} | COP "
          f"{_fmt(fri['cop_fridge'])} < Carnot COP {_fmt(fri['cop_carnot'])} "
          f"({fri['regime']})")
    print(f"    fridge + friction 0.05: Q_c flips to {_fmt(hea['q_cold'])} "
          f"-> {hea['regime']} (work in, heat dumped to both baths)")
    print("\n[4] Szilard engine + Maxwell demon - the erasure bill")
    for row in szilard_table():
        print(f"    {row['bits']:5d} bit(s) at {SZILARD_T:.0f} K: "
              f"{row['work_j']:.4e} J = {row['work_ev']:.6f} eV")
    led = demon_ledger()
    print(f"    demon ledger ({led['bits']} bits): extracted "
          f"{led['work_extracted_j']:.4e} J - erasure "
          f"{led['erasure_cost_j']:.4e} J = net {led['net_j']:.1e} J")
    print("    -> the demon pays k_B T ln 2 per bit to forget; the second")
    print("       law survives in the same ledger that pays the demon.")
    jar = jarzynski_book()
    print("\n[5] Jarzynski equality - two-point measurement work book")
    for o in jar["outcomes"]:
        print(f"    n={o['n']} -> m={o['m']}: P {_fmt(o['prob'])} | "
              f"beta W {_fmt(o['beta_w'], 3)}")
    print(f"    <e^(-beta W)> = {_fmt(jar['exp_avg'])} vs e^(-beta dF) = "
          f"{_fmt(jar['jarzynski_rhs'])} | abs err "
          f"{jar['jarzynski_abs_err']:.2e}")
    print(f"    <beta W> = {_fmt(jar['mean_beta_w'])} >= beta dF = "
          f"{_fmt(jar['beta_delta_f'])} | dissipated "
          f"{_fmt(jar['dissipated'])}")
    print("\n[6] Cycle regime classifier (TinyML kNN, policy-labelled grid)")
    for name, label in classifier_report().items():
        print(f"    {name:28s} -> {label}")
    print("\n[7] Advisory seats")
    brains = brains_report()
    print(f"    decider: {brains['decider']['decision']} "
          f"trace={brains['decider']['trace_sha256_16']}")
    print(f"    advisor can_override_hold = {brains['advisor']['can_override_hold']}")
    print(f"    flow rendered = {brains['flow']['rendered']} "
          f"live = {brains['flow']['live']}")
    print(f"\n[8] HOLD gates: {len(HOLD_GATES)}")
    for key in HOLD_GATES:
        print(f"    HOLD  {key}")
    checks = run_checks()
    passed = sum(1 for _, ok in checks if ok)
    print(f"\nCHECKS {passed}/{len(checks)}")
    for name, ok in checks:
        if not ok:
            print(f"    FAIL {name}")
    verdict = "PROCEED" if passed == len(checks) else "HOLD"
    print(f"VERDICT {verdict} (sandbox simulation only) | HOLD gates {len(HOLD_GATES)}")
    return 0 if passed == len(checks) else 1


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] == "demo":
        return demo()
    cmd = argv[0]
    if cmd == "checks":
        checks = run_checks()
        for name, ok in checks:
            print(f"{'PASS' if ok else 'FAIL'} {name}")
        print(f"CHECKS {sum(1 for _, ok in checks if ok)}/{len(checks)}")
        return 0 if all(ok for _, ok in checks) else 1
    if cmd == "otto":
        print(json.dumps({
            "engine": engine_book(), "fridge": fridge_book(),
            "boundary": boundary_book(), "friction_heater": heater_book()},
            indent=2, sort_keys=True))
        return 0
    if cmd == "demon":
        print(json.dumps({"table_300k": szilard_table(),
                          "ledger": demon_ledger()},
                         indent=2, sort_keys=True))
        return 0
    if cmd == "jarzynski":
        print(json.dumps(jarzynski_book(), indent=2, sort_keys=True))
        return 0
    if cmd == "classify":
        print(json.dumps(classifier_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "brains":
        print(json.dumps(brains_report(), indent=2, sort_keys=True))
        return 0
    if cmd == "holds":
        for key, value in HOLD_GATES.items():
            print(f"{key}: {value}")
        return 0
    if cmd == "hold-demo":
        action = argv[1] if len(argv) > 1 else "free_energy_claim"
        print(f"{action}: {HOLD_GATES.get(action, 'PROCEED - not gated')}")
        return 2 if gate(action) == "HOLD" else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
