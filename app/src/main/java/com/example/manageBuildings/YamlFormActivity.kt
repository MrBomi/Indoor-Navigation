package com.example.manageBuildings

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import com.example.FloorplanUI.Door
import com.example.FloorplanUI.FloorPlanMapActivity
import com.example.wifirssilogger.R
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException


class YamlFormActivity : AppCompatActivity() {


    private val FLOOR_PLAN_REQUEST_CODE = 1001
    private lateinit var precision: EditText
    private lateinit var wallLayer: EditText
    private lateinit var doorLayer: EditText
    private lateinit var roofLayer: EditText
    private lateinit var submitBtn: Button

    private lateinit var fileUri: Uri
    private lateinit var fileName: String

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_yaml_form)

        fileUri = intent.getParcelableExtra("fileUri")!!
        fileName = intent.getStringExtra("fileName")!!

        precision = findViewById(R.id.precision)
        wallLayer = findViewById(R.id.wallLayer)
        doorLayer = findViewById(R.id.doorLayer)
        roofLayer = findViewById(R.id.roofLayer)
        submitBtn = findViewById(R.id.submitYamlBtn)



        submitBtn.setOnClickListener {
            val yaml = buildYaml()
            val fileBytes = contentResolver.openInputStream(fileUri)?.readBytes()
            if (fileBytes != null) {
                uploadWithYaml(fileName, fileBytes, yaml)
            }
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)

        if (requestCode == FLOOR_PLAN_REQUEST_CODE && resultCode == Activity.RESULT_OK) {
            // Pass the result back to ManageActivity
            val resultIntent = Intent().apply {
                putExtra("buildingName", fileName.substringBeforeLast('.'))
            }
            setResult(Activity.RESULT_OK, resultIntent)
            finish() // Closes YamlFormActivity
        }
    }


    private fun buildYaml(): String {
        val fileNameWithoutExtension = fileName.substringBeforeLast('.')

        // Auto-fill computed fields
        val inputPath = "${fileNameWithoutExtension}.dxf"
        val outputPath = "static/output/${fileNameWithoutExtension}.graphml"
        val svgPath = "static/output/${fileNameWithoutExtension}.svg"
        val jsonPath = "static/output/${fileNameWithoutExtension}_points.json"

        return """
            app:
              name: Graph Maker
              version: 1.0

            file:
              input_name: $inputPath
              output_name: $outputPath
              svg_output_name: $svgPath
              json_output_name: $jsonPath
              precision: ${precision.text}

            graph:
              node_size: 30.0
              scale: 1
              offset_cm: 200

            layers:
              wall_layer:
                name: ${wallLayer.text}
                color: "#000000"
                opacity: 0.5

              door_layer:
                name: ${doorLayer.text}
                color: "#FF0000"
                opacity: 0.5

              roof_layer:
                name: ${roofLayer.text}
                color: "#00FF00"
                opacity: 0.5
        """.trimIndent()
    }

    private fun uploadWithYaml(fileName: String, fileBytes: ByteArray, yaml: String) {
        val yamlRequestBody = yaml.toRequestBody("text/plain".toMediaTypeOrNull())
        val fileRequestBody = fileBytes.toRequestBody("application/octet-stream".toMediaTypeOrNull())

        val multipartBody = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("dwg", fileName, fileRequestBody)
            .addFormDataPart("yaml", "config.yaml", yamlRequestBody)
            .addFormDataPart("buildingId", "1") //TODO change it
            .build()

        val request = Request.Builder()
            .url("http://172.20.10.3:8574/building/add") // <- Replace with your server URL
            .post(multipartBody)
            .build()

        OkHttpClient().newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread {
                    Toast.makeText(this@YamlFormActivity, "Upload failed", Toast.LENGTH_LONG).show()
                }
            }

            override fun onResponse(call: Call, response: Response) {

                response.use {
                    if (!response.isSuccessful) {
                        runOnUiThread {
                            Toast.makeText(this@YamlFormActivity, "Server error", Toast.LENGTH_SHORT).show()
                        }
                        return
                    }

                    val json = JSONObject(response.body!!.string())

                    // 1. Parse doors array into Map<Int, String>
                    val doorsJson = json.getJSONArray("doors")
                    val doors = mutableListOf<Door>()
//                    for (i in 0 until doorsJson.length()) {
//                        val d = doorsJson.getJSONObject(i)
//                        doors.add(
//                            Door(
//                                id = d.getInt("id"),
//                                x = d.getDouble("x").toFloat(),
//                                y = d.getDouble("y").toFloat()
//                            )
//                        )
//                    }
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
                    // 2. Get the SVG link
                    val svgLink = json.getString("image_url")

                    // 3. Start FloorPlanMapActivity and pass both
                    val intent = Intent(this@YamlFormActivity, FloorPlanMapActivity::class.java).apply {
                        putExtra("svgLink", svgLink)
                        putExtra("buildingName", fileName.substringBeforeLast('.'))

                        // You must serialize the map to a Bundle or use Serializable
                        putExtra("doors", ArrayList(doors)) // Serializable version
                    }

                    startActivityForResult(intent, FLOOR_PLAN_REQUEST_CODE)
                }
            }
        })
    }
}