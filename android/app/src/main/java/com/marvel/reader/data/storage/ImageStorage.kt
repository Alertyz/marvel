package com.marvel.reader.data.storage

import android.content.Context
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

class ImageStorage(private val context: Context) {

    private val baseDir get() = File(context.filesDir, "comics")

    private fun issueDir(orderNum: Int): File =
        File(baseDir, "issue_$orderNum").also { it.mkdirs() }

    fun getPageFile(orderNum: Int, pageNum: Int): File =
        File(issueDir(orderNum), "page_${pageNum.toString().padStart(3, '0')}.jpg")

    fun hasPage(orderNum: Int, pageNum: Int): Boolean =
        getPageFile(orderNum, pageNum).exists()

    fun getDownloadedPageCount(orderNum: Int): Int {
        val dir = File(baseDir, "issue_$orderNum")
        if (!dir.exists()) return 0
        return dir.listFiles()?.count {
            it.extension in listOf("jpg", "png", "webp")
        } ?: 0
    }

    suspend fun savePage(orderNum: Int, pageNum: Int, data: ByteArray) =
        withContext(Dispatchers.IO) {
            getPageFile(orderNum, pageNum).writeBytes(data)
        }

    suspend fun deleteIssue(orderNum: Int) = withContext(Dispatchers.IO) {
        File(baseDir, "issue_$orderNum").deleteRecursively()
    }

    fun getStorageUsedBytes(): Long =
        if (baseDir.exists()) baseDir.walkTopDown().filter { it.isFile }.sumOf { it.length() } else 0L
}
