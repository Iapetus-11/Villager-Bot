def add(addends):
    return sum([parse(addend) for addend in addends])


def subtract(subtrahends):
    subtrahends = [parse(subtrahend) for subtrahend in subtrahends]
    difference = subtrahends.pop(0)

    for subtrahend in subtrahends:
        difference -= subtrahend

    return difference


def multiply(multiplicands):
    multiplicands = [parse(multiplicand) for multiplicand in multiplicands]
    product = 1

    for multiplicand in multiplicands:
        product *= multiplicand

    return product


def divide(divisors):
    divisors = [parse(divisor) for divisor in divisors]
    quotient = divisors.pop(0)

    for divisor in divisors:
        quotient /= divisor

    return quotient


def exponentiate(indexes):
    indexes = [parse(index) for index in indexes]
    power = indexes.pop(0)

    for index in indexes:
        power **= index

    return power


def parse(s):
    # fixes issue of code to split at * messing with ** for exponentiation
    s = str(s).replace(" ", "").replace("*", "x").replace("xx", "**").replace("×", "x").replace("÷", "/")

    # reverse order of operations here because it's resolved bottom up cause it's a tree
    split = s.split("+")
    if len(split) > 1:
        return add(split)

    split = s.split("-")
    if len(split) > 1:
        return subtract(split)

    split = s.split("x")
    if len(split) > 1:
        return multiply(split)

    split = s.split("/")
    if len(split) > 1:
        return divide(split)

    split = s.split("**")
    if len(split) > 1:
        return exponentiate(split)

    return float(s)  # if there's no more parsing that can be done
