
async def execute_code(code: str, env: dict) -> object:
    code_parsed = ast.parse("async def _eval_code():\n" + "\n".join(f"    {i}" for i in code.splitlines()))
    code_final = code_parsed.body[0].body

    def insert_returns():
        if isinstance(code_final[-1], ast.Expr):
            code_final[-1] = ast.Return(code_final[-1].value)
            ast.fix_missing_locations(code_final[-1])

        if isinstance(code_final[-1], ast.If):
            insert_returns(code_final[-1].body)
            insert_returns(code_final[-1].orelse)

        if isinstance(code_final[-1], ast.With):
            insert_returns(code_final[-1].body)

    insert_returns()

    exec(compile(code_parsed, filename="<ast>", mode="exec"), env)
    return await eval("_eval_code()", env)
