package com.example.wifirssilogger

import android.Manifest
import android.content.Context
import android.content.pm.PackageManager
import android.net.wifi.ScanResult
import android.net.wifi.WifiManager
import android.os.Bundle
import android.os.Handler
import android.util.Log
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.File
import java.io.FileWriter
import java.text.SimpleDateFormat
import java.util.*
import java.io.IOException


class ScanActivity : AppCompatActivity() {

    private lateinit var etNodeName: EditText
    private lateinit var btnScan: Button
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
        setContentView(R.layout.activity_scan)

        etNodeName = findViewById(R.id.etNodeName)
        btnScan = findViewById(R.id.btnScan)
        tvResults = findViewById(R.id.tvResults)
        tvConnectedNetwork = findViewById(R.id.tvConnectedNetwork)

        wifiManager = getSystemService(Context.WIFI_SERVICE) as WifiManager
        handler = Handler()
        bssidColumnMap.clear()
        nextColumnIndex = 1

        // Create CSV file with timestamp
        val timestamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
        csvFile = File(getExternalFilesDir(null), "wifi_scan_$timestamp.csv")

        // Initialize CSV header
        try {
            FileWriter(csvFile).use { writer ->
                writer.append("Vertex").append(",")
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
        //startScanning()
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
            append("Vertex")
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


        val displayText = StringBuilder()
        displayText.append("got nothing\n")
        tvResults.text = displayText.toString()

        // Find all BSSIDs with the same SSID
        val sameSSIDResults = results.filter {
            it.SSID?.removeSurrounding("\"") == connectedSSID
        }

        val jsonObject = JSONObject()
        val bssids = JSONObject()

        sameSSIDResults.forEach {
            bssids.put(it.BSSID, it.level)
        }

        jsonObject.put("userId", "Noam")  // Add your user ID or device ID here
        jsonObject.put("bssids", bssids)

        val client = OkHttpClient()

        val JSON = "application/json; charset=utf-8".toMediaType()
        val requestBody = jsonObject.toString().toRequestBody(JSON)

//        val request = Request.Builder()
//            .url("https://yourserver.com/api/location")
//            .post(requestBody)
//            .build()
        val request = Request.Builder()
            .url("http://192.168.1.227:8574/books/health")
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                e.printStackTrace()
                Log.e("HTTP_ERROR", "Network call failed", e)

                runOnUiThread {
                    displayText.clear()
                    displayText.append("Request failed: ${e.message}\n")
                    tvResults.text = displayText.toString()
                }
            }

            override fun onResponse(call: Call, response: Response) {
                val responseText = if (response.isSuccessful) {
                    "GET successful: ${response.code}\n${response.body?.string()}"
                } else {
                    "GET failed: ${response.code}"
                }

                runOnUiThread {
                    displayText.clear()
                    displayText.append(responseText)
                    tvResults.text = displayText.toString()
                }

                response.close()
            }
        })


//        // Update UI with all BSSIDs for the connected SSID
//        val displayText = StringBuilder()
//        displayText.append("Network: $connectedSSID\n\n")
//        displayText.append("Available Access Points:\n")
//        displayText.append("------------------------\n")
//
//        sameSSIDResults.forEach { result ->
//            displayText.append("BSSID: ${result.BSSID}\n")
//            displayText.append("RSSI: ${result.level} dBm\n")
//            displayText.append("------------------------\n")
//        }
//
//        tvResults.text = displayText.toString()
    }

    override fun onDestroy() {
        super.onDestroy()
        scanRunnable?.let { handler.removeCallbacks(it) }
    }
} 