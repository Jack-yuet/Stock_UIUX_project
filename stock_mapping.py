# 股票代码后缀映射
# 自动为用户输入的代码添加正确的后缀

def add_stock_suffix(stock_code):
    """为股票代码添加正确的后缀"""
    if not stock_code:
        return stock_code
    
    # 如果已经有后缀，直接返回
    if '.' in stock_code:
        return stock_code
    
    # 根据代码规则添加后缀
    code = stock_code.upper()
    
    # 港股规则（4位数字）
    if len(code) == 4 and code.isdigit():
        return code + '.HK'  # 香港证券交易所
    
    # A股规则（6位数字）
    if len(code) == 6 and code.isdigit():
        if code.startswith('60') or code.startswith('68'):
            return code + '.SS'  # 上海证券交易所
        elif code.startswith('00') or code.startswith('30'):
            return code + '.SZ'  # 深圳证券交易所
        elif code.startswith('83') or code.startswith('87'):
            return code + '.BJ'  # 北京证券交易所
    
    # 美股规则（通常不需要后缀，但yfinance可能需要）
    # 如果都不匹配，可能是美股，直接返回原代码
    return stock_code 