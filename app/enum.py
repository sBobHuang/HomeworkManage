from enum import Enum


class PayType(Enum):
    weixin = 0
    alipay = 1
    cardTransfer = 2
    adminConfirm = 3
    unknown = 4
    refund = 9
    payToTeacher = 10
    payToAssistant = 11
    Others = 13


class OrderStatus(Enum):
    Cancel = -2
    WaitRefund = -1
    AuditionSuccess = 0
    InfoSuccess = 1
    SetSeat = 2
    ConfirmPay = 3
    EnrollmentSuccess = 4
    WaitConfirmTime = 5
    PartialRefund = 6
    OrderFinish = 7
