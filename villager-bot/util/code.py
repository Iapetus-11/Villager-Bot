import traceback
import ast


def format_exception(e: Exception) -> str:
    return "".join(traceback.format_exception(type(e), e, e.__traceback__, 4)).replace("```", "｀｀｀")


async def execute_code(code: str, env: dict) -> object:
    code_parsed = ast.parse("async def _eval_code():\n" + "\n".join(f"    {i}" for i in code.splitlines()))

    def insert_returns(body):
        if isinstance(body[-1], ast.Expr):
            body[-1] = ast.Return(body[-1].value)
            ast.fix_missing_locations(body[-1])

        if isinstance(body[-1], ast.If):
            insert_returns(body[-1].body)
            insert_returns(body[-1].orelse)

        if isinstance(body[-1], ast.With):
            insert_returns(body[-1].body)

    insert_returns(code_parsed.body[0].body)

    exec(compile(code_parsed, filename="<ast>", mode="exec"), env)
    return await eval("_eval_code()", env)
