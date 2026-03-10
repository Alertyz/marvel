package com.marvel.reader.data.db

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "issues")
data class IssueEntity(
    @PrimaryKey val orderNum: Int,
    val title: String,
    val issue: Int,
    val phase: String,
    val event: String?,
    val year: String,
    val totalPages: Int = 0,
    val availablePages: Int = 0,
    val downloadedPages: Int = 0,
)

@Entity(tableName = "reading_progress")
data class ProgressEntity(
    @PrimaryKey val orderNum: Int,
    val currentPage: Int = 1,
    val isRead: Boolean = false,
    val updatedAt: String = "",
)

@Entity(tableName = "reports")
data class ReportEntity(
    @PrimaryKey(autoGenerate = true) val id: Int = 0,
    val issueOrder: Int,
    val pageNum: Int?,
    val reportType: String,
    val description: String = "",
    val resolved: Boolean = false,
    val createdAt: String = "",
)

@Entity(tableName = "settings")
data class SettingEntity(
    @PrimaryKey val key: String,
    val value: String,
)
