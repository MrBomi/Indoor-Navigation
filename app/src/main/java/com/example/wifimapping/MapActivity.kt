package com.example.wifimapping

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.net.wifi.ScanResult
import android.net.wifi.WifiManager
import android.os.Bundle
import android.os.Handler
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import com.example.wifirssilogger.R
import java.io.File
import java.io.FileWriter
import java.text.SimpleDateFormat
import java.util.*
import java.io.IOException

class MapActivity : AppCompatActivity() {

    private lateinit var etNodeName: EditText
    private lateinit var btnScan: Button
    private lateinit var btnDone: Button
    private lateinit var tvResults: TextView
    private lateinit var wifiManager: WifiManager
    private lateinit var handler: Handler
    private var scanRunnable: Runnable? = null
    private lateinit var csvFile: File
    private val bssidColumnMap = mutableMapOf<String, Int>()
    private var nextColumnIndex = 1 // Start after the Vertex column
    private lateinit var tvConnectedNetwork: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_map)

        etNodeName = findViewById(R.id.etNodeName)
        btnScan = findViewById(R.id.btnScan)
        btnDone = findViewById(R.id.btnDone)
        tvResults = findViewById(R.id.tvResults)
        tvConnectedNetwork = findViewById(R.id.tvConnectedNetwork)


        wifiManager = getSystemService(Context.WIFI_SERVICE) as WifiManager
        handler = Handler()
        bssidColumnMap.clear()
        nextColumnIndex = 1

        // Create CSV file with timestamp
        val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
        csvFile = File(getExternalFilesDir(null), "$timestamp.csv")

        // Initialize CSV header
        try {
            FileWriter(csvFile).use { writer ->
                writer.append("vertex").append(",")
            }
        } catch (e: IOException) {
            e.printStackTrace()
        }

        btnScan.setOnClickListener {
            if(etNodeName.text.isEmpty()){
                etNodeName.error = "Please enter a node name"
                return@setOnClickListener
            }else{
                // Write current scan results to CSV
                writeToCSV(etNodeName.text.toString())
                etNodeName.text.clear()
                startScanning()
            }
        }


        // Start scanning automatically
        startScanning()
    }

    private fun startScanning() {
        scanRunnable?.let { handler.removeCallbacks(it) }

        scanRunnable = object : Runnable {
            override fun run() {
                performScan()
                handler.postDelayed(this, 30000) // Repeat every 30 seconds
            }
        }
        handler.post(scanRunnable!!)
    }

    private fun writeToCSV(nodeName: String) {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
            != PackageManager.PERMISSION_GRANTED
        ) {
            return
        }

        val results = wifiManager.scanResults

        val connectionInfo = wifiManager.connectionInfo
        val connectedSSID = connectionInfo.ssid?.removeSurrounding("\"") ?: "Not Connected"

        val sameSSIDResults = results.filter {
            it.SSID?.removeSurrounding("\"") == connectedSSID
        }

        // Add any new BSSIDs to the column map
        for (result in sameSSIDResults) {
            if (!bssidColumnMap.containsKey(result.BSSID)) {
                bssidColumnMap[result.BSSID] = nextColumnIndex++
            }
        }

        // Sort BSSID columns by their assigned index
        val sortedBSSIDs = bssidColumnMap.entries.sortedBy { it.value }.map { it.key }

        // Rebuild the header line each time to ensure all columns are included
        val headerLine = buildString {
            append("vertex")
            for (bssid in sortedBSSIDs) {
                append(",").append(bssid)
            }
            append("\n")
        }

        val dataLine = buildString {
            append(nodeName)
            for (bssid in sortedBSSIDs) {
                val rssi = sameSSIDResults.find { it.BSSID == bssid }?.level ?: -100
                append(",").append(rssi)
            }
            append("\n")
        }

        try {
            // If file doesn't exist or is empty, write header first
            val writeHeader = csvFile.length() == 0L
            FileWriter(csvFile, true).use { writer ->
                if (writeHeader) writer.append(headerLine)
                writer.append(dataLine)
            }
        } catch (e: IOException) {
            e.printStackTrace()
        }
    }

    private fun performScan() {
        wifiManager.startScan()
        val results = if (ActivityCompat.checkSelfPermission(
                this,
                Manifest.permission.ACCESS_FINE_LOCATION
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            return
        }else{
            wifiManager.scanResults
        }

        // Get connected network info
        val connectionInfo = wifiManager.connectionInfo
        val connectedSSID = connectionInfo.ssid?.removeSurrounding("\"") ?: "Not Connected"

        // Update connected network display
        tvConnectedNetwork.text = "Connected to: $connectedSSID"

        // Find all BSSIDs with the same SSID
        val sameSSIDResults = results.filter {
            it.SSID?.removeSurrounding("\"") == connectedSSID
        }

        // Update UI with all BSSIDs for the connected SSID
        val displayText = StringBuilder()
        displayText.append("Network: $connectedSSID\n\n")
        displayText.append("Available Access Points:\n")
        displayText.append("------------------------\n")

        sameSSIDResults.forEach { result ->
            displayText.append("BSSID: ${result.BSSID}\n")
            displayText.append("RSSI: ${result.level} dBm\n")
            displayText.append("------------------------\n")
        }

        tvResults.text = displayText.toString()
    }

    override fun onDestroy() {
        super.onDestroy()
        scanRunnable?.let { handler.removeCallbacks(it) }
    }
}