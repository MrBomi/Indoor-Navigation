package com.example.user.model

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.example.wifirssilogger.databinding.MapItemBinding

class MapListAdapter(
    private val onClick: (String) -> Unit
) : RecyclerView.Adapter<MapListAdapter.MapViewHolder>() {

    private var items: List<String> = emptyList()

    fun submitList(data: List<String>) {
        items = data
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): MapViewHolder {
        val binding = MapItemBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return MapViewHolder(binding)
    }

    override fun onBindViewHolder(holder: MapViewHolder, position: Int) {
        holder.bind(items[position])
    }

    override fun getItemCount(): Int = items.size

    inner class MapViewHolder(private val binding: MapItemBinding) :
        RecyclerView.ViewHolder(binding.root) {
        fun bind(name: String) {
            binding.mapName.text = name
            binding.root.setOnClickListener {
                onClick(name)
            }
        }
    }
}
