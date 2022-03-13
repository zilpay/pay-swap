_amount = 1000000000000
pool = {
  "zil_reserve": 1000000000000000,
  "zrc_reserve": 50000000000
}
fee = 9970
FEE_DENOM = 10000

def swap_token_for_zil():
  input_amount_after_fee = _amount * fee
  numerator = input_amount_after_fee * pool["zrc_reserve"]
  denominator = (pool["zil_reserve"] * FEE_DENOM) + input_amount_after_fee
  result = numerator // denominator

  print("input_amount_after_fee", input_amount_after_fee)
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

swap_zil_for_token()
# swap_token_for_zil()
