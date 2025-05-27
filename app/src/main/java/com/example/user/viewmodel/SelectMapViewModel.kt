package com.example.user.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import com.example.admin.model.Door
import com.example.admin.viewmodel.UploadResult
import okhttp3.Call
import okhttp3.Callback
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import org.json.JSONObject
import java.io.IOException

data class UploadResult(val svgUrl: String, val doors: List<Door>)

class SelectMapViewModel : ViewModel() {

    private val _uploadResult = MutableLiveData<Result<UploadResult>>()
    val uploadResult: LiveData<Result<UploadResult>> get() = _uploadResult

    private val _mapList = MutableLiveData<List<String>>() // replace String with a Map model if needed
    val mapList: LiveData<List<String>> get() = _mapList

    init {
        loadMaps()
    }

    private fun loadMaps() {
        // Example static data
        //TODO: Replace with actual data loading logic,from server 1-HTTP
        _mapList.value = listOf("Library", "Main Hall", "Building B", "Floor 3")
    }

    fun selectMap(mapName: String) {
        //TODO sending http to the server get the map data (clean svg) and names of doors/rooms  2-HTTP
        /// TODO on success go to the map screen

        val request = Request.Builder()
            .url("http://172.20.10.3:8574/building/data/get?buildingName=$mapName")
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
                                y = d.getDouble("y").toFloat(),
                                name = d.getString("name")
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
