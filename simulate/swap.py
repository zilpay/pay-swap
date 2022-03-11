import enum
from typing import Dict

class Zil:
    pass

class Token:
    def __init__(self, addr: str) -> None:
        self.Token = addr

class Denom:
    Zil = Zil

    def __init__(self, token: str):
        self.Token = Token(token)

class Coins:
    def __init__(self, denom: Denom, amount: int) -> None:
        self.denom = denom
        self.amount = amount

class Pool:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def serialize(self):
        return {
            "x": self.x,
            "y": self.y
        }

class SwapDirection(enum.Enum):
    ZilToToken = 0
    TokenToZil = 1

class ExactSide(enum.Enum):
    ExactInput = 0
    ExactOutput = 1

class Swap:
    SwapDirection: int
    ExactSide: int

    #exact amt, limit amt, after fee amt
    def __init__(self, amount: int, limit: int, fee: int, pool: Pool = None) -> None:
        self.amount = amount
        self.limit = limit
        self.fee = fee
        self.pool = pool

ZERO = 0
ONE = 1
FEE_DENOM = 10000 # fee denominated in basis points (1 b.p. = 0.01%)

def unwrap_or_zero(wrapped: int = None) -> int:
    if (wrapped):
        return int(wrapped)
    return 0

def frac(d: int, x: int, y: int) -> int:
    # TESTED
    # computes the amount of the fraction x / d that is in y
    d_times_y = d * y
    return d_times_y // x

def output_for(
    input_amount: int,
    input_reserve: int,
    output_reserve: int,
    after_fee: int
):
    # TESTED!
    # computes the output that should be taken from the output reserve
    # when the given input amount is added to the input reserve.
    input_amount_after_fee = input_amount * after_fee
    numerator = input_amount_after_fee * output_reserve
    denominator = input_reserve * FEE_DENOM + input_amount_after_fee
    result = numerator // denominator

    return result

def input_for(
    output_amount: int,
    input_reserve: int,
    output_reserve: int,
    after_fee: int
):
    # TESTED
    # computes the input that should be given to the input reserve
    # when the given output amount is removed from the output reserve.

    numerator = (input_reserve * output_amount) * FEE_DENOM
    denominator = (output_reserve - output_amount) * after_fee
    result = numerator // denominator

    return result

def amount_for(
    pool: Pool,
    direction: int,
    exact_side: int, # ExactSide
    exact_amount: int,
    after_fee: int
):
    # TESTED
    # computes the corresponding input or output amount for
    # the given exact output or input amount, pool, and direction
    zil_reserve = pool.x
    token_reserve = pool.y

    def calc(exact: int):
        if (exact == ExactSide.ExactInput):
            return output_for

        if (exact == ExactSide.ExactOutput):
            return input_for
        
        raise "Incorrect exact"

    if direction == SwapDirection.ZilToToken:
        return calc(exact_side)(exact_amount, zil_reserve, token_reserve, after_fee)

    if (direction == SwapDirection.TokenToZil):
        return calc(exact_side)(exact_amount, token_reserve, zil_reserve, after_fee)
    
    raise "Incorect direction";

def within_limits(result_amount: int, exact_side: int, maybe_limit_amount: int = None):
    # TESTED
    # checks whether the result amount is within the user provided
    # limit amount, which is dependent on whether the output or input
    # result was the one being computed.

    if (maybe_limit_amount == None):
        return True
    
    limit_amount = int(maybe_limit_amount)

    if (exact_side == ExactSide.ExactInput):
        # we are given an exact input and are computing the output,
        # which should be greater or equal to the limit
        return result_amount > limit_amount

    if (exact_side == ExactSide.ExactOutput):
        # we are given an exact output and are computing the input,
        # which should be lower or equal to the limit.
        return limit_amount > result_amount

    raise "Incorrect exact"

def result_for(swap: Swap):
    # TESTED
    # computes the resultant amount for the given swap.
    direction = swap.SwapDirection
    exact_side = swap.ExactSide
    exact_amount = swap.amount
    maybe_limit_amount = swap.limit
    after_fee = swap.fee

    if swap.pool == None:
        raise "MissingPool"

    pool = swap.pool
    amount = amount_for(pool, direction, exact_side, exact_amount, after_fee)
    is_limit = within_limits(amount, exact_side, maybe_limit_amount)

    print(is_limit, amount, exact_side, maybe_limit_amount)

    if is_limit == False:
        raise "RequestedRatesCannotBeFulfilled"
    
    return [pool.serialize(), amount]


# FILEDS
pools = dict() #  Map ByStr20 Pool
balances = dict() # Map ByStr20 (Map ByStr20 Uint128)
total_contributions = dict()  # Map ByStr20 Uint128
# FILEDS

def addLiquidity(
    token_address : str,
    min_contribution_amount : int,
    max_token_amount : int,
    _amount: int,
    _sender = "0xee4caad51521da0f284b64c4d5e9d024bfa852e6"
):
    if (token_address not in pools):
        new_pool = Pool(_amount, max_token_amount)
        pools[token_address] = new_pool
        print({
            "_eventname": "PoolCreated",
            "pool": token_address
        })
        balances[token_address] = dict()
        balances[token_address][_sender] = _amount;
        total_contributions[token_address] = _amount;
        print({
            "_eventname": "Mint",
            "pool": token_address,
            "address": _sender,
            "amount": _amount
        })


def removeLiquidity():
    pass

addLiquidity(
    "0xee4caad51521da0f284b64c4d5e9d024bfa852e6",
    1000,
    5000,
    4000
)

print(pools)
print(balances)
print(total_contributions)