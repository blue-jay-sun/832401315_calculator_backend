"""Restricted arithmetic grammar; no execution of user code."""
import re
from decimal import Decimal, DecimalException, localcontext


class CalculationError(ValueError):
    pass


def calculate(expression):
    if not isinstance(expression, str) or not expression.strip():
        raise CalculationError('请输入表达式')
    if len(expression) > 500:
        raise CalculationError('表达式最多 500 个字符')
    text = expression.replace('×', '*').replace('÷', '/')
    tokens = re.findall(r'(?:\d+(?:\.\d*)?|\.\d+)|[+*/()\-]|\S', text)
    position = 0

    def peek():
        return tokens[position] if position < len(tokens) else None

    def take():
        nonlocal position
        token = peek()
        position += 1
        return token

    def factor(depth=0):
        if depth > 64:
            raise CalculationError('表达式嵌套过深')
        token = take()
        if token in ('+', '-'):
            value = factor(depth + 1)
            return value if token == '+' else -value
        if token == '(':
            value = expression_rule(depth + 1)
            if take() != ')':
                raise CalculationError('括号不匹配')
            return value
        if token is None or not re.fullmatch(r'(?:\d+(?:\.\d*)?|\.\d+)', token):
            raise CalculationError('表达式格式错误')
        return Decimal(token)

    def term(depth):
        value = factor(depth)
        while peek() in ('*', '/'):
            operator = take()
            right = factor(depth)
            if operator == '/' and right == 0:
                raise CalculationError('除数不能为零')
            value = value * right if operator == '*' else value / right
        return value

    def expression_rule(depth):
        value = term(depth)
        while peek() in ('+', '-'):
            operator = take()
            right = term(depth)
            value = value + right if operator == '+' else value - right
        return value

    try:
        with localcontext() as context:
            context.prec = 28
            result = expression_rule(0)
            if position != len(tokens):
                raise CalculationError('表达式含多余符号或缺少运算符')
            if not result.is_finite() or result.adjusted() > 1000:
                raise CalculationError('结果超出支持范围')
            return format(result, 'f').rstrip('0').rstrip('.') if '.' in format(result, 'f') else format(result, 'f')
    except DecimalException as error:
        raise CalculationError('数值超出支持范围') from error
