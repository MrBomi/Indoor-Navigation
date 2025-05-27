package com.example.user.ui

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.Toast
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.admin.ui.YamlFormActivity
import com.example.admin.viewmodel.UploadResult
import com.example.user.model.MapListAdapter
import com.example.user.viewmodel.SelectMapViewModel
import com.example.wifirssilogger.databinding.ActivitySelectMapBinding

class SelectMapActivity : AppCompatActivity() {

    private lateinit var binding: ActivitySelectMapBinding
    private val viewModel: SelectMapViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySelectMapBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val adapter = MapListAdapter { selectedMap ->
            Toast.makeText(this, "Selected: $selectedMap", Toast.LENGTH_SHORT).show()
            viewModel.selectMap(selectedMap)
        }

        binding.mapsRecyclerView.layoutManager = LinearLayoutManager(this)
        binding.mapsRecyclerView.adapter = adapter



        observeViewModel(adapter)
    }

    private fun observeViewModel(adapter: MapListAdapter) {

        viewModel.mapList.observe(this) { maps ->
            adapter.submitList(maps)
        }

        viewModel.uploadResult.observe(this) { result ->
            result
                .onSuccess { data ->
                    handleSelectedMap(data)
                }
                .onFailure {
                    Toast.makeText(this, "Upload failed: ${it.message}", Toast.LENGTH_LONG).show()
                }
        }
    }

    private fun handleSelectedMap(data: UploadResult){
        val intent = Intent(this, ViewMapActivity::class.java).apply {
            putExtra("svgUrl", data.svgUrl)
            putExtra("doors", ArrayList(data.doors))
        }
        startActivity(intent)
    }
}
