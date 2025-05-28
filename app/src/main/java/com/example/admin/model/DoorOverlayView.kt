package com.example.admin.model

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Matrix
import android.graphics.Paint
import android.graphics.drawable.Drawable
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.View
import android.widget.Button
import androidx.appcompat.app.AlertDialog
import com.github.chrisbanes.photoview.PhotoView
import java.io.Serializable

// Data class to represent a door
data class Door(
    val id: Int,
    val x: Float,
    val y: Float,
    var name: String? = null
) : Serializable

class DoorOverlayView(context: Context, attrs: AttributeSet) : View(context, attrs) {
    var doors: MutableList<Door> = mutableListOf()
    var doorsMap: MutableMap<Int,String> = mutableMapOf()
    var referencePhotoView: PhotoView? = null
    var referenceBtnContinue: Button? = null
    var originalSvgWidth: Int = 800
    var originalSvgHeight: Int = 800

    private val paint = Paint().apply {
        color = Color.BLUE
        style = Paint.Style.STROKE  // <- This makes it hollow
        strokeWidth = 4f            // <- Optional: set border thickness
        isAntiAlias = true
    }
    private val filledPaint = Paint().apply {
        color = Color.GREEN
        style = Paint.Style.FILL
        strokeWidth = 4f
        isAntiAlias = true
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val photoView = referencePhotoView ?: return
        val btnContinue = referenceBtnContinue ?: return
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
            var selectedPaint = paint

            if (!door.name.isNullOrBlank()) {
                // Draw name and switch to filled green paint
                canvas.drawText(door.name!!, drawX + 25, drawY - 10, Paint().apply {
                    color = Color.GREEN
                    textSize = 20f
                    isAntiAlias = true
                })
                selectedPaint = filledPaint
            }
            canvas.drawCircle(drawX, drawY, 10f, selectedPaint)
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
                doorsMap[door.id] = door.name ?: ""
                invalidate()
                //TODO change the test!
                TESTcheckIfAllDoorsNamed()
                //checkIfAllDoorsNamed()
            }
            .setNegativeButton("Cancel", null)
        .show()
        }

    private fun TESTcheckIfAllDoorsNamed() {
        val namedDoorsCount = doors.count { !it.name.isNullOrBlank() }
        referenceBtnContinue?.isEnabled = namedDoorsCount >= 5
    }

    private fun checkIfAllDoorsNamed() {
        val allNamed = doors.all { !it.name.isNullOrBlank() }
        referenceBtnContinue?.isEnabled = allNamed
    }
}