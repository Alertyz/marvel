package com.marvel.reader.data.repository

import com.marvel.reader.data.api.SyncApi
import com.marvel.reader.data.api.SyncProgress
import com.marvel.reader.data.api.SyncReport
import com.marvel.reader.data.api.SyncState
import com.marvel.reader.data.db.AppDatabase
import com.marvel.reader.data.db.IssueEntity
import com.marvel.reader.data.db.ProgressEntity
import com.marvel.reader.data.db.ReportEntity
import com.marvel.reader.data.db.SettingEntity
import com.marvel.reader.data.storage.ImageStorage
import kotlinx.coroutines.flow.Flow
import java.time.Instant

class ComicRepository(
    private val db: AppDatabase,
    private val api: SyncApi,
    private val storage: ImageStorage,
) {
    private val issueDao = db.issueDao()
    private val progressDao = db.progressDao()
    private val reportDao = db.reportDao()
    private val settingDao = db.settingDao()

    // ── Connection ─────────────────────────────────────────

    val isConnected get() = api.isConfigured

    suspend fun connect(host: String, port: Int = 8080): com.marvel.reader.data.api.HandshakeResponse {
        api.setServer(host, port)
        val hs = api.handshake()
        settingDao.upsert(SettingEntity("server_host", host))
        settingDao.upsert(SettingEntity("server_port", port.toString()))
        return hs
    }

    suspend fun tryReconnect(): Boolean {
        val host = settingDao.get("server_host")?.value ?: return false
        val port = settingDao.get("server_port")?.value?.toIntOrNull() ?: 8080
        return try {
            api.setServer(host, port)
            api.handshake()
            true
        } catch (_: Exception) {
            false
        }
    }

    // ── Catalog & Sync ─────────────────────────────────────

    suspend fun syncCatalog() {
        val catalog = api.getCatalog()
        val entities = catalog.map { item ->
            val existing = issueDao.getByOrder(item.orderNum)
            IssueEntity(
                orderNum = item.orderNum,
                title = item.title,
                issue = item.issue,
                phase = item.phase,
                event = item.event,
                year = item.year,
                totalPages = item.availablePages,
                availablePages = item.availablePages,
                downloadedPages = existing?.downloadedPages
                    ?: storage.getDownloadedPageCount(item.orderNum),
            )
        }
        issueDao.upsertAll(entities)
    }

    suspend fun syncState() {
        val remoteState = api.getState()

        // Merge progress — last-write-wins based on timestamp
        for (rp in remoteState.progress) {
            val local = progressDao.get(rp.issueOrder)
            if (local == null || rp.lastReadAt > local.updatedAt) {
                progressDao.upsert(
                    ProgressEntity(
                        orderNum = rp.issueOrder,
                        currentPage = rp.currentPage,
                        isRead = rp.isRead != 0,
                        updatedAt = rp.lastReadAt,
                    )
                )
            }
        }

        // Push local state to server
        val localProgress = progressDao.getAll().map {
            SyncProgress(
                issueOrder = it.orderNum,
                currentPage = it.currentPage,
                isRead = if (it.isRead) 1 else 0,
                lastReadAt = it.updatedAt,
            )
        }
        val localReports = reportDao.getUnresolved().map {
            SyncReport(
                id = it.id,
                issueOrder = it.issueOrder,
                pageNum = it.pageNum,
                reportType = it.reportType,
                description = it.description,
                resolved = if (it.resolved) 1 else 0,
                createdAt = it.createdAt,
            )
        }
        val localSettings = settingDao.getAll()
            .filter { it.key !in setOf("server_host", "server_port") }
            .associate { it.key to it.value }

        val pushResult = api.pushState(
            SyncState(localProgress, localReports, localSettings)
        )

        // Apply merged state from server response
        for (rp in pushResult.state.progress) {
            progressDao.upsert(
                ProgressEntity(
                    orderNum = rp.issueOrder,
                    currentPage = rp.currentPage,
                    isRead = rp.isRead != 0,
                    updatedAt = rp.lastReadAt,
                )
            )
        }
    }

    // ── Issues ─────────────────────────────────────────────

    fun issuesFlow(): Flow<List<IssueEntity>> = issueDao.allFlow()
    fun progressFlow(): Flow<List<ProgressEntity>> = progressDao.allFlow()
    fun flaggedFlow(): Flow<List<Int>> = reportDao.flaggedFlow()

    suspend fun getIssue(orderNum: Int) = issueDao.getByOrder(orderNum)
    suspend fun getAllIssues() = issueDao.getAll()
    suspend fun getProgress(orderNum: Int) = progressDao.get(orderNum)

    // ── Reading Progress ───────────────────────────────────

    suspend fun updateProgress(orderNum: Int, currentPage: Int) {
        val now = Instant.now().toString()
        val existing = progressDao.get(orderNum)
        progressDao.upsert(
            ProgressEntity(
                orderNum = orderNum,
                currentPage = currentPage,
                isRead = existing?.isRead ?: false,
                updatedAt = now,
            )
        )
    }

    suspend fun toggleRead(orderNum: Int): Boolean {
        val now = Instant.now().toString()
        val existing = progressDao.get(orderNum)
        val newState = !(existing?.isRead ?: false)
        progressDao.upsert(
            ProgressEntity(
                orderNum = orderNum,
                currentPage = existing?.currentPage ?: 1,
                isRead = newState,
                updatedAt = now,
            )
        )
        return newState
    }

    suspend fun markAsRead(orderNum: Int) {
        val now = Instant.now().toString()
        val existing = progressDao.get(orderNum)
        progressDao.upsert(
            ProgressEntity(
                orderNum = orderNum,
                currentPage = existing?.currentPage ?: 1,
                isRead = true,
                updatedAt = now,
            )
        )
    }

    suspend fun markAllBeforeAsRead(orderNum: Int) {
        progressDao.markAllBeforeAsRead(orderNum, Instant.now().toString())
    }

    // ── Reports ────────────────────────────────────────────

    suspend fun addReport(issueOrder: Int, pageNum: Int?, type: String, desc: String): Long {
        return reportDao.insert(
            ReportEntity(
                issueOrder = issueOrder,
                pageNum = pageNum,
                reportType = type,
                description = desc,
                createdAt = Instant.now().toString(),
            )
        )
    }

    // ── Downloads ──────────────────────────────────────────

    suspend fun downloadIssue(
        orderNum: Int,
        onProgress: (downloaded: Int, total: Int) -> Unit = { _, _ -> },
    ) {
        val pagesResp = api.getIssuePages(orderNum)
        val total = pagesResp.pages.size
        var downloaded = 0
        for (page in pagesResp.pages) {
            if (!storage.hasPage(orderNum, page.pageNum)) {
                val data = api.downloadPage(orderNum, page.pageNum)
                storage.savePage(orderNum, page.pageNum, data)
            }
            downloaded++
            onProgress(downloaded, total)
        }
        issueDao.updateDownloadedPages(orderNum, downloaded)
    }

    fun hasPage(orderNum: Int, pageNum: Int) = storage.hasPage(orderNum, pageNum)
    fun getPageFile(orderNum: Int, pageNum: Int) = storage.getPageFile(orderNum, pageNum)

    fun getPageUrl(orderNum: Int, pageNum: Int): String? =
        if (api.isConfigured) api.getPageUrl(orderNum, pageNum) else null

    suspend fun deleteIssueDownload(orderNum: Int) {
        storage.deleteIssue(orderNum)
        issueDao.updateDownloadedPages(orderNum, 0)
    }

    fun getStorageUsedBytes() = storage.getStorageUsedBytes()

    // ── Settings ───────────────────────────────────────────

    suspend fun getSetting(key: String) = settingDao.get(key)?.value
    suspend fun setSetting(key: String, value: String) =
        settingDao.upsert(SettingEntity(key, value))
}
