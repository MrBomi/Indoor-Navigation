package com.example.manageBuildings

import android.app.Activity
import android.content.Intent
import android.database.Cursor
import android.net.Uri
import android.os.Bundle
import android.widget.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import com.example.wifirssilogger.R


class ManageActivity : AppCompatActivity() {

    private lateinit var btnAddBuilding: Button
    private lateinit var buildingList: LinearLayout

    private val yamlFormLauncher =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
            if (result.resultCode == Activity.RESULT_OK) {
                val buildingName = result.data?.getStringExtra("buildingName")
                if (buildingName != null) {
                    addBuildingToList(buildingName)
                }
            }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_manage_buildings)

        buildingList = findViewById(R.id.buildingList)
        btnAddBuilding = findViewById(R.id.btnAddBuilding)

        btnAddBuilding.setOnClickListener {
            openFilePicker()
        }
    }

    private fun openFilePicker() {
        val intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        intent.type = "*/*" // You can filter by file type if needed
        filePickerLauncher.launch(intent)
    }

    // File picker that triggers YAML form
    private val filePickerLauncher =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
            if (result.resultCode == Activity.RESULT_OK) {
                val data: Intent? = result.data
                val uri: Uri? = data?.data
                uri?.let {
                    handleSelectedFile(it)
                }
            }
        }


    private fun addBuildingToList(buildingName: String) {
        val inflater = layoutInflater
        val newBuilding = inflater.inflate(R.layout.item_building, buildingList, false)

        val tvBuildingName = newBuilding.findViewById<TextView>(R.id.tvBuildingName)
        tvBuildingName?.text = buildingName

        buildingList.addView(newBuilding)
    }

    private fun handleSelectedFile(uri: Uri) {
        val fileName = getFileNameFromUri(uri)

        val intent = Intent(this, YamlFormActivity::class.java)
        intent.putExtra("fileUri", uri)
        intent.putExtra("fileName", fileName)
        yamlFormLauncher.launch(intent)
    }

    private fun getFileNameFromUri(uri: Uri): String {
        var name = uri.lastPathSegment ?: "Selected File"

        if (uri.scheme == "content") {
            contentResolver.query(uri, null, null, null, null)?.use { cursor ->
                val nameIndex = cursor.getColumnIndexOpenableDisplayName()
                if (nameIndex != -1 && cursor.moveToFirst()) {
                    name = cursor.getString(nameIndex)
                }
            }
        }
        return name
    }

    private fun Cursor.getColumnIndexOpenableDisplayName(): Int {
        return getColumnIndex("_display_name").takeIf { it != -1 } ?: getColumnIndex("name")
    }
}
