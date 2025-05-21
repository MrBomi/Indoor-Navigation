package com.example.FloorplanUI

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Matrix
import android.graphics.Paint
import android.graphics.drawable.Drawable
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.View
import androidx.appcompat.app.AlertDialog
import com.github.chrisbanes.photoview.PhotoView

// Data class to represent a door
data class Door(val id: Int, val x: Float, val y: Float, var name: String? = null)

class DoorOverlayView(context: Context, attrs: AttributeSet) : View(context, attrs) {
    var doors: MutableList<Door> = mutableListOf()
    var referencePhotoView: PhotoView? = null
    var originalSvgWidth: Int = 800
    var originalSvgHeight: Int = 800

    private val paint = Paint().apply {
        color = Color.BLUE
        style = Paint.Style.STROKE  // <- This makes it hollow
        strokeWidth = 4f            // <- Optional: set border thickness
        isAntiAlias = true
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val photoView = referencePhotoView ?: return
        val drawable: Drawable = photoView.drawable ?: return

        val matrix = FloatArray(9)
        photoView.imageMatrix.getValues(matrix)

        val scaleX = matrix[Matrix.MSCALE_X]
        val scaleY = matrix[Matrix.MSCALE_Y]
        val transX = matrix[Matrix.MTRANS_X]
        val transY = matrix[Matrix.MTRANS_Y]

        for (door in doors) {
            val drawX = door.x * scaleX + transX
            val drawY = door.y * scaleY + transY
            canvas.drawCircle(drawX, drawY, 10f, paint)
            door.name?.let {
                canvas.drawText(it, drawX, drawY, Paint().apply {
                //canvas.drawText(it, drawX + 25, drawY - 10, Paint().apply {
                    color = Color.BLUE
                    textSize = 20f
                })
            }
        }
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        if (event.action == MotionEvent.ACTION_DOWN) {
            val photoView = referencePhotoView ?: return false
            val drawable: Drawable = photoView.drawable ?: return false

            val matrix = FloatArray(9)
            photoView.imageMatrix.getValues(matrix)

            val scaleX = matrix[Matrix.MSCALE_X]
            val scaleY = matrix[Matrix.MSCALE_Y]
            val transX = matrix[Matrix.MTRANS_X]
            val transY = matrix[Matrix.MTRANS_Y]

            val touchedX = (event.x - transX) / scaleX
            val touchedY = (event.y - transY) / scaleY

            val clicked = doors.find {
                val dx = it.x - touchedX
                val dy = it.y - touchedY
                dx * dx + dy * dy < 30 * 30 / (scaleX * scaleX)
            }
            clicked?.let { showNameDialog(it) }
        }
        return super.onTouchEvent(event)
    }

    private fun showNameDialog(door: Door) {
        val input = android.widget.EditText(context).apply {
            setText(door.name ?: "")
        }
        AlertDialog.Builder(context)
            .setTitle("Enter door name")
            .setView(input)
            .setPositiveButton("Save") { _, _ ->
                door.name = input.text.toString()
                invalidate()
                //TODO update the server
            }
            .setNegativeButton("Cancel", null)
        .show()
        }
}