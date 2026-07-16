class VerificationResponse {
  final String status;
  final String? reason;

  VerificationResponse({required this.status, this.reason});

  factory VerificationResponse.fromJson(Map<String, dynamic> json) {
    return VerificationResponse(
      status: json['status'] ?? 'Failed',
      reason: json['reason'],
    );
  }
}