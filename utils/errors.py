class BaseException(Exception):
    pass

class AccountNotExistError(BaseException):
    def __init__(self, acc_id):
        self.args = [
            ''
        ]

class AmountError(BaseException):
    def __init__(self, args):
        print(args)
        self.args = ['My args']

class BalanceError(BaseException):
    pass
