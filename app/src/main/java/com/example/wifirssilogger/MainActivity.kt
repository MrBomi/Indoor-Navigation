package com.example.wifirssilogger

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import androidx.appcompat.app.AppCompatActivity
import com.example.wifimapping.MapActivity
import com.example.FloorplanUI.FloorPlanMapActivity
import com.example.manageBuildings.ManageActivity

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val btnNewScan: Button = findViewById(R.id.btnNewScan)
        val btnNewMap: Button = findViewById(R.id.btnNewMap)
        val btnNewFloorPlan: Button = findViewById(R.id.btnNewPlan)
        val btnManageBuildings: Button = findViewById(R.id.btnManage)

        btnNewScan.setOnClickListener {
            val intent = Intent(this, ScanActivity::class.java)
            startActivity(intent)
        }

        btnNewMap.setOnClickListener {
            val intent1 = Intent(this, MapActivity::class.java)
            startActivity(intent1)
        }

        btnNewFloorPlan.setOnClickListener {
            val intent2 = Intent(this, FloorPlanMapActivity::class.java)
            startActivity(intent2)
        }
        btnManageBuildings.setOnClickListener {
            val intent3 = Intent(this, ManageActivity::class.java)
            startActivity(intent3)
        }
    }
} 