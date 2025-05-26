package com.example.FloorplanUI

import android.graphics.drawable.PictureDrawable
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.caverock.androidsvg.SVG
import com.example.wifirssilogger.databinding.ActivityDoorsSelectBinding
import com.google.gson.Gson
import kotlinx.coroutines.*
import org.json.JSONObject
import java.io.InputStream
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException

class FloorPlanMapActivity : AppCompatActivity() {
    private lateinit var binding: ActivityDoorsSelectBinding
    var doorsJson: MutableMap<Int,String> = mutableMapOf()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityDoorsSelectBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val svgLink = intent.getStringExtra("svgLink")
        val doors = intent.getSerializableExtra("doors") as? ArrayList<Door>

        // Back button
        binding.backButton.setOnClickListener {
            finish()
        }

        // Attach overlay to PhotoView
        binding.doorOverlay.referencePhotoView = binding.imageMap
        binding.doorOverlay.referenceBtnContinue = binding.continueButton
        binding.doorOverlay.doorsMap = doorsJson
        // Invalidate overlay when image changes
        binding.imageMap.setOnMatrixChangeListener {
            binding.doorOverlay.invalidate()
        }

        binding.continueButton.setOnClickListener {
            println("Doors: ${doorsJson}")
            sendNewDoors(doorsJson)
        }

        if (svgLink != null) {
            loadSVGFromUrl(svgLink)
        }
        if (doors != null) {
            binding.doorOverlay.doors = doors
            binding.doorOverlay.invalidate()
        }
    }
    private fun loadSVGFromUrl(url: String) {
        CoroutineScope(Dispatchers.IO).launch {
            val urlWithParam = "http://172.20.10.3:8574/building/getSvgDirect?svgLink=$url"
            val request = Request.Builder()
                .url(urlWithParam) // <- Replace with your server URL
                .build()

            OkHttpClient().newCall(request).enqueue(object : Callback {
                override fun onFailure(call: Call, e: IOException) {
                    e.printStackTrace() // Log the full error to Logcat

                    runOnUiThread {
                        Toast.makeText(this@FloorPlanMapActivity, "Network error: ${e.message}", Toast.LENGTH_LONG).show()
                    }
                }

                override fun onResponse(call: Call, response: Response) {
                    if (!response.isSuccessful || response.body == null) {
                        runOnUiThread {
                            Toast.makeText(this@FloorPlanMapActivity, "Failed to load SVG", Toast.LENGTH_SHORT).show()
                        }
                        return
                    }

                    try {
                        val inputStream = response.body!!.byteStream()
                        val svg = SVG.getFromInputStream(inputStream)
                        val drawable = PictureDrawable(svg.renderToPicture())

                        runOnUiThread {
                            binding.imageMap.setLayerType(android.view.View.LAYER_TYPE_SOFTWARE, null)
                            binding.imageMap.setImageDrawable(drawable)
                            binding.doorOverlay.invalidate()
                        }
                    } catch (e: Exception) {
                        e.printStackTrace()
                        runOnUiThread {
                            Toast.makeText(this@FloorPlanMapActivity, "Error displaying SVG", Toast.LENGTH_SHORT).show()
                        }
                    }


                }
            })

        }
    }

    private fun sendNewDoors(doorsJson : MutableMap<Int, String>) {
        val buildingId = 1 // or any value you need dynamically

        val payload = mapOf(
            "buildingID" to buildingId,
            "doors" to doorsJson
        )

        val gson = Gson()
        val json = gson.toJson(payload) // Serialize to JSON

        val client = OkHttpClient()
        val mediaType = "application/json; charset=utf-8".toMediaTypeOrNull()
        val body = json.toRequestBody(mediaType)

        val request = Request.Builder()
            .url("http://172.20.10.3:8574/building/updateDoorsName")
            .put(body)
            .build()

        client.newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread {
                    Toast.makeText(this@FloorPlanMapActivity, "Failed to send data", Toast.LENGTH_SHORT).show()
                }
            }

            override fun onResponse(call: Call, response: Response) {
                runOnUiThread {
                    Toast.makeText(this@FloorPlanMapActivity, "Data sent successfully", Toast.LENGTH_SHORT).show()
                    setResult(RESULT_OK)
                    finish()
                }
            }
        })
    }

    private fun loadSVGFromAssets(input: InputStream) {
        CoroutineScope(Dispatchers.IO).launch {
            val svg = SVG.getFromInputStream(input)
            val drawable = PictureDrawable(svg.renderToPicture())

            withContext(Dispatchers.Main) {
                binding.imageMap.setLayerType(android.view.View.LAYER_TYPE_SOFTWARE, null)
                binding.imageMap.setImageDrawable(drawable)
                binding.doorOverlay.invalidate()
            }
        }
    }

    private fun loadDoorDataFromAssets(input: InputStream) {
        CoroutineScope(Dispatchers.Default).launch {
            val json = input.bufferedReader().use { it.readText() }
            val obj = JSONObject(json)
            val doorsJson = obj.getJSONArray("doors")

            val doors = mutableListOf<Door>()
            for (i in 0 until 5) {
                val d = doorsJson.getJSONObject(i)
                doors.add(
                    Door(
                        id = d.getInt("id"),
                        x = d.getDouble("x").toFloat(),
                        y = d.getDouble("y").toFloat()
                    )
                )
            }
//            for (i in 0 until doorsJson.length()) {
//                val d = doorsJson.getJSONObject(i)
//                doors.add(
//                    Door(
//                        id = d.getInt("id"),
//                        x = d.getDouble("x").toFloat(),
//                        y = d.getDouble("y").toFloat()
//                    )
//                )
//            }

            withContext(Dispatchers.Main) {
                binding.doorOverlay.doors = doors
                binding.doorOverlay.invalidate()
            }
        }
    }


}
