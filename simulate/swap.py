from ast import Delete
import enum
from typing import Dict

class Token:
    Zil = "Zil"
    Token = None
    def __init__(self, addr: str) -> None:
        self.Token = addr

class Coins:
    def __init__(self, denom: Token, amount: int) -> None:
        self.denom = denom
        self.amount = amount

    def __repr__(self):
        return self.denom

class Pool:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def serialize(self):
        return {
            "x": self.x,
            "y": self.y
        }

    def __repr__(self):
        return "x: %i, y: %i" % (self.x, self.y)

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
ZERO_ADDR = "0x0000000000000000000000000000000000000000"

def unwrap_or_zero(wrapped: int = None) -> int:
    if (wrapped):
        return int(wrapped)
    return 0

def unpack_dict(map: dict, key: str):
    try:
        return map[key]
    except:
        return None

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
    exact_amount = swap.amount # _amount
    maybe_limit_amount = swap.limit
    after_fee = swap.fee

    if swap.pool == None:
        raise "MissingPool"

    pool = swap.pool
    amount = amount_for(pool, direction, exact_side, exact_amount, after_fee)
    is_limit = within_limits(amount, exact_side, maybe_limit_amount)

    if is_limit == False:
        raise "RequestedRatesCannotBeFulfilled"
    
    return [pool, amount]

def pool_empty(pool: Pool):
    return pool.x < ONE or pool.x < ONE

# FILEDS
pools = dict() #  Map ByStr20 Pool
balances = dict() # Map ByStr20 (Map ByStr20 Uint128)
total_contributions = dict()  # Map ByStr20 Uint128
output_after_fee = 9970
# FILEDS

def send(coins: Coins, to_address: str):
    amount = coins.amount
    if coins.denom == Token.Zil:
        print({
            "_eventname": "AddFunds",
            "to": to_address,
            "amount": amount
        })
        return

    print({
        "_eventname": "Transfer",
        "to": to_address,
        "amount": amount,
        "token": coins.denom
    })

def receive(coins: Coins):
    amount = coins.amount

    if coins.denom == Token.Zil:
        print({
            "_eventname": "Accept",
            "amount": amount
        })
        return
    
    print({
        "_eventname": "TransferFrom",
        "token": coins.denom,
        "from": "_sender",
        "to": ZERO_ADDR,
        "amount": amount
    })

def do_swap(
    pool: Pool,
    token_address: str,
    _input: Coins,
    output: Coins,
    input_from: str,
    output_to: str
):
    input_denom = _input.denom
    input_amount = _input.amount
    output_amount = output.amount

    if input_denom == Token.Zil:
        new_x = pool.x + input_amount
        new_y = pool.y - output_amount
        new_pool = Pool(new_x, new_y)
        pools[token_address] = new_pool
    elif input_denom == Token(token_address).Token:
        new_x = pool.x - output_amount
        new_y = pool.y + input_amount
        new_pool = Pool(new_x, new_y)
        pools[token_address] = new_pool
    
    if input_from != ZERO_ADDR:
        receive(_input)

    if output_to != ZERO_ADDR:
        send(output, output_to)

    print({
      "_eventname": "Swapped",
      "pool": token_address,
      "input": _input,
      "output": output
    })

def swap_using_zil(
    token_address : str,
    direction : int,
    exact_side : int,
    exact_amount : int,
    limit_amount : int
):
    after_fee = output_after_fee

    if token_address not in pools:
        raise "MissingPool"

    pool = pools[token_address]

    swap = Swap(exact_amount, limit_amount, after_fee, pool)
    swap.ExactSide = exact_side
    swap.SwapDirection = direction
    result = result_for(swap)

    pool = result[0]
    calculated_amount = result[1]
    token = Token(token_address)

    if exact_side == ExactSide.ExactInput:
        if direction == SwapDirection.ZilToToken:
            _input = Coins(Token.Zil, exact_amount)
            output = Coins(token.Token, calculated_amount)
            return do_swap(pool, token_address, _input, output, "_sender", "recipient_address")
        if direction == SwapDirection.TokenToZil:
            _input = Coins(token.Token, exact_amount)
            output = Coins(Token.Zil, calculated_amount)
            return do_swap(pool, token_address, _input, output, "_sender", "recipient_address")

    if exact_side == ExactSide.ExactOutput:
        if direction == SwapDirection.ZilToToken:
            _input = Coins(Token.Zil, calculated_amount)
            output = Coins(Token.Token, exact_amount)
            return do_swap(pool, token_address, _input, output, "_sender", "recipient_address")
        if direction == SwapDirection.TokenToZil:
            _input = Coins(token.Token, calculated_amount)
            output = Coins(Token.Zil, exact_amount)
            return do_swap(pool, token_address, _input, output, "_sender", "recipient_address")

    raise "msing exact_side"


def print_state():
    print("")
    print('###################################################################################################')
    print("")
    print(pools)
    print(balances)
    print(total_contributions)


def addLiquidity(
    token_address: str,
    min_contribution_amount: int,
    max_token_amount: int,
    _amount: int,
    _sender
):
    # TESTED
    if (token_address not in pools):
        new_pool = Pool(_amount, max_token_amount)
        pools[token_address] = new_pool
        print({
            "_eventname": "PoolCreated",
            "pool": token_address
        })
        balances[token_address] = dict()
        balances[token_address][_sender] = _amount
        total_contributions[token_address] = _amount
        print({
            "_eventname": "Mint",
            "pool": token_address,
            "address": _sender,
            "amount": _amount
        })
        return
    
    pool = pools[token_address]
    result = frac(_amount, pool.x, pool.y)

    # dY = dX * Y / X
    delta_y = result # removed one.

    mb_total_contribution = unpack_dict(total_contributions, token_address)
    total_contribution = unwrap_or_zero(mb_total_contribution)

    # (amt *  total_contribution) / x
    new_contribution = frac(_amount, pool.x, total_contribution)

    token_lte_max = delta_y <= max_token_amount
    contribution_gte_max = new_contribution >= min_contribution_amount
    within_limits = token_lte_max and contribution_gte_max

    if within_limits == False:
        raise "RequestedRatesCannotBeFulfilled delta_y: %i" % delta_y
    
    new_x = pool.x + _amount
    new_y = pool.y + delta_y

    new_pool = Pool(new_x, new_y)

    pools[token_address] = new_pool

    try:
        existing_balance = balances[token_address][_sender]
        new_balance = existing_balance + new_contribution
        balances[token_address][_sender] = new_balance
    except:
        balances[token_address] = dict()
        balances[token_address][_sender] = _amount

    new_total_contribution = total_contribution + new_contribution
    total_contributions[token_address] = new_total_contribution

    print({
        "_eventname": "Mint",
        "pool": token_address,
        "address": _sender,
        "amount": new_contribution
    })

def removeLiquidity(
    token_address : str,
    contribution_amount : int,
    min_zil_amount: int,
    min_token_amount : int,
    _sender
):
    # TESTED
    if token_address not in pools:
        raise "MissingPool"
    
    pool = pools[token_address]
    total_contribution = total_contributions[token_address]
    zil_amount = frac(contribution_amount, total_contribution, pool.x)
    token_amount = frac(contribution_amount, total_contribution, pool.y)

    zil_ok = zil_amount >= min_zil_amount
    token_ok = token_amount >= min_token_amount
    within_limits = zil_ok and token_ok

    if within_limits == False:
        raise "RequestedRatesCannotBeFulfilled"
    
    existing_balance = balances[token_address][_sender]
    
    new_balance = existing_balance - contribution_amount
    new_total_contribution = total_contribution - contribution_amount
    
    new_x = pool.x - zil_amount
    new_y = pool.y - token_amount
    new_pool = Pool(new_x, new_y)

    is_pool_now_empty = pool_empty(new_pool)

    if is_pool_now_empty:
        del pools[token_address]
        del balances[token_address]
        del total_contributions[token_address]
    else:
        pools[token_address] = new_pool;
        balances[token_address][_sender] = new_balance;
        total_contributions[token_address] = new_total_contribution
    
    print({
        "_eventname": "Burnt",
        "pool": token_address,
        "address": _sender,
        "amount": contribution_amount
    })

def swapExactZILForTokens(
    token_address: str,
    min_token_amount: int,
    _amount: int
):
    direction = SwapDirection.ZilToToken
    exact_side = ExactSide.ExactInput
    exact_amount = _amount
    limit_amount = min_token_amount

    swap_using_zil(token_address, direction, exact_side, exact_amount, limit_amount)

def swapExactTokensForZIL(
    token_address: str,
    token_amount: int,
    min_zil_amount : int
):
    direction = SwapDirection.TokenToZil
    exact_side = ExactSide.ExactInput
    exact_amount = token_amount
    limit_amount = min_zil_amount

    swap_using_zil(token_address, direction, exact_side, exact_amount, limit_amount)


def testLiquidity():
    tokenAddr = "0xee4caad51521da0f284b64c4d5e9d024bfa852e6"
    sender = "0x8617B72E22090f0c13167865147eC48a6dB788ff"
    token_amount = 50000000000
    zil_amount = 1000000000000000
    min_contribution_amount = 0

    addLiquidity(
        tokenAddr,
        min_contribution_amount,
        token_amount,
        zil_amount,
        sender
    )

    print_state()

    addLiquidity(
        tokenAddr,
        min_contribution_amount,
        token_amount,
        zil_amount,
        sender
    )

    print_state()

    removeLiquidity(
        tokenAddr,
        zil_amount,
        zil_amount,
        token_amount,
        sender
    )

    print_state()

def testSwap():
    tokenAddr = "0xee4caad51521da0f284b64c4d5e9d024bfa852e6"
    sender = "0x8617B72E22090f0c13167865147eC48a6dB788ff"
    token_amount = 50000000000
    zil_amount = 1000000000000000
    min_contribution_amount = 0

    addLiquidity(
        tokenAddr,
        min_contribution_amount,
        token_amount,
        zil_amount,
        sender
    )

    print_state()

    swapExactZILForTokens(tokenAddr, 5000000, 1000000000000)
    print_state()
    swapExactTokensForZIL(tokenAddr, 10000000000, 100000000)

    print_state()
testLiquidity()
# testSwap()
