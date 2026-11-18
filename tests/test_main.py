"""Tests for QuantumThermodynamics-Lab: Otto, Szilard, Jarzynski, gates."""
import math

import pytest

import main as m


# ---- Gibbs qubit
def test_gibbs_half_at_zero():
    assert m.gibbs_p_excited(0.0) == 0.5


def test_gibbs_monotone_and_cold_limit():
    vals = [m.gibbs_p_excited(x) for x in (0.5, 1.0, 2.0, 5.0)]
    assert vals == sorted(vals, reverse=True)
    assert m.gibbs_p_excited(50.0) < 1e-20


def test_gibbs_rejects_negative():
    with pytest.raises(ValueError):
        m.gibbs_p_excited(-0.1)


def test_entropy_pure_and_max():
    assert m.qubit_entropy_kb(0.0) == 0.0
    assert m.qubit_entropy_kb(1.0) == 0.0
    assert m.qubit_entropy_kb(0.5) == pytest.approx(math.log(2.0), abs=1e-15)


def test_entropy_symmetric():
    assert m.qubit_entropy_kb(0.25) == pytest.approx(
        m.qubit_entropy_kb(0.75), abs=1e-15)


def test_free_energy_limits():
    assert m.gibbs_free_energy_kb(0.0) == pytest.approx(-math.log(2.0))
    assert abs(m.gibbs_free_energy_kb(50.0)) < 1e-20


# ---- Otto cycle: engine
def test_engine_eta_formula():
    b = m.engine_book()
    assert b["eta"] == pytest.approx(1.0 - 0.5 / 1.0, abs=1e-12)
    assert b["eta"] == pytest.approx(b["eta_ideal"], abs=1e-15)


def test_engine_below_carnot_and_positive_work():
    b = m.engine_book()
    assert b["work_out"] > 0
    assert 0 < b["eta"] < b["eta_carnot"]


def test_engine_first_law():
    b = m.engine_book()
    assert b["work_out"] == pytest.approx(b["q_hot"] + b["q_cold"], abs=1e-15)
    assert b["q_hot"] > 0 and b["q_cold"] < 0


def test_engine_entropy_production_and_frozen_adiabats():
    b = m.engine_book()
    assert b["entropy_production_kb"] > 0
    assert b["corners"]["A"]["s"] == pytest.approx(b["corners"]["B"]["s"])
    assert b["corners"]["C"]["s"] == pytest.approx(b["corners"]["D"]["s"])


def test_otto_eta_formula_scan():
    for tc, th, Tc, Th in ((0.3, 0.9, 0.5, 3.0), (0.8, 1.0, 0.2, 1.0),
                           (0.25, 2.0, 0.25, 4.0)):
        b = m.otto_cycle(tc, th, Tc, Th)
        assert b["work_out"] > 0
        assert b["eta"] == pytest.approx(1.0 - tc / th, abs=1e-12)
        assert b["eta"] < b["eta_carnot"]
        assert b["entropy_production_kb"] >= 0


def test_otto_rejects_bad_geometry():
    with pytest.raises(ValueError):
        m.otto_cycle(1.0, 0.5, 0.4, 2.0)
    with pytest.raises(ValueError):
        m.otto_cycle(0.5, 1.0, 2.0, 0.4)


# ---- Otto cycle: boundary, fridge, heater
def test_boundary_is_dud():
    b = m.boundary_book()
    assert abs(b["work_out"]) < 1e-15
    assert b["regime"] == "dud"
    assert b["boundary_ratio"] == pytest.approx(1.0)


def test_fridge_book():
    b = m.fridge_book()
    assert b["work_out"] < 0
    assert b["q_cold"] > 0 and b["q_hot"] < 0
    assert 0 < b["cop_fridge"] < b["cop_carnot"]
    assert b["regime"] == "refrigerator"
    assert b["entropy_production_kb"] > 0


def test_friction_heater():
    b = m.heater_book()
    assert b["regime"] == "heater"
    assert b["q_hot"] < 0 and b["q_cold"] < 0 and b["work_out"] < 0
    assert b["work_out"] == pytest.approx(b["q_hot"] + b["q_cold"], abs=1e-15)


# ---- Szilard + Landauer
def test_szilard_bit_value():
    assert m.work_per_bit_joules(300.0) == pytest.approx(
        m.K_B * 300.0 * math.log(2.0), rel=1e-12)
    assert m.work_per_bit_joules(300.0) / m.EV_J == pytest.approx(
        0.017919, abs=1e-5)


def test_szilard_table_scaling():
    rows = m.szilard_table(300.0)
    assert rows[0]["bits"] == 1
    assert rows[3]["work_j"] == 64.0 * m.work_per_bit_joules(300.0)


def test_demon_ledger_net_zero():
    led = m.demon_ledger()
    assert led["work_extracted_j"] > 0
    assert led["net_j"] == 0.0
    assert led["second_law_safe"] is True


# ---- Jarzynski
def test_jarzynski_equality():
    j = m.jarzynski_book()
    assert j["jarzynski_abs_err"] < 1e-9
    assert sum(o["prob"] for o in j["outcomes"]) == pytest.approx(1.0)


def test_jarzynski_second_law():
    j = m.jarzynski_book()
    assert j["mean_beta_w"] >= j["beta_delta_f"]
    assert j["dissipated"] > 0


def test_jarzynski_second_protocol_and_no_drive():
    assert m.jarzynski_book(0.4, 2.2, 1.1)["jarzynski_abs_err"] < 1e-9
    j0 = m.jarzynski_book(1.0, 1.6, 0.0)
    assert j0["jarzynski_abs_err"] < 1e-9
    assert sum(1 for o in j0["outcomes"] if o["prob"] > 0) == 2


# ---- classifier
def test_classifier_report():
    rep = m.classifier_report()
    assert rep["otto_engine_demo"] == "engine"
    assert rep["otto_fridge_demo"] == "refrigerator"
    assert rep["otto_boundary_demo"] == "dud"
    assert rep["otto_friction_heater_demo"] == "heater"


def test_classifier_matches_policy():
    for book in (m.engine_book(), m.fridge_book(), m.boundary_book(),
                 m.heater_book()):
        assert m.classify_cycle(*m._book_features(book)) == book["regime"]


# ---- gates + seats
def test_hold_gates_14():
    assert len(m.HOLD_GATES) == 14
    assert all(v.startswith("HOLD") for v in m.HOLD_GATES.values())


def test_gate_specifics():
    assert m.gate("free_energy_claim") == "HOLD"
    assert m.gate("perpetual_motion_claim") == "HOLD"
    assert m.gate("second_law_violation_claim") == "HOLD"
    assert m.gate("run_simulation") == "PROCEED"


def test_seats_cannot_override():
    b = m.brains_report()
    assert b["decider"]["seat"] == "Gemini Argon 4 Extended Thinking"
    assert b["decider"]["can_override_hold"] is False
    assert b["advisor"]["can_override_hold"] is False
    assert b["flow"]["rendered"] is False and b["flow"]["live"] == 0


def test_checks_all_pass():
    checks = m.run_checks()
    assert all(ok for _, ok in checks), [n for n, ok in checks if not ok]


def test_hold_demo_exit_code():
    assert m.main(["hold-demo", "free_energy_claim"]) == 2
    assert m.main(["hold-demo", "run_simulation"]) == 0
