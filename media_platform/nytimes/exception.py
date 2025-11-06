class DataFetchError(Exception):
    """数据获取异常"""
    def __init__(self, message: str):
        super().__init__(message)


class ParseError(Exception):
    """数据解析异常"""
    def __init__(self, message: str):
        super().__init__(message)


class LoginRequiredError(Exception):
    """需要登录异常"""
    def __init__(self, message: str = "该操作需要先登录"):
        super().__init__(message)


class RequestLimitError(Exception):
    """请求限制异常"""
    def __init__(self, message: str = "请求过于频繁，请稍后再试"):
        super().__init__(message)