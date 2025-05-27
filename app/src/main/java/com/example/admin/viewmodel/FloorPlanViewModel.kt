package com.example.admin.viewmodel

import android.graphics.drawable.PictureDrawable
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import com.caverock.androidsvg.SVG
import com.google.gson.Gson
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException

class FloorPlanViewModel : ViewModel() {

    private val _svgDrawable = MutableLiveData<Result<PictureDrawable>>()
    val svgDrawable: LiveData<Result<PictureDrawable>> get() = _svgDrawable

    private val _uploadResult = MutableLiveData<Result<Unit>>()
    val uploadResult: LiveData<Result<Unit>> get() = _uploadResult

    fun loadSVGFromUrl(svgLink: String) {
        val url = "http://172.20.10.3:8574/building/getSvgDirect?svgLink=$svgLink"
        val request = Request.Builder()
            .url(url)
            .build()

        OkHttpClient().newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                _svgDrawable.postValue(Result.failure(e))
            }

            override fun onResponse(call: Call, response: Response) {
                if (!response.isSuccessful || response.body == null) {
                    _svgDrawable.postValue(Result.failure(IOException("Failed to load SVG")))
                    return
                }

                try {
                    val inputStream = response.body!!.bytes().inputStream()
                    val svg = SVG.getFromInputStream(inputStream)
                    val drawable = PictureDrawable(svg.renderToPicture())
                    _svgDrawable.postValue(Result.success(drawable))
                } catch (e: Exception) {
                    _svgDrawable.postValue(Result.failure(e))
                }
            }
        })
    }

    fun sendNewDoors(buildingId: Int, doorsJson: Map<Int, String>) {
        val payload = mapOf("buildingID" to buildingId, "doors" to doorsJson)
        val gson = Gson()
        val json = gson.toJson(payload)

        val requestBody = json.toRequestBody("application/json; charset=utf-8".toMediaTypeOrNull())
        val request = Request.Builder()
            .url("http://172.20.10.3:8574/building/updateDoorsName")
            .put(requestBody)
            .build()

        OkHttpClient().newCall(request).enqueue(object : Callback {
            override fun onFailure(call: Call, e: IOException) {
                _uploadResult.postValue(Result.failure(e))
            }

            override fun onResponse(call: Call, response: Response) {
                if (response.isSuccessful) {
                    _uploadResult.postValue(Result.success(Unit))
                } else {
                    _uploadResult.postValue(Result.failure(IOException("Failed to update doors")))
                }
            }
        })
    }
}
