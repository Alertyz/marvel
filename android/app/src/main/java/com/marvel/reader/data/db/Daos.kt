package com.marvel.reader.data.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import androidx.room.Upsert
import kotlinx.coroutines.flow.Flow

@Dao
interface IssueDao {
    @Query("SELECT * FROM issues ORDER BY orderNum ASC")
    fun allFlow(): Flow<List<IssueEntity>>

    @Query("SELECT * FROM issues ORDER BY orderNum ASC")
    suspend fun getAll(): List<IssueEntity>

    @Query("SELECT * FROM issues WHERE orderNum = :orderNum")
    suspend fun getByOrder(orderNum: Int): IssueEntity?

    @Upsert
    suspend fun upsertAll(issues: List<IssueEntity>)

    @Query("UPDATE issues SET downloadedPages = :count WHERE orderNum = :orderNum")
    suspend fun updateDownloadedPages(orderNum: Int, count: Int)

    @Query("SELECT COUNT(*) FROM issues")
    suspend fun count(): Int
}

@Dao
interface ProgressDao {
    @Query("SELECT * FROM reading_progress WHERE orderNum = :orderNum")
    suspend fun get(orderNum: Int): ProgressEntity?

    @Query("SELECT * FROM reading_progress")
    suspend fun getAll(): List<ProgressEntity>

    @Query("SELECT * FROM reading_progress")
    fun allFlow(): Flow<List<ProgressEntity>>

    @Upsert
    suspend fun upsert(progress: ProgressEntity)

    @Upsert
    suspend fun upsertAll(list: List<ProgressEntity>)

    @Query("UPDATE reading_progress SET isRead = 1, updatedAt = :timestamp WHERE orderNum <= :orderNum")
    suspend fun markAllBeforeAsRead(orderNum: Int, timestamp: String)
}

@Dao
interface ReportDao {
    @Insert
    suspend fun insert(report: ReportEntity): Long

    @Query("SELECT * FROM reports WHERE resolved = 0 ORDER BY id DESC")
    suspend fun getUnresolved(): List<ReportEntity>

    @Query("SELECT DISTINCT issueOrder FROM reports WHERE resolved = 0")
    fun flaggedFlow(): Flow<List<Int>>

    @Upsert
    suspend fun upsertAll(reports: List<ReportEntity>)
}

@Dao
interface SettingDao {
    @Query("SELECT * FROM settings WHERE `key` = :key")
    suspend fun get(key: String): SettingEntity?

    @Query("SELECT * FROM settings")
    suspend fun getAll(): List<SettingEntity>

    @Upsert
    suspend fun upsert(setting: SettingEntity)
}
