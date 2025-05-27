//package com.example.admin.ui
//
//import android.app.Activity
//import android.content.Intent
//import android.net.Uri
//import android.os.Build
//import android.os.Bundle
//import android.widget.*
//import androidx.activity.result.contract.ActivityResultContracts
//import androidx.appcompat.app.AppCompatActivity
//import com.example.admin.model.Door
//import com.example.wifirssilogger.R
//import okhttp3.*
//import okhttp3.MediaType.Companion.toMediaTypeOrNull
//import okhttp3.RequestBody.Companion.toRequestBody
//import org.json.JSONObject
//import java.io.IOException
//
//class YamlFormActivity : AppCompatActivity() {
//
//    private lateinit var precision: EditText
//    private lateinit var wallLayer: EditText
//    private lateinit var doorLayer: EditText
//    private lateinit var roofLayer: EditText
//    private lateinit var submitBtn: Button
//
//    private lateinit var fileUri: Uri
//    private lateinit var fileName: String
//
//    // Modern activity result launcher instead of deprecated startActivityForResult
//    private val floorPlanLauncher = registerForActivityResult(
//        ActivityResultContracts.StartActivityForResult()
//    ) { result ->
//        if (result.resultCode == Activity.RESULT_OK) {
//            val resultIntent = Intent().apply {
//                putExtra("buildingName", fileName.substringBeforeLast('.'))
//            }
//            setResult(Activity.RESULT_OK, resultIntent)
//            finish()
//        }
//    }
//
//    override fun onCreate(savedInstanceState: Bundle?) {
//        super.onCreate(savedInstanceState)
//        setContentView(R.layout.activity_yaml_form)
//
//        // Use modern version for getParcelableExtra
//        fileUri = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
//            intent.getParcelableExtra("fileUri", Uri::class.java)
//        } else {
//            @Suppress("DEPRECATION")
//            intent.getParcelableExtra("fileUri")
//        } ?: run {
//            Toast.makeText(this, "File URI is missing", Toast.LENGTH_SHORT).show()
//            finish()
//            return
//        }
//
//        fileName = intent.getStringExtra("fileName") ?: "UnnamedFile.dxf"
//
//        precision = findViewById(R.id.precision)
//        wallLayer = findViewById(R.id.wallLayer)
//        doorLayer = findViewById(R.id.doorLayer)
//        roofLayer = findViewById(R.id.roofLayer)
//        submitBtn = findViewById(R.id.submitYamlBtn)
//
//        submitBtn.setOnClickListener {
//            val yaml = buildYaml()
//            val fileBytes = contentResolver.openInputStream(fileUri)?.readBytes()
//            if (fileBytes != null) {
//                uploadWithYaml(fileName, fileBytes, yaml)
//            }
//        }
//    }
//
//    private fun buildYaml(): String {
//        val fileNameWithoutExtension = fileName.substringBeforeLast('.')
//
//        return """
//            app:
//              name: Graph Maker
//              version: 1.0
//
//            file:
//              input_name: ${fileNameWithoutExtension}.dxf
//              output_name: static/output/${fileNameWithoutExtension}.graphml
//              svg_output_name: static/output/${fileNameWithoutExtension}.svg
//              json_output_name: static/output/${fileNameWithoutExtension}_points.json
//              precision: ${precision.text}
//
//            graph:
//              node_size: 30.0
//              scale: ${precision.text}
//              offset_cm: 200
//
//            layers:
//              wall_layer:
//                name: ${wallLayer.text}
//                color: "#000000"
//                opacity: 0.5
//
//              door_layer:
//                name: ${doorLayer.text}
//                color: "#FF0000"
//                opacity: 0.5
//
//              roof_layer:
//                name: ${roofLayer.text}
//                color: "#00FF00"
//                opacity: 0.5
//        """.trimIndent()
//    }
//
//    private fun uploadWithYaml(fileName: String, fileBytes: ByteArray, yaml: String) {
//        val yamlRequestBody = yaml.toRequestBody("text/plain".toMediaTypeOrNull())
//        val fileRequestBody = fileBytes.toRequestBody("application/octet-stream".toMediaTypeOrNull())
//
//        val multipartBody = MultipartBody.Builder()
//            .setType(MultipartBody.FORM)
//            .addFormDataPart("dwg", fileName, fileRequestBody)
//            .addFormDataPart("yaml", "config.yaml", yamlRequestBody)
//            .addFormDataPart("buildingId", "1") // TODO: dynamic ID
//            .build()
//
//        val request = Request.Builder()
//            .url("http://172.20.10.3:8574/building/add") // Your backend
//            .post(multipartBody)
//            .build()
//
//        OkHttpClient().newCall(request).enqueue(object : Callback {
//            override fun onFailure(call: Call, e: IOException) {
//                runOnUiThread {
//                    Toast.makeText(this@YamlFormActivity, "Upload failed", Toast.LENGTH_LONG).show()
//                }
//            }
//
//            override fun onResponse(call: Call, response: Response) {
//                response.use {
//                    if (!response.isSuccessful) {
//                        runOnUiThread {
//                            Toast.makeText(this@YamlFormActivity, "Server error", Toast.LENGTH_SHORT).show()
//                        }
//                        return
//                    }
//
//                    val json = JSONObject(response.body!!.string())
//                    val doorsJson = json.getJSONArray("doors")
//                    val doors = mutableListOf<Door>()
//
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
//
//                    val svgLink = json.getString("image_url")
//
//                    // Build intent and launch next activity
//                    val intent = Intent(this@YamlFormActivity, FloorPlanMapActivity::class.java).apply {
//                        putExtra("svgLink", svgLink)
//                        putExtra("buildingName", fileName.substringBeforeLast('.'))
//                        putExtra("doors", ArrayList(doors)) // Serializable
//                    }
//
//                    floorPlanLauncher.launch(intent)
//                }
//            }
//        })
//    }
//}
package com.example.admin.ui

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.widget.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import com.example.admin.viewmodel.UploadResult
import com.example.admin.viewmodel.YamlFormViewModel
import com.example.wifirssilogger.R

class YamlFormActivity : AppCompatActivity() {

    private lateinit var precision: EditText
    private lateinit var wallLayer: EditText
    private lateinit var doorLayer: EditText
    private lateinit var roofLayer: EditText
    private lateinit var submitBtn: Button

    private lateinit var fileUri: Uri
    private lateinit var fileName: String

    private val viewModel: YamlFormViewModel by viewModels()

    private val floorPlanLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val resultIntent = Intent().apply {
                putExtra("buildingName", fileName.substringBeforeLast('.'))
            }
            setResult(Activity.RESULT_OK, resultIntent)
            finish()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_yaml_form)

        fileUri = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            intent.getParcelableExtra("fileUri", Uri::class.java)
        } else {
            @Suppress("DEPRECATION")
            intent.getParcelableExtra("fileUri")
        } ?: run {
            Toast.makeText(this, "File URI is missing", Toast.LENGTH_SHORT).show()
            finish()
            return
        }

        fileName = intent.getStringExtra("fileName") ?: "UnnamedFile.dxf"

        precision = findViewById(R.id.precision)
        wallLayer = findViewById(R.id.wallLayer)
        doorLayer = findViewById(R.id.doorLayer)
        roofLayer = findViewById(R.id.roofLayer)
        submitBtn = findViewById(R.id.submitYamlBtn)

        submitBtn.setOnClickListener {
            val yaml = viewModel.buildYaml(
                fileName,
                precision.text.toString(),
                wallLayer.text.toString(),
                doorLayer.text.toString(),
                roofLayer.text.toString()
            )

            val fileBytes = contentResolver.openInputStream(fileUri)?.readBytes()
            if (fileBytes != null) {
                viewModel.upload(fileName, fileBytes, yaml)
            } else {
                Toast.makeText(this, "Failed to read file", Toast.LENGTH_SHORT).show()
            }
        }

        observeViewModel()
    }

    private fun observeViewModel() {
        viewModel.uploadResult.observe(this) { result ->
            result
                .onSuccess { data ->
                    openFloorPlan(data)
                }
                .onFailure {
                    Toast.makeText(this, "Upload failed: ${it.message}", Toast.LENGTH_LONG).show()
                }
        }
    }

    private fun openFloorPlan(data: UploadResult) {
        val intent = Intent(this, FloorPlanMapActivity::class.java).apply {
            putExtra("svgLink", data.svgUrl)
            putExtra("buildingName", fileName.substringBeforeLast('.'))
            putExtra("doors", ArrayList(data.doors)) // Serializable
        }

        floorPlanLauncher.launch(intent)
    }
}
