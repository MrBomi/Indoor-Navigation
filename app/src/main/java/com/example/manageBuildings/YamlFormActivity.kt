package com.example.manageBuildings

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import com.example.wifirssilogger.R
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException

class YamlFormActivity : AppCompatActivity() {


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

    private fun buildYaml(): String {
        val fileNameWithoutExtension = fileName.substringBeforeLast('.')

        // Auto-fill computed fields
        val inputPath = "${fileNameWithoutExtension}.dxf"
        val outputPath = "${fileNameWithoutExtension}.graphml"
        val svgPath = "${fileNameWithoutExtension}.svg"
        val jsonPath = "${fileNameWithoutExtension}_points.json"

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
            .addFormDataPart("config", "config.yaml", yamlRequestBody)
            .build()

        val request = Request.Builder()
            .url("https://yourserver.com/upload")
            .post(multipartBody)
            .build()

        OkHttpClient().newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                runOnUiThread {
                    Toast.makeText(this@YamlFormActivity, "Upload failed", Toast.LENGTH_LONG).show()
                }
            }

            override fun onResponse(call: Call, response: Response) {
                runOnUiThread {
                    Toast.makeText(this@YamlFormActivity, "Upload success", Toast.LENGTH_SHORT).show()

                    // Return result to ManageActivity
                    val resultIntent = Intent().apply {
                        putExtra("buildingName", fileName.substringBeforeLast('.'))
                    }
                    setResult(Activity.RESULT_OK, resultIntent)
                    finish() // Closes YamlFormActivity and returns
                }
            }
        })
    }
}