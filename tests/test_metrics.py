from app import epley_e1rm, linear_forecast

def test_epley_basic():
    # 200 x 5 ≈ 233.3
    assert round(epley_e1rm(200, 5), 1) == 233.3

def test_forecast_needs_two_points():
    assert linear_forecast([200]) == []            # 1 point => no forecast
    assert len(linear_forecast([200, 210])) == 4   # 2 points => 4 weeks projected

def test_forecast_increasing_trend():
    fc = linear_forecast([200, 210, 220])
    assert fc[0] >= 220  # shouldn’t dip below last actual point
