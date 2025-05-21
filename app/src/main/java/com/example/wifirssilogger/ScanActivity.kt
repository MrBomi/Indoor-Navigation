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
import com.google.gson.Gson
import com.google.gson.JsonObject
import com.google.gson.JsonParser


class ScanActivity : AppCompatActivity() {

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

        btnScan = findViewById(R.id.btnScan)
        tvResults = findViewById(R.id.tvResults)
        tvConnectedNetwork = findViewById(R.id.tvConnectedNetwork)

        wifiManager = getSystemService(Context.WIFI_SERVICE) as WifiManager
        handler = Handler()
        bssidColumnMap.clear()

        btnScan.setOnClickListener {
            startScanning()
        }

        val connectionInfo = wifiManager.connectionInfo
        val connectedSSID = connectionInfo.ssid?.removeSurrounding("\"") ?: "Not Connected"
        tvConnectedNetwork.text = "$connectedSSID"
    }

    private fun startScanning() {
        scanRunnable?.let { handler.removeCallbacks(it) }

        scanRunnable = object : Runnable {
            override fun run() {
                performScan()
            }
        }
        handler.post(scanRunnable!!)
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
        val hardCodeSSID = "MTA WiFi"
        // Update connected network display
        tvConnectedNetwork.text = "$connectedSSID"


        // Find all BSSIDs with the same SSID
        val sameSSIDResults = results.filter {
            it.SSID?.removeSurrounding("\"") == hardCodeSSID
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

        val request = Request.Builder()
            .url("https://flask-rssi-server-691362032525.us-central1.run.app/predict")
            .post(requestBody)
            .build()
//        val request = Request.Builder()
//            .url("https://flask-rssi-server-691362032525.us-central1.run.app/health")
//            .addHeader("Accept", "application/json")
//            .build()

        client.newCall(request).enqueue(object : Callback {
            val displayText = StringBuilder()
            override fun onFailure(call: Call, e: IOException) {
                e.printStackTrace()
                Log.e("HTTP_ERROR", "Network call failed: ${e.localizedMessage}", e)

                runOnUiThread {
                    displayText.clear()
                    displayText.append("Request failed: ${e.message ?: "Unknown error"}\n")
                    tvResults.text = displayText.toString()
                }
            }

            override fun onResponse(call: Call, response: Response) {
                val responseText = if (response.isSuccessful) {
                    val body = response.body?.use { it.string() } ?: return

                    try {
                        val json = JsonParser.parseString(body).asJsonObject
                        val top3 = json.getAsJsonArray("top3")
                        val vertices = top3.map { it.asJsonObject["vertex"].asString }
                        vertices.joinToString(" ")  // join with spaces
                    } catch (e: Exception) {
                        "JSON parse error"
                    }
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
    }

    override fun onDestroy() {
        super.onDestroy()
        scanRunnable?.let { handler.removeCallbacks(it) }
    }
} 