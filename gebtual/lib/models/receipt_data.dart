class ReceiptData {
  final String? payerName;
  final String? creditedPartyName;
  final String? creditedPartyAccount;
  final String? transactionStatus;
  final String? invoiceNo;
  final String? paymentDate;
  final String? settledAmount;
  final String? totalPaidAmount;

  ReceiptData({
    this.payerName,
    this.creditedPartyName,
    this.creditedPartyAccount,
    this.transactionStatus,
    this.invoiceNo,
    this.paymentDate,
    this.settledAmount,
    this.totalPaidAmount,
  });

  Map<String, dynamic> toJson() => {
        "payer_name": payerName,
        "credited_party_name": creditedPartyName,
        "credited_party_account": creditedPartyAccount,
        "transaction_status": transactionStatus,
        "invoice_no": invoiceNo,
        "payment_date": paymentDate,
        "settled_amount": settledAmount,
        "total_paid_amount": totalPaidAmount,
      };
}