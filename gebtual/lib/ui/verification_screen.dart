import 'package:flutter/material.dart';
import '../services/verification_service.dart';
import '../models/verification_response.dart';

class VerificationScreen extends StatefulWidget {
  const VerificationScreen({super.key});

  @override
  State<VerificationScreen> createState() => _VerificationScreenState();
}

class _VerificationScreenState extends State<VerificationScreen> {
  final _formKey = GlobalKey<FormState>();
  final _linkController = TextEditingController();
  final _txnController = TextEditingController();
  final VerificationService _service = VerificationService();
  
  bool _isLoading = false;

  @override
  void dispose() {
    _linkController.dispose();
    _txnController.dispose();
    super.dispose();
  }

  void _verifyPayment() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
    });

    final response = await _service.executeVerificationFlow(
      verificationUrl: _linkController.text.trim(),
      transactionId: _txnController.text.trim(),
    );

    setState(() {
      _isLoading = false;
    });

    if (mounted) {
      _showResultDialog(response);
    }
  }

  void _showResultDialog(VerificationResponse response) {
    final isSuccess = response.status.toLowerCase() == 'verified';

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF2C2C2C),
        title: Row(
          children: [
            Icon(
              isSuccess ? Icons.check_circle : Icons.cancel,
              color: isSuccess ? Colors.greenAccent : Colors.redAccent,
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                isSuccess ? "Payment Verified Successfully" : "Verification Failed",
                style: const TextStyle(fontSize: 18),
              ),
            ),
          ],
        ),
        content: isSuccess
            ? null
            : Text(
                "Reason:\n${response.reason ?? 'Unknown error occurred.'}",
                style: const TextStyle(color: Colors.white70),
              ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              if (isSuccess) {
                _linkController.clear();
                _txnController.clear();
              }
            },
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Secure Verification'),
        centerTitle: true,
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Enter details to verify the transaction.',
                  style: TextStyle(color: Colors.white70, fontSize: 16),
                ),
                const SizedBox(height: 24),
                TextFormField(
                  controller: _linkController,
                  enabled: !_isLoading,
                  decoration: const InputDecoration(
                    labelText: 'Verification Link',
                    hintText: 'https://verify.example.com/pay/...',
                    prefixIcon: Icon(Icons.link),
                  ),
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please paste the verification link';
                    }
                    if (!value.startsWith('http')) {
                      return 'Invalid URL format';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _txnController,
                  enabled: !_isLoading,
                  textCapitalization: TextCapitalization.characters,
                  decoration: const InputDecoration(
                    labelText: 'Transaction ID',
                    hintText: 'e.g., ABC123XYZ',
                    prefixIcon: Icon(Icons.receipt_long),
                  ),
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter the Transaction ID';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 32),
                ElevatedButton(
                  onPressed: _isLoading ? null : _verifyPayment,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Text(
                          'Verify',
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                        ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}