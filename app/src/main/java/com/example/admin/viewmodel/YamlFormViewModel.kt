package com.example.admin.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import com.example.admin.model.Door
import kotlinx.coroutines.*
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.IOException

data class UploadResult(val svgUrl: String, val doors: List<Door>)

class YamlFormViewModel : ViewModel() {

    private val _uploadResult = MutableLiveData<Result<UploadResult>>()
    val uploadResult: LiveData<Result<UploadResult>> get() = _uploadResult

    fun buildYaml(fileName: String, precision: String, wall: String, door: String, roof: String): String {
        val fileNameWithoutExtension = fileName.substringBeforeLast('.')

        return """
            app:
              name: Graph Maker
              version: 1.0

            file:
              input_name: $fileNameWithoutExtension.dxf
              output_name: static/output/$fileNameWithoutExtension.graphml
              svg_output_name: static/output/$fileNameWithoutExtension.svg
              json_output_name: static/output/${fileNameWithoutExtension}_points.json
              precision: $precision

            graph:
              node_size: 30.0
              scale: $precision
              offset_cm: 200

            layers:
              wall_layer:
                name: $wall
                color: "#000000"
                opacity: 0.5

              door_layer:
                name: $door
                color: "#FF0000"
                opacity: 0.5

              roof_layer:
                name: $roof
                color: "#00FF00"
                opacity: 0.5
        """.trimIndent()
    }

    fun upload(fileName: String, fileBytes: ByteArray, yaml: String) {
        val yamlRequestBody = yaml.toRequestBody("text/plain".toMediaTypeOrNull())
        val fileRequestBody = fileBytes.toRequestBody("application/octet-stream".toMediaTypeOrNull())

        val multipartBody = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("dwg", fileName, fileRequestBody)
            .addFormDataPart("yaml", "config.yaml", yamlRequestBody)
            .addFormDataPart("buildingId", "1")
            .build()

        val request = Request.Builder()
            .url("http://172.20.10.3:8574/building/add")
            .post(multipartBody)
            .build()

        OkHttpClient().newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                _uploadResult.postValue(Result.failure(e))
            }

            override fun onResponse(call: Call, response: Response) {
                response.use {
                    if (!it.isSuccessful) {
                        _uploadResult.postValue(Result.failure(IOException("Server error")))
                        return
                    }

                    val json = JSONObject(it.body!!.string())
                    val doorsJson = json.getJSONArray("doors")
                    val doors = mutableListOf<Door>()

                    for (i in 0 until doorsJson.length()) {
                        val d = doorsJson.getJSONObject(i)
                        doors.add(
                            Door(
                                id = d.getInt("id"),
                                x = d.getDouble("x").toFloat(),
                                y = d.getDouble("y").toFloat()
                            )
                        )
                    }

                    val svgLink = json.getString("image_url")
                    _uploadResult.postValue(Result.success(UploadResult(svgLink, doors)))
                }
            }
        })
    }
}
