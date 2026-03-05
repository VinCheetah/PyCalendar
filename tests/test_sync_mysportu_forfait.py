from pycalendar.mysportu.models import MatchState
from scripts.sync_mysportu import normalize_state_for_sync, is_cancelled_for_sync


def test_normalize_state_for_sync_maps_forfait_to_termine():
    assert normalize_state_for_sync(MatchState.FORFAIT) == MatchState.TERMINE


def test_is_cancelled_for_sync_excludes_forfait():
    assert is_cancelled_for_sync(MatchState.REPORTE)
    assert is_cancelled_for_sync(MatchState.ANNULE)
    assert not is_cancelled_for_sync(MatchState.FORFAIT)
