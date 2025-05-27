package com.example

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import androidx.appcompat.app.AppCompatActivity
import com.example.user.ui.MapActivity
import com.example.admin.ui.ManageActivity
import com.example.wifirssilogger.R
import com.example.user.ui.ScanActivity
import com.example.user.ui.SelectMapActivity

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val btnNewScan: Button = findViewById(R.id.btnNewScan)
        val btnNewMap: Button = findViewById(R.id.btnNewMap)
        val btnNavigate: Button = findViewById(R.id.btnNavigate)
        val btnManageBuildings: Button = findViewById(R.id.btnManage)

        btnNewScan.setOnClickListener {
            val intent = Intent(this, ScanActivity::class.java)
            startActivity(intent)
        }

        btnNewMap.setOnClickListener {
            val intent1 = Intent(this, MapActivity::class.java)
            startActivity(intent1)
        }

        btnNavigate.setOnClickListener {
            val intent2 = Intent(this, SelectMapActivity::class.java)
            startActivity(intent2)
        }
        btnManageBuildings.setOnClickListener {
            val intent3 = Intent(this, ManageActivity::class.java)
            startActivity(intent3)
        }
    }
} 