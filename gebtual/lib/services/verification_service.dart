import 'package:dio/dio.dart';
import '../core/telebirr_parser.dart';
import '../models/receipt_data.dart';
import '../models/verification_response.dart';

class VerificationService {
  final Dio _dio = Dio(
    BaseOptions(
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 15),
      headers: {
        "User-Agent": "Mozilla/5.0 (Android; Mobile; rv:109.0) Gecko/109.0",
      },
    ),
  );

  final TelebirrParser _parser = TelebirrParser();
  // Replace with your actual backend URL
  final String backendUrl = "https://api.yourdomain.com/verify";

  Future<VerificationResponse> executeVerificationFlow({
    required String verificationUrl,
    required String transactionId,
  }) async {
    try {
      // 1. Extract Token
      final uri = Uri.parse(verificationUrl);
      if (!uri.isScheme('https')) throw Exception("Invalid URL scheme. HTTPS required.");
      final token = uri.pathSegments.last;
      
      // 2. Normalize Transaction ID
      final normalizedTxnId = transactionId.replaceAll(RegExp(r'\s+'), '').toUpperCase();

      // 3. Download Receipt HTML
      final htmlResponse = await _dio.get(
        "https://transactioninfo.ethiotelecom.et/receipt/$normalizedTxnId",
      );
      
      final htmlString = htmlResponse.data.toString();
      if (htmlString.isEmpty) throw Exception("Empty response from Telebirr.");

      // 4. Parse Locally
      final ReceiptData parsedData = _parser.parse(htmlString);

      // 5. POST to Backend
      final backendResponse = await _dio.post(
        backendUrl,
        data: {
          "token": token,
          "transaction_id": normalizedTxnId,
          "parser_version": "1.0.0",
          "parsed_data": parsedData.toJson(),
        },
      );

      // 6. Return Server Response
      return VerificationResponse.fromJson(backendResponse.data);

    } on DioException catch (e) {
      return VerificationResponse(
        status: "Failed",
        reason: "Network error: ${e.message}",
      );
    } catch (e) {
      return VerificationResponse(
        status: "Failed",
        reason: e.toString(),
      );
    }
  }
}