package com.example.FloorplanUI

import android.graphics.drawable.PictureDrawable
import android.os.Bundle
import android.widget.Button
import androidx.appcompat.app.AppCompatActivity
import com.caverock.androidsvg.SVG
import com.example.wifirssilogger.R
import com.example.wifirssilogger.databinding.ActivityDoorsSelectBinding
import kotlinx.coroutines.*
import org.json.JSONObject
import java.io.InputStream

class FloorPlanMapActivity : AppCompatActivity() {
    private lateinit var binding: ActivityDoorsSelectBinding
    var doorsJson: MutableMap<Int,String> = mutableMapOf()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityDoorsSelectBinding.inflate(layoutInflater)
        setContentView(binding.root)


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
        }

        // Load SVG and doors
        val svgData = assets.open("output.svg")
        val jsonData = assets.open("doors.json")

        loadSVGFromAssets(svgData)
        loadDoorDataFromAssets(jsonData)
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
