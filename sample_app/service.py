def helper(x: int) -> str:
    if x > 0:
        return "positive"
    return "non-positive"


def run(flag: bool) -> None:
    if flag:
        print(helper(1))
    else:
        print(helper(-1))
