_amount = 1000000000000
pool = {
  "zil_reserve": 1000000000000000,
  "zrc_reserve": 50000000000
}
fee = 9970
FEE_DENOM = 10000

def swap_token_for_zil():
  numerator = _amount * pool["zrc_reserve"]
  denominator = pool["zil_reserve"] + _amount
  result = numerator // denominator

  print("numerator", numerator)
  print("denominator", denominator)
  print("result", result)

  pool["zil_reserve"] += _amount
  pool["zrc_reserve"] -= result

  print(pool)

def swap_zil_for_token():
  numerator = (pool["zrc_reserve"] * _amount) * FEE_DENOM
  denominator = (pool["zil_reserve"] - _amount) * fee
  result = numerator // denominator

  pool["zil_reserve"] += _amount
  pool["zrc_reserve"] -= result

  print("numerator", numerator)
  print("denominator", denominator)
  print("result", result)

  print(pool)

def frac(d: int, x: int, y: int) -> int:
    # TESTED
    # computes the amount of the fraction x / d that is in y
    d_times_y = d * y
    return d_times_y // x

swap_zil_for_token()
# swap_token_for_zil()

