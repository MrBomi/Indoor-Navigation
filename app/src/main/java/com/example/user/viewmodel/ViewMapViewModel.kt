package com.example.user.viewmodel

import android.graphics.drawable.PictureDrawable
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import com.caverock.androidsvg.SVG
import com.example.admin.model.Door
import okhttp3.Call
import okhttp3.Callback
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import java.io.IOException

class ViewMapViewModel : ViewModel() {

    private val _roomList = MutableLiveData<List<String>>()
    val roomList: LiveData<List<String>> get() = _roomList


    private val _svgDrawable = MutableLiveData<Result<PictureDrawable>>()
    val svgDrawable: LiveData<Result<PictureDrawable>> get() = _svgDrawable

    fun setRoomList(rooms: List<Door>) {
        val names = rooms.mapNotNull { it.name }
        _roomList.value = names
    }

    fun loadSVGFromUrl(svgLink: String) {
        val url = "http://172.20.10.14:8574/building/getSvgDirect?buildingId=$svgLink"
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

    fun loadSVGFromUrlWithRoute(query: String) {
        val url = "http://172.20.10.14:8574/building/route/get$query"
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

}
