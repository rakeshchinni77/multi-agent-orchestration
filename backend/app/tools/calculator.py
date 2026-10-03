import ast
import math
import operator
from typing import Dict, Any, Callable
from app.tools.schemas import CalculatorInput, ToolResult
from app.core.logging import get_logger

logger = get_logger(__name__)

# Mapping of supported AST operators to Python operator functions
_SAFE_OPERATORS: Dict[type, Callable] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Whitelist of safe mathematical functions and constants
_SAFE_FUNCTIONS: Dict[str, Callable] = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "ceil": math.ceil,
    "floor": math.floor,
}

_SAFE_CONSTANTS: Dict[str, float] = {
    "pi": math.pi,
    "e": math.e,
}


def _safe_eval_node(node: ast.AST) -> Any:
    """Recursively evaluate an AST node in a secure, isolated sandbox."""
    if isinstance(node, ast.Expression):
        return _safe_eval_node(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant type: {type(node.value).__name__}")

    if isinstance(node, ast.BinOp):
        op_func = _SAFE_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")
        left = _safe_eval_node(node.left)
        right = _safe_eval_node(node.right)
        # Prevent huge exponents causing DoS
        if isinstance(node.op, ast.Pow) and (right > 1000 or (isinstance(left, (int, float)) and abs(left) > 1000 and right > 100)):
            raise ValueError("Exponent calculation exceeds allowed complexity limits")
        return op_func(left, right)

    if isinstance(node, ast.UnaryOp):
        op_func = _SAFE_OPERATORS.get(type(node.op))
        if op_func is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        operand = _safe_eval_node(node.operand)
        return op_func(operand)

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Direct function calls only permitted (no chained attributes)")
        func_name = node.func.id.lower()
        if func_name not in _SAFE_FUNCTIONS:
            raise ValueError(f"Function '{func_name}' is not in the safe mathematical whitelist")
        args = [_safe_eval_node(arg) for arg in node.args]
        return _SAFE_FUNCTIONS[func_name](*args)

    if isinstance(node, ast.Name):
        const_name = node.id.lower()
        if const_name in _SAFE_CONSTANTS:
            return _SAFE_CONSTANTS[const_name]
        raise ValueError(f"Variable or identifier '{node.id}' is not defined")

    raise ValueError(f"Unsupported syntax expression element: {type(node).__name__}")


def evaluate_calculator(input_data: CalculatorInput) -> ToolResult:
    """
    Safely evaluate a mathematical expression without ever using eval().
    
    Catches zero division, syntax errors, and invalid tokens gracefully.
    """
    expr = input_data.expression.strip()
    logger.info(f"Executing Calculator tool with expression: '{expr}'")

    if not expr:
        return ToolResult(
            tool_name="calculator",
            success=False,
            error="Expression cannot be empty.",
            error_type="VALIDATION_ERROR",
            retryable=False
        )

    try:
        parsed = ast.parse(expr, mode="eval")
        result = _safe_eval_node(parsed)

        # Round floats slightly to eliminate floating point precision artifacts (e.g. 0.30000000000000004)
        if isinstance(result, float) and not math.isnan(result) and not math.isinf(result):
            result = round(result, 6)

        return ToolResult(
            tool_name="calculator",
            success=True,
            data={
                "expression": expr,
                "result": result
            }
        )

    except ZeroDivisionError:
        logger.warning(f"Calculator zero division error in: {expr}")
        return ToolResult(
            tool_name="calculator",
            success=False,
            error="Division by zero is mathematically undefined.",
            error_type="MATH_ERROR",
            retryable=False
        )
    except SyntaxError as e:
        logger.warning(f"Calculator syntax error in '{expr}': {e}")
        return ToolResult(
            tool_name="calculator",
            success=False,
            error=f"Malformed mathematical syntax: {str(e)}",
            error_type="SYNTAX_ERROR",
            retryable=False
        )
    except Exception as e:
        logger.error(f"Calculator evaluation failure in '{expr}': {e}")
        return ToolResult(
            tool_name="calculator",
            success=False,
            error=f"Evaluation failed: {str(e)}",
            error_type="EVALUATION_ERROR",
            retryable=False
        )
