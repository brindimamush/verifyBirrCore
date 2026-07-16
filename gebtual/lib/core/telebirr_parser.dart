import 'package:html/parser.dart' as html_parser;
import 'package:html/dom.dart';
import '../models/receipt_data.dart';

class TelebirrParser {
  String clean(String value) =>
      value.replaceAll(RegExp(r'\s+'), ' ').trim();

  String? findValue(Document document, String keyword) {
    final tds = document.getElementsByTagName("td");

    for (final td in tds) {
      final text = clean(td.text);

      if (text.toLowerCase().contains(keyword.toLowerCase())) {
        final next = td.nextElementSibling;

        if (next != null) {
          return clean(next.text);
        }
      }
    }
    return null;
  }

  Map<String, String?> invoice(Document document) {
    final rows = document.getElementsByTagName("tr");

    for (int i = 0; i < rows.length - 1; i++) {
      final header = rows[i].getElementsByTagName("td");

      if (header.length != 3) continue;

      if (header[0].text.contains("Invoice No") &&
          header[1].text.contains("Payment date") &&
          header[2].text.contains("Settled Amount")) {
        final values = rows[i + 1].getElementsByTagName("td");

        if (values.length == 3) {
          return {
            "invoice_no": clean(values[0].text),
            "payment_date": clean(values[1].text),
            "settled_amount": clean(values[2].text),
          };
        }
      }
    }
    return {};
  }

  ReceiptData parse(String html) {
    final document = html_parser.parse(html);
    final inv = invoice(document);

    return ReceiptData(
      payerName: findValue(document, "Payer Name"),
      creditedPartyName: findValue(document, "Credited Party name"),
      creditedPartyAccount: findValue(document, "Credited party account no"),
      transactionStatus: findValue(document, "transaction status"),
      invoiceNo: inv["invoice_no"],
      paymentDate: inv["payment_date"],
      settledAmount: inv["settled_amount"],
      totalPaidAmount: findValue(document, "Total Paid Amount"),
    );
  }
}