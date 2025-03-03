package com.vehicledb.network

import retrofit2.Response
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.Query

interface VINService {
    @GET("api/check_vin")
    suspend fun checkVIN(
        @Header("X-API-Key") apiKey: String,
        @Query("vin") vin: String
    ): Response<VINResponse>
}

data class VINResponse(
    val found: Boolean,
    val description: String?,
    val scan_date: String?
) 