package com.vehicledb.network

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object APIClient {
    private const val BASE_URL = "https://vehicledb.onrender.com/"
    private const val API_KEY = "5fe6a87f63ababfcb50fc3e15ed9cbbf"

    private val retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .addConverterFactory(GsonConverterFactory.create())
        .build()

    val vinService: VINService = retrofit.create(VINService::class.java)
    fun getApiKey() = API_KEY
} 