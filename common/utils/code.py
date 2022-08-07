import ast
import traceback


def format_exception(e: Exception) -> str:
    return "".join(traceback.format_exception(type(e), e, e.__traceback__, 4))


async def execute_code(code: str, env: dict) -> object:
    def insert_returns(body):
        try:
            if isinstance(body[-1], ast.Expr):
                body[-1] = ast.Return(body[-1].value)
                ast.fix_missing_locations(body[-1])

            if isinstance(body[-1], ast.If):
                insert_returns(body[-1].body)
                insert_returns(body[-1].orelse)

            if isinstance(body[-1], ast.With):
                insert_returns(body[-1].body)
        except IndexError:
            pass

    func_content = "\n".join(f"    {line}" for line in code.strip("\n").splitlines())
    code = f"async def _execute_code():\n{func_content}"

    parsed = ast.parse(code)
    insert_returns(parsed.body[0].body)  # type: ignore

    exec(compile(parsed, filename="<ast>", mode="exec"), env)
    return await eval("_execute_code()", env)
