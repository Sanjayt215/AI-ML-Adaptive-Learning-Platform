"""
Isolated Worker Process for Sandboxed Code Execution.
Executed strictly in a standalone subprocess with Python isolated flags (-I -s).
Part of AutoLearn KT-RL Phase 11 Security & Sandboxing Architecture.
"""

from __future__ import annotations

import ast
import json
import math
import sys
import time
from typing import Any, Dict, List

# Block dangerous modules from sys.modules
FORBIDDEN_MODULES = {
    "os", "sys", "subprocess", "socket", "shutil", "builtins", "requests",
    "http", "urllib", "ctypes", "threading", "multiprocessing", "pty",
    "posix", "winreg", "_winapi", "msvcrt", "signal", "asyncio",
}

FORBIDDEN_NAMES = {
    "__import__", "open", "eval", "exec", "compile", "globals", "locals",
    "getattr", "setattr", "delattr", "hasattr", "input", "breakpoint",
}

FORBIDDEN_ATTRS = {
    "__class__", "__subclasses__", "__bases__", "__mro__", "__globals__",
    "__builtins__", "__code__", "__closure__", "__dict__", "__module__",
    "__qualname__", "gi_frame", "f_globals", "f_locals", "f_code",
    "cr_frame", "ag_frame",
}


def static_ast_inspection(code_str: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Statically analyzes the AST for dangerous constructs, indirect imports,
    and Python introspection escapes.
    """
    try:
        tree = ast.parse(code_str)
    except SyntaxError as e:
        return False, "SyntaxError", f"Line {e.lineno}: {e.msg}"

    for node in ast.walk(tree):
        # 1. Check direct forbidden identifiers
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            return False, "SecurityViolation", f"Security violation: Access to dangerous builtin '{node.id}' is blocked."

        # 2. Check forbidden attribute lookups (e.g., .__class__, .__subclasses__)
        if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_ATTRS:
            return False, "SecurityViolation", f"Security violation: Python introspection attribute '{node.attr}' is strictly blocked."

        # 3. Check imports
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mod = getattr(node, "module", None) or (node.names[0].name if node.names else "")
            root_mod = mod.split(".")[0] if mod else ""
            if root_mod in FORBIDDEN_MODULES:
                return False, "SecurityViolation", f"Security violation: Import of module '{root_mod}' is restricted."

    return True, None, None


def run_worker():
    """Reads execution payload from stdin, runs in sandbox, outputs JSON to stdout."""
    raw_in = sys.stdin.read(1024 * 1024)  # Max 1MB payload
    if not raw_in.strip():
        print(json.dumps({"ok": False, "error": "Empty execution payload."}))
        return

    try:
        payload = json.loads(raw_in)
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"Invalid JSON payload: {e}"}))
        return

    code_str = payload.get("code", "")
    test_cases = payload.get("test_cases", [])

    # 1. AST Validation
    is_valid_ast, err_type, err_msg = static_ast_inspection(code_str)
    if not is_valid_ast:
        if err_type == "SyntaxError":
            print(json.dumps({
                "ok": True,
                "syntax_valid": False,
                "error_type": "SyntaxError",
                "error_message": err_msg,
                "tests_passed": 0,
                "total_tests": len(test_cases),
                "score_pct": 0.0,
            }))
        else:
            print(json.dumps({
                "ok": False,
                "error": err_msg,
                "security_violation": True,
            }))
        return

    # 2. Prepare Safe Execution Namespace
    safe_builtins = {
        "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict, "enumerate": enumerate,
        "filter": filter, "float": float, "int": int, "len": len, "list": list, "map": map,
        "max": max, "min": min, "pow": pow, "print": lambda *args, **kw: None, "range": range,
        "reversed": reversed, "round": round, "set": set, "sorted": sorted, "str": str,
        "sum": sum, "tuple": tuple, "zip": zip, "True": True, "False": False, "None": None,
    }

    exec_globals: Dict[str, Any] = {"__builtins__": safe_builtins, "math": math}
    exec_locals: Dict[str, Any] = {}

    start_time = time.perf_counter()
    try:
        compiled = compile(code_str, filename="<student_code>", mode="exec")
        exec(compiled, exec_globals, exec_locals)
    except Exception as e:
        print(json.dumps({
            "ok": True,
            "syntax_valid": True,
            "runtime_error": f"{type(e).__name__}: {str(e)}",
            "tests_passed": 0,
            "total_tests": len(test_cases),
            "score_pct": 0.0,
        }))
        return

    exec_globals.update(exec_locals)

    # 3. Evaluate Test Cases
    passed_tests = 0
    test_results = []

    for idx, tc in enumerate(test_cases):
        expr = tc.get("input", "")
        expected = str(tc.get("expected", "")).strip()

        try:
            val = eval(expr, exec_globals, exec_locals)
            val_str = str(val).strip()

            is_match = False
            try:
                if abs(float(val_str) - float(expected)) < 1e-4:
                    is_match = True
            except ValueError:
                is_match = (val_str == expected)

            if is_match:
                passed_tests += 1
            test_results.append({
                "test_index": idx + 1,
                "input": expr,
                "expected": expected,
                "actual": val_str,
                "passed": is_match,
            })
        except Exception as e:
            test_results.append({
                "test_index": idx + 1,
                "input": expr,
                "expected": expected,
                "actual": f"Error: {type(e).__name__}",
                "passed": False,
            })

    elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
    score_pct = round((passed_tests / max(1, len(test_cases))) * 100, 1)

    print(json.dumps({
        "ok": True,
        "syntax_valid": True,
        "execution_time_ms": elapsed_ms,
        "tests_passed": passed_tests,
        "total_tests": len(test_cases),
        "score_pct": score_pct,
        "test_results": test_results,
    }))


if __name__ == "__main__":
    run_worker()
