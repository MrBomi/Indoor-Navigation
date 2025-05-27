package com.example.admin.viewmodel

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel

class ManageViewModel : ViewModel() {

    private val _buildings = MutableLiveData<List<String>>(emptyList())
    val buildings: LiveData<List<String>> get() = _buildings

    fun addBuilding(name: String) {
        val updated = _buildings.value.orEmpty().toMutableList()
        updated.add(name)
        _buildings.value = updated
    }
}
