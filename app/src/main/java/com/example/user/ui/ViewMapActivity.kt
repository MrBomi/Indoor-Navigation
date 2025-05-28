package com.example.user.ui

import android.graphics.drawable.PictureDrawable
import android.os.Build
import android.os.Bundle
import android.view.View
import android.widget.ArrayAdapter
import android.widget.Toast
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import com.example.admin.model.Door
import com.example.user.viewmodel.ViewMapViewModel
import com.example.wifirssilogger.databinding.ActivityViewMapBinding
import kotlinx.coroutines.*


class ViewMapActivity : AppCompatActivity() {

    private lateinit var binding: ActivityViewMapBinding
    private val viewModel: ViewMapViewModel by viewModels()
    private val coroutineScope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityViewMapBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val svgUrl = intent.getStringExtra("svgUrl")
        val doors = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            intent.getSerializableExtra("doors", ArrayList::class.java) as? ArrayList<Door>
        } else {
            @Suppress("DEPRECATION")
            intent.getSerializableExtra("doors") as? ArrayList<Door>
        }

        if (doors == null || svgUrl == null) {
            Toast.makeText(this, "Missing map data", Toast.LENGTH_SHORT).show()
            finish()
            return
        }

        viewModel.setRoomList(doors)

        svgUrl.let {
            viewModel.loadSVGFromUrl(it)
        }

        observeViewModel()

        binding.goButton.setOnClickListener {
            val start = binding.startRoomSpinner.selectedItem?.toString()
            val end = binding.endRoomSpinner.selectedItem?.toString()
            Toast.makeText(this, "Navigate from $start to $end", Toast.LENGTH_SHORT).show()
            val addQuery = "?buildingId=$svgUrl&start=$start&goal=$end"
            viewModel.loadSVGFromUrlWithRoute(addQuery)
        }
    }

    private fun observeViewModel() {
        viewModel.roomList.observe(this) { rooms ->
            val adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, rooms)
            binding.startRoomSpinner.adapter = adapter
            binding.endRoomSpinner.adapter = adapter
        }
        viewModel.svgDrawable.observe(this) { result ->
            result.onSuccess { drawable ->
                displaySvg(drawable)
            }.onFailure {
                Toast.makeText(this, "Failed to load map: ${it.message}", Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun displaySvg(drawable: PictureDrawable) {
        binding.imageMap.setLayerType(View.LAYER_TYPE_SOFTWARE, null)
        binding.imageMap.setImageDrawable(drawable)
        binding.doorOverlay.invalidate()
    }

    private fun showError(message: String) {
        runOnUiThread {
            Toast.makeText(this@ViewMapActivity, message, Toast.LENGTH_SHORT).show()
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        coroutineScope.cancel()
    }
}

