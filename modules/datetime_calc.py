"""
MODULE 15 — Date, Time & Math
================================
Instant answers for time, date, and arithmetic queries.
Always handled locally by NLP — never routed to Groq.
Math uses safe sandboxed eval (ast module) — no exec() calls.

Tech: datetime (built-in), dateparser, ast (sandboxed eval)
Output: Formatted date/time/math result string → TTS engine
"""

import datetime
import dateparser
import ast
import operator
import re

class SafeMathEvaluator:
    """
    A safe AST-based arithmetic evaluator that avoids raw eval() or exec().
    Supports addition, subtraction, multiplication, division, modulo, and power.
    """
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: lambda x: x
    }

    def evaluate(self, expression: str):
        try:
            # Clean and normalize the expression
            expr_str = self._normalize(expression)
            if not expr_str:
                return "Empty math expression."

            # Parse expression to AST node
            node = ast.parse(expr_str, mode='eval')
            result = self._eval(node.body)
            # Format floats nicely
            if isinstance(result, float) and result.is_integer():
                return int(result)
            return result
        except ZeroDivisionError:
            return "Error: Division by zero."
        except Exception as e:
            return f"Error: Invalid mathematical expression ({e})."

    def _normalize(self, expr: str) -> str:
        # Lowercase and strip
        expr = expr.lower().strip()
        
        # Handle "X percent of Y" -> "X * Y / 100"
        percent_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:percent|%)\s*(?:of)\s*(\d+(?:\.\d+)?)", expr)
        if percent_match:
            pct = percent_match.group(1)
            val = percent_match.group(2)
            return f"({pct} * {val}) / 100"
        
        # Word-based operator normalization
        replacements = {
            r"\bplus\b": "+",
            r"\bminus\b": "-",
            r"\btimes\b": "*",
            r"\bmultiplied\s+by\b": "*",
            r"\bmultiplied\b": "*",
            r"\bdivided\s+by\b": "/",
            r"\bdivided\b": "/",
            r"\bover\b": "/",
            r"\bx\b": "*",  # commonly transcribed "5 x 3"
        }
        for pattern, replacement in replacements.items():
            expr = re.sub(pattern, replacement, expr)
            
        # Strip out any remaining alphabetic characters except mathematical terms/functions
        # to prevent malicious injections (e.g. imports or attribute accesses)
        expr = re.sub(r"[a-zA-Z_]+", "", expr)
        return expr

    def _eval(self, node):
        if isinstance(node, ast.Constant):  # Python 3.8+
            if isinstance(node.value, (int, float)):
                return node.value
            raise TypeError(f"Unsafe constant type: {type(node.value)}")
        elif isinstance(node, ast.Num):  # Fallback for older Pythons
            return node.n
        elif isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type in self.OPERATORS:
                left_val = self._eval(node.left)
                right_val = self._eval(node.right)
                return self.OPERATORS[op_type](left_val, right_val)
            raise TypeError(f"Unsupported binary operator: {op_type.__name__}")
        elif isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type in self.OPERATORS:
                operand_val = self._eval(node.operand)
                return self.OPERATORS[op_type](operand_val)
            raise TypeError(f"Unsupported unary operator: {op_type.__name__}")
        else:
            raise TypeError(f"Unsupported expression node: {type(node).__name__}")


class DateTimeCalc:
    """
    Provides handlers for Date, Time, Days until, and Math Calculations locally.
    """
    def __init__(self):
        self.evaluator = SafeMathEvaluator()

    def get_time(self) -> str:
        """Returns the current system time in a conversational format."""
        return datetime.datetime.now().strftime("It is %I:%M %p.")

    def get_date(self) -> str:
        """Returns the current system date in a conversational format."""
        return datetime.datetime.now().strftime("Today is %A, %B %d, %Y.")

    def days_until(self, target_date_str: str) -> str:
        """Calculates the number of calendar days until the specified target date."""
        if not target_date_str:
            return "Please specify a date."
        try:
            target_dt = dateparser.parse(target_date_str)
            if not target_dt:
                return f"I couldn't understand the date '{target_date_str}'."
            
            # Use date calculation (normalize both to dates without times)
            today = datetime.date.today()
            target_date = target_dt.date()
            delta = target_date - today
            days = delta.days
            
            if days == 0:
                return "That date is today!"
            elif days == 1:
                return "There is 1 day until that date."
            elif days > 1:
                return f"There are {days} days until that date."
            elif days == -1:
                return "That date was yesterday."
            else:
                return f"That date was {-days} days ago."
        except Exception as e:
            return f"Error calculating days: {e}"

    def calculate(self, expression: str) -> str:
        """Safely evaluates an arithmetic expression."""
        if not expression:
            return "What mathematical calculation would you like me to do?"
        res = self.evaluator.evaluate(expression)
        if isinstance(res, str) and res.startswith("Error"):
            return res
        return f"The result is {res}."
