import 'package:flutter/material.dart';
import 'package:indigo_test/screens/homeScreen/home_screen.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';

final RouteObserver<ModalRoute<void>> routeObserver = RouteObserver<ModalRoute<void>>();

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: ".env");
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  static const Color primaryColor = Color(0xFF225FFF);


  // This widget is the root of your application.
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Login Screen',
      theme: ThemeData(
        primaryColor: primaryColor,
        scaffoldBackgroundColor: Colors.white,
        colorScheme: ColorScheme.fromSwatch().copyWith(
          primary: primaryColor,
          secondary: Color(0xFFEDEFFF),
        ),
        textTheme: TextTheme(
          bodyMedium: TextStyle(color: Colors.black87),
        ),
        appBarTheme: AppBarTheme(
          backgroundColor: Colors.white,
          foregroundColor: Colors.black87,
          elevation: 0,
        ),
        iconTheme: IconThemeData(color: primaryColor),
      ),
      //home: PdrTestScreen(),
      home: HomeScreen(),
      navigatorObservers: [routeObserver],
      debugShowCheckedModeBanner: false,
    );
  }
}

