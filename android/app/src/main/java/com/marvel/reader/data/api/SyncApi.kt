package com.marvel.reader.data.api

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.concurrent.TimeUnit

class SyncApi {
    private var baseUrl: String = ""
    private val json = Json { ignoreUnknownKeys = true; coerceInputValues = true }
    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(120, TimeUnit.SECONDS)
        .build()

    fun setServer(host: String, port: Int = 8080) {
        baseUrl = "http://$host:$port"
    }

    val isConfigured get() = baseUrl.isNotEmpty()

    private suspend fun get(path: String): String = withContext(Dispatchers.IO) {
        val request = Request.Builder().url("$baseUrl$path").build()
        client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) throw ApiException(response.code, response.message)
            response.body?.string() ?: throw ApiException(0, "Empty response")
        }
    }

    private suspend fun post(path: String, body: String): String = withContext(Dispatchers.IO) {
        val mediaType = "application/json".toMediaType()
        val request = Request.Builder()
            .url("$baseUrl$path")
            .post(body.toRequestBody(mediaType))
            .build()
        client.newCall(request).execute().use { response ->
            if (!response.isSuccessful) throw ApiException(response.code, response.message)
            response.body?.string() ?: throw ApiException(0, "Empty response")
        }
    }

    suspend fun handshake(): HandshakeResponse =
        json.decodeFromString(get("/sync/handshake"))

    suspend fun getCatalog(): List<CatalogItem> =
        json.decodeFromString(get("/sync/catalog"))

    suspend fun getState(): SyncState =
        json.decodeFromString(get("/sync/state"))

    suspend fun pushState(state: SyncState): SyncPushResponse {
        val body = json.encodeToString(state)
        return json.decodeFromString(post("/sync/state", body))
    }

    suspend fun getIssuePages(orderNum: Int): PagesResponse =
        json.decodeFromString(get("/sync/issue/$orderNum/pages"))

    fun getPageUrl(orderNum: Int, pageNum: Int): String =
        "$baseUrl/sync/issue/$orderNum/page/$pageNum"

    suspend fun downloadPage(orderNum: Int, pageNum: Int): ByteArray =
        withContext(Dispatchers.IO) {
            val request = Request.Builder().url(getPageUrl(orderNum, pageNum)).build()
            client.newCall(request).execute().use { response ->
                if (!response.isSuccessful) throw ApiException(response.code, response.message)
                response.body?.bytes() ?: throw ApiException(0, "Empty response")
            }
        }
}

class ApiException(val code: Int, message: String) : Exception("API error $code: $message")
