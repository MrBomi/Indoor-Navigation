package com.example
import com.google.gson.Gson
import com.google.gson.GsonBuilder
import com.example.user.model.*
import com.example.admin.model.*

class Constants {
    companion object {
        // global constants
        val LINE_SEPARATOR: String = System.getProperty("line.separator") ?: "\n"
        const val REFRESH_RATE: Int = 500

        // Server resources locations
        const val BASE_DOMAIN: String = "172.20.10.14"
        const val PORT: String = "8574"

        private val BASE_URL: String = "http://$BASE_DOMAIN:$PORT"
        private const val CONTEXT_PATH: String = "/IndiGo"
        private val FULL_SERVER_PATH: String = BASE_URL + CONTEXT_PATH


        val NEW_BUILDING: String = "$FULL_SERVER_PATH/building/add"

        val GET_ALL_BUILDINGS: String = "$FULL_SERVER_PATH/buildings/get"
        val GET_BUILDING_DATA: String = "$FULL_SERVER_PATH/building/data/get"

        val GET_BUILDING_SVG: String = "$FULL_SERVER_PATH/building/svg/get"
        val GET_BUILDING_ROUTE_SVG: String = "$FULL_SERVER_PATH/building/svg/route/get"

        val UPDATE_DOORS_NAME: String = "$FULL_SERVER_PATH/building/doors/update"


//        val LOGIN_PAGE: String = "$FULL_SERVER_PATH/login"
//        val LOGOUT: String = "$FULL_SERVER_PATH/logout"
//        val USERS_LIST: String = "$FULL_SERVER_PATH/userslist"
//        val SHEETS_LIST: String = "$FULL_SERVER_PATH/sheetslist"
//
//
//        val GET_VERSION: String = "$FULL_SERVER_PATH/sheetslist/sheet/version"
//        val UPDATE_CELL: String = "$FULL_SERVER_PATH/sheetslist/sheet/updateCell"
//
//        val ADD_RANGE: String = "$FULL_SERVER_PATH/range/add"
//        val DELETE_RANGE: String = "$FULL_SERVER_PATH/range/delete"
//
//        val SORT_SHEET: String = "$FULL_SERVER_PATH/utils/sort"
//        val FILTER_SHEET: String = "$FULL_SERVER_PATH/utils/filter"
//        val DYNAMIC_SHEET: String = "$FULL_SERVER_PATH/utils/dynamic"
//        val GET_VALUES_FROM_COLUMN: String = "$FULL_SERVER_PATH/utils/getValuesFromColumn"
//        val GET_PERMISSION: String = "$FULL_SERVER_PATH/permission"
//        val ADD_PERMISSION: String = "$FULL_SERVER_PATH/permission/add"
//
//        val SIMULTANEITY: String = "$FULL_SERVER_PATH/simultaneity"
//
//        // GSON instance
//        val GSON_INSTANCE: Gson = GsonBuilder()
//            .registerTypeAdapter(Coordinate::class.java, CoordinateDeserializer())
//            .registerTypeAdapter(Cell::class.java, CellDeserializer())
//            //.registerTypeAdapter(Logic::class.java, LogicDeserializer()) // אם תרצה להפעיל
//            .registerTypeAdapter(SheetDTO::class.java, DTOSheetDeserializer())
//            .registerTypeAdapter(RangeDTO::class.java, DTORangeDeserializer())
//            .create()
    }
}