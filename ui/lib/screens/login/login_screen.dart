import 'package:flutter/material.dart';
import 'package:indigo_test/screens/homeScreen/home_screen.dart';
import 'signup_screen.dart';
import '../../widgets/head_title.dart';


class LoginScreen extends StatelessWidget {
  const LoginScreen({super.key});

  void _loginWithGoogle() {
    // TODO: Implement Google login logic
    debugPrint("Google login tapped");
  }

  void _loginWithApple() {
    // TODO: Implement Apple login logic
    debugPrint("Apple login tapped");
  }

  void _navigateToSignUp(BuildContext context) {
    // TODO: Replace with your actual SignUp screen
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => const SignUp()),
    );
  }
  void _navigateToHome(BuildContext context) {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (context) => HomeScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final emailController = TextEditingController();
    final passwordController = TextEditingController();

    return Scaffold(
      backgroundColor: Colors.white,
      body: SafeArea(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
                const SizedBox(height: 25),
                headTitle(context, "Log In", showBackIcon: false),
                Expanded(
                  child: Center(
                    child: SingleChildScrollView(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        const SizedBox(height: 0),
                        const Text(
                          'Welcome',
                          style: TextStyle(
                            color: Color(0xFF225FFF),
                            fontSize: 24,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 30),
                        const Text(
                          'Email or Mobile Number',
                          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w500),
                        ),
                        const SizedBox(height: 8),
                        TextField(
                          controller: emailController,
                          decoration: InputDecoration(
                            hintText: 'example@example.com',
                            filled: true,
                            fillColor: const Color(0xFFECF1FF),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(13),
                              borderSide: BorderSide.none,
                            ),
                          ),
                        ),
                        const SizedBox(height: 20),
                        const Text(
                          'Password',
                          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w500),
                        ),
                        const SizedBox(height: 8),
                        TextField(
                          controller: passwordController,
                          obscureText: true,
                          decoration: InputDecoration(
                            hintText: 'Enter your password',
                            filled: true,
                            fillColor: const Color(0xFFECF1FF),
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(13),
                              borderSide: BorderSide.none,
                            ),
                          ),
                        ),
                        const SizedBox(height: 10),
                        Align(
                          alignment: Alignment.centerRight,
                          child: TextButton(
                            onPressed: () {
                              // TODO: Handle forgot password
                            },
                            child: const Text(
                              'Forget Password?',
                              style: TextStyle(color: Color(0xFF225FFF)),
                            ),
                          ),
                        ),
                        const SizedBox(height: 10),
                        ElevatedButton(
                          onPressed: () {
                            debugPrint('Email: ${emailController.text}');
                            debugPrint('Password: ${passwordController.text}');
                            _navigateToHome(context);
                          },
                          style: ElevatedButton.styleFrom(
                            backgroundColor: const Color(0xFF225FFF),
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(30),
                            ),
                          ),
                            child: const Text(
                              'Log In',
                              style: TextStyle(fontSize: 18, color: Colors.white),
                            ),

                        ),
                        const SizedBox(height: 30),
                        const Center(
                          child: Text(
                            'or sign in with',
                            style: TextStyle(color: Colors.black54, fontSize: 12),
                          ),
                        ),
                        const SizedBox(height: 20),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            _socialLoginButton(
                              icon: Icons.g_mobiledata,
                              onTap: _loginWithGoogle,
                              tooltip: 'Google',
                            ),
                            const SizedBox(width: 20),
                            _socialLoginButton(
                              icon: Icons.apple,
                              onTap: _loginWithApple,
                              tooltip: 'Apple',
                            ),
                          ],
                        ),
                        const SizedBox(height: 30),
                        Center(
                          child: GestureDetector(
                            onTap: () => _navigateToSignUp(context),
                            child: RichText(
                              text: const TextSpan(
                                text: 'Don’t have an account? ',
                                style: TextStyle(color: Colors.black54, fontSize: 12),
                                children: [
                                  TextSpan(
                                    text: 'Sign Up',
                                    style: TextStyle(
                                      color: Color(0xFF225FFF),
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 40),
                      ],
                    ),
                  ),
                        ),
                ),
            ]
          )
      )
    );
  }

  Widget _socialLoginButton({
    required IconData icon,
    required VoidCallback onTap,
    String? tooltip,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(40),
      child: CircleAvatar(
        radius: 25,
        backgroundColor: const Color(0xFFCAD6FF),
        child: Icon(icon, size: 28, color: Colors.black),
      ),
    );
  }


}




