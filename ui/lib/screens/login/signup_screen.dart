import 'package:flutter/material.dart';

class SignUp extends StatefulWidget {
  const SignUp({super.key});

  @override
  State<SignUp> createState() => _SignUpState();
}

class _SignUpState extends State<SignUp> {
  final _formKey = GlobalKey<FormState>();
  final nameController = TextEditingController();
  final passwordController = TextEditingController();
  final emailController = TextEditingController();
  final phoneController = TextEditingController();
  final dobController = TextEditingController();

  @override
  void dispose() {
    nameController.dispose();
    passwordController.dispose();
    emailController.dispose();
    phoneController.dispose();
    dobController.dispose();
    super.dispose();
  }

  void _submitForm() {
    if (_formKey.currentState!.validate()) {
      // TODO: Connect to sign-up backend
      print('Signing up:');
      print('Name: ${nameController.text}');
      print('Password: ${passwordController.text}');
      print('Email: ${emailController.text}');
      print('Phone: ${phoneController.text}');
      print('DOB: ${dobController.text}');
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Signed up successfully!')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFFFFFFF),
      body: Center(
        child: Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(30),
          ),
          padding: const EdgeInsets.all(20),
          child: SingleChildScrollView(
            child: Form(
              key: _formKey,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 28),
                  Center(
                    child: Text(
                      'New Account',
                      style: TextStyle(
                        color: const Color(0xFF225FFF),
                        fontSize: 24,
                        fontFamily: 'League Spartan',
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  const SizedBox(height: 32),
                  _buildLabel('Full name'),
                  _buildTextField(nameController, 'Enter your full name'),
                  _buildLabel('Password'),
                  _buildTextField(passwordController, '*************',
                      obscure: true),
                  _buildLabel('Email'),
                  _buildTextField(emailController, 'example@example.com',
                      keyboardType: TextInputType.emailAddress),
                  _buildLabel('Mobile Number'),
                  _buildTextField(phoneController, '055-1234567',
                      keyboardType: TextInputType.phone),
                  _buildLabel('Date of birth'),
                  _buildTextField(dobController, 'DD / MM / YYYY'),
                  const SizedBox(height: 20),
                  Center(
                    child: Text.rich(
                      TextSpan(
                        children: [
                          const TextSpan(
                            text: 'By continuing, you agree to \n',
                            style: TextStyle(
                              color: Colors.black87,
                              fontSize: 12,
                              fontWeight: FontWeight.w300,
                            ),
                          ),
                          TextSpan(
                            text: 'Terms of Use',
                            style: TextStyle(
                              color: const Color(0xFF225FFF),
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          const TextSpan(
                            text: ' and ',
                            style: TextStyle(
                              color: Colors.black87,
                              fontSize: 12,
                              fontWeight: FontWeight.w300,
                            ),
                          ),
                          TextSpan(
                            text: 'Privacy Policy.',
                            style: TextStyle(
                              color: const Color(0xFF225FFF),
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ),
                  const SizedBox(height: 20),
                  Center(
                    child: ElevatedButton(
                      onPressed: _submitForm,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF225FFF),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(30),
                        ),
                        padding: const EdgeInsets.symmetric(
                            horizontal: 60, vertical: 14),
                      ),
                      child: const Text(
                        'Sign Up',
                        style: TextStyle(
                          color: Colors.white,
                          fontSize: 20,
                          fontFamily: 'League Spartan',
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 30),
                  Center(
                    child: Text(
                      'or sign up with',
                      style: TextStyle(
                        color: Colors.black87,
                        fontSize: 12,
                        fontWeight: FontWeight.w300,
                      ),
                    ),
                  ),
                  const SizedBox(height: 10),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: List.generate(3, (i) {
                      return CircleAvatar(
                        radius: 20,
                        backgroundColor: const Color(0xFFCAD6FF),
                        child: i == 1
                            ? Container(
                                width: 24,
                                height: 24,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  border: Border.all(
                                    color: const Color(0xFF225FFF),
                                    width: 2,
                                  ),
                                ),
                              )
                            : null,
                      );
                    }),
                  ),
                  const SizedBox(height: 24),
                  Center(
                    child: Text.rich(
                      TextSpan(
                        children: [
                          const TextSpan(
                            text: 'Already have an account? ',
                            style: TextStyle(
                              color: Colors.black87,
                              fontSize: 12,
                              fontWeight: FontWeight.w300,
                            ),
                          ),
                          TextSpan(
                            text: 'Log in',
                            style: TextStyle(
                              color: const Color(0xFF225FFF),
                              fontSize: 12,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(top: 14.0, bottom: 6.0),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 20,
          fontFamily: 'League Spartan',
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  Widget _buildTextField(
    TextEditingController controller,
    String hint, {
    bool obscure = false,
    TextInputType keyboardType = TextInputType.text,
  }) {
    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFECF1FF),
        borderRadius: BorderRadius.circular(13),
      ),
      child: TextFormField(
        controller: controller,
        obscureText: obscure,
        keyboardType: keyboardType,
        validator: (value) =>
            value == null || value.isEmpty ? 'This field is required' : null,
        style: TextStyle(
          fontSize: 18,
          color: const Color(0xFF225FFF),
          fontFamily: 'League Spartan',
        ),
        decoration: InputDecoration(
          contentPadding: const EdgeInsets.symmetric(horizontal: 12),
          hintText: hint,
          hintStyle: const TextStyle(
            color: Color(0xFF7F9BFF),
            fontSize: 18,
            fontFamily: 'League Spartan',
          ),
          border: InputBorder.none,
        ),
      ),
    );
  }
}
