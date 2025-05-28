package com.example.user.viewmodel

import android.util.Log
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import com.example.Constants
import com.example.admin.model.Door
import com.example.admin.viewmodel.UploadResult
import okhttp3.Call
import okhttp3.Callback
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException

data class UploadResult(val svgUrl: String, val doors: List<Door>)

class SelectMapViewModel : ViewModel() {

    private val _uploadResult = MutableLiveData<Result<UploadResult>>()
    val uploadResult: LiveData<Result<UploadResult>> get() = _uploadResult

    private val _mapList = MutableLiveData<List<String>>() // replace String with a Map model if needed
    val mapList: LiveData<List<String>> get() = _mapList

    init {
        Log.d("ViewModelInit", "ViewModel created and loadMaps called")
        loadMaps()
    }

    private fun loadMaps() {
        Log.d("loadMaps", "Sending request to server...")

        val request = Request.Builder()
            .url("http://172.20.10.14:8574/buildings/get")
            .build()

        OkHttpClient().newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                Log.e("loadMaps", "Failed to fetch maps", e)
                _mapList.postValue(emptyList())
            }

            override fun onResponse(call: Call, response: Response) {
                response.use {
                    if (!it.isSuccessful) {
                        Log.e("loadMaps", "Failed to fetch maps")
                        _mapList.postValue(emptyList())
                        return
                    }

                    val jsonArray = JSONArray(it.body!!.string())
                    val mapNames = mutableListOf<String>()

                    for (i in 0 until jsonArray.length()) {
                        mapNames.add(jsonArray.getString(i))
                    }

                    _mapList.postValue(mapNames)
                }
            }
        })
    }

    fun selectMap(mapName: String) {
        val request = Request.Builder()
            .url("http://172.20.10.14:8574/building/data/get?buildingId=$mapName")
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
                    val roomsJson = json.getJSONArray("rooms")
                    val rooms = mutableListOf<Door>()

                    for (i in 0 until roomsJson.length()) {
                        val d = roomsJson.getJSONObject(i)
                        rooms.add(
                            Door(
                                id = d.getInt("id"),
                                x = d.getDouble("x").toFloat(),
                                y = d.getDouble("y").toFloat(),
                                name = d.getString("name")
                            )
                        )
                    }

                    val svgLink = json.getString("building_id")
                    _uploadResult.postValue(Result.success(UploadResult(svgLink, rooms)))
                }
            }
        })
    }
}
