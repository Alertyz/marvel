package com.marvel.reader.data.api

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class HandshakeResponse(
    val server: String,
    val version: String,
    @SerialName("total_issues") val totalIssues: Int,
    @SerialName("available_issues") val availableIssues: Int,
    @SerialName("read_issues") val readIssues: Int,
)

@Serializable
data class CatalogItem(
    @SerialName("order_num") val orderNum: Int,
    val title: String,
    val issue: Int,
    val phase: String,
    val event: String? = null,
    val year: String,
    @SerialName("available_pages") val availablePages: Int,
)

@Serializable
data class PageInfo(
    @SerialName("page_num") val pageNum: Int,
    val filename: String,
    val size: Long,
)

@Serializable
data class PagesResponse(
    @SerialName("order_num") val orderNum: Int,
    val pages: List<PageInfo>,
)

/* Sync state matches the server's GET /sync/state response exactly */

@Serializable
data class SyncState(
    val progress: List<SyncProgress> = emptyList(),
    val reports: List<SyncReport> = emptyList(),
    val settings: Map<String, String> = emptyMap(),
    val version: String = "",
)

@Serializable
data class SyncProgress(
    @SerialName("issue_order") val issueOrder: Int,
    @SerialName("current_page") val currentPage: Int = 1,
    @SerialName("is_read") val isRead: Int = 0,
    @SerialName("last_read_at") val lastReadAt: String = "",
)

@Serializable
data class SyncReport(
    val id: Int = 0,
    @SerialName("issue_order") val issueOrder: Int,
    @SerialName("page_num") val pageNum: Int? = null,
    @SerialName("report_type") val reportType: String = "other",
    val description: String = "",
    val resolved: Int = 0,
    @SerialName("created_at") val createdAt: String = "",
)

@Serializable
data class SyncPushResponse(
    val version: String,
    val state: SyncState,
)
