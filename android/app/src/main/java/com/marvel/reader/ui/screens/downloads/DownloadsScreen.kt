package com.marvel.reader.ui.screens.downloads

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CloudDownload
import androidx.compose.material.icons.filled.CloudOff
import androidx.compose.material.icons.filled.DeleteOutline
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.WifiOff
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import com.marvel.reader.data.db.IssueEntity
import com.marvel.reader.data.repository.ComicRepository
import com.marvel.reader.ui.theme.Accent
import com.marvel.reader.ui.theme.Border
import com.marvel.reader.ui.theme.Danger
import com.marvel.reader.ui.theme.Info
import com.marvel.reader.ui.theme.Success
import com.marvel.reader.ui.theme.Surface
import com.marvel.reader.ui.theme.Surface2
import com.marvel.reader.ui.theme.TextSecondary
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit

private enum class DlFilter { ALL, DOWNLOADED, PENDING }

class DownloadsViewModel(private val repo: ComicRepository) : ViewModel() {
    var issues by mutableStateOf<List<IssueEntity>>(emptyList())
    var filter by mutableStateOf(DlFilter.ALL)
    var activeDownloads by mutableStateOf<Map<Int, Float>>(emptyMap())
    var searchQuery by mutableStateOf("")
    private val semaphore = Semaphore(3)

    init {
        viewModelScope.launch { repo.issuesFlow().collect { issues = it } }
    }

    val isConnected get() = repo.isConnected

    val filteredIssues: List<IssueEntity>
        get() {
            var list = issues.filter { it.availablePages > 0 }
            if (searchQuery.isNotEmpty()) {
                list = list.filter {
                    it.title.contains(searchQuery, ignoreCase = true) ||
                        it.issue.toString().contains(searchQuery)
                }
            }
            return when (filter) {
                DlFilter.ALL -> list
                DlFilter.DOWNLOADED -> list.filter { it.downloadedPages >= it.availablePages }
                DlFilter.PENDING -> list.filter { it.downloadedPages < it.availablePages }
            }
        }

    val storageText: String
        get() {
            val bytes = repo.getStorageUsedBytes()
            return when {
                bytes < 1_048_576 -> "${bytes / 1024} KB"
                bytes < 1_073_741_824 -> "${"%.1f".format(bytes.toFloat() / 1_048_576)} MB"
                else -> "${"%.2f".format(bytes.toFloat() / 1_073_741_824)} GB"
            }
        }

    fun downloadIssue(orderNum: Int) {
        if (orderNum in activeDownloads) return
        viewModelScope.launch {
            semaphore.withPermit {
                try {
                    activeDownloads = activeDownloads + (orderNum to 0f)
                    repo.downloadIssue(orderNum) { downloaded, total ->
                        activeDownloads = activeDownloads + (orderNum to downloaded.toFloat() / total)
                    }
                } catch (_: Exception) {
                } finally {
                    activeDownloads = activeDownloads - orderNum
                }
            }
        }
    }

    fun deleteIssue(orderNum: Int) {
        viewModelScope.launch { repo.deleteIssueDownload(orderNum) }
    }

    fun downloadAllVisible() {
        filteredIssues
            .filter { it.downloadedPages < it.availablePages }
            .forEach { downloadIssue(it.orderNum) }
    }
}

@Composable
fun DownloadsScreen(repository: ComicRepository) {
    val vm: DownloadsViewModel = viewModel(
        factory = object : ViewModelProvider.Factory {
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                @Suppress("UNCHECKED_CAST") return DownloadsViewModel(repository) as T
            }
        },
    )

    val filtered = vm.filteredIssues
    val downloadedCount = vm.issues.count { it.downloadedPages >= it.availablePages && it.availablePages > 0 }
    val hasConnection = vm.isConnected

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
    ) {
        item("header") {
            Spacer(Modifier.height(8.dp))
            Text("Downloads", style = MaterialTheme.typography.headlineMedium)
            Text("Armazenamento: ${vm.storageText}", style = MaterialTheme.typography.bodySmall, color = TextSecondary)
            Spacer(Modifier.height(4.dp))
            Text(
                "$downloadedCount de ${vm.issues.count { it.availablePages > 0 }} edições baixadas",
                style = MaterialTheme.typography.bodySmall,
                color = TextSecondary,
            )
            Spacer(Modifier.height(12.dp))
        }

        if (!hasConnection) {
            item("no_conn") {
                Card(
                    colors = CardDefaults.cardColors(containerColor = Danger.copy(alpha = 0.12f)),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.WifiOff, null, tint = Danger, modifier = Modifier.size(20.dp))
                        Spacer(Modifier.width(8.dp))
                        Text("Conecte ao PC para baixar edições", style = MaterialTheme.typography.bodySmall, color = Danger)
                    }
                }
                Spacer(Modifier.height(12.dp))
            }
        }

        item("search") {
            OutlinedTextField(
                value = vm.searchQuery,
                onValueChange = { vm.searchQuery = it },
                placeholder = { Text("Buscar...") },
                leadingIcon = { Icon(Icons.Default.Search, null, modifier = Modifier.size(20.dp)) },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = Accent, unfocusedContainerColor = Surface),
                shape = RoundedCornerShape(12.dp),
            )
            Spacer(Modifier.height(8.dp))

            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                FilterChip(
                    selected = vm.filter == DlFilter.ALL,
                    onClick = { vm.filter = DlFilter.ALL },
                    label = { Text("Todas") },
                )
                FilterChip(
                    selected = vm.filter == DlFilter.DOWNLOADED,
                    onClick = { vm.filter = DlFilter.DOWNLOADED },
                    label = { Text("Baixadas") },
                )
                FilterChip(
                    selected = vm.filter == DlFilter.PENDING,
                    onClick = { vm.filter = DlFilter.PENDING },
                    label = { Text("Pendentes") },
                )
            }
            Spacer(Modifier.height(6.dp))

            if (hasConnection && filtered.any { it.downloadedPages < it.availablePages }) {
                Button(
                    onClick = { vm.downloadAllVisible() },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(containerColor = Info),
                ) {
                    Icon(Icons.Default.CloudDownload, null, modifier = Modifier.size(18.dp))
                    Spacer(Modifier.width(6.dp))
                    Text("Baixar tudo visível", fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.onSecondary)
                }
                Spacer(Modifier.height(6.dp))
            }
        }

        items(filtered, key = { it.orderNum }) { issue ->
            DownloadCard(
                issue = issue,
                isDownloaded = issue.downloadedPages >= issue.availablePages && issue.availablePages > 0,
                progress = vm.activeDownloads[issue.orderNum],
                hasConnection = hasConnection,
                onDownload = { vm.downloadIssue(issue.orderNum) },
                onDelete = { vm.deleteIssue(issue.orderNum) },
            )
        }

        item("bottom") { Spacer(Modifier.height(80.dp)) }
    }
}

@Composable
private fun DownloadCard(
    issue: IssueEntity,
    isDownloaded: Boolean,
    progress: Float?,
    hasConnection: Boolean,
    onDownload: () -> Unit,
    onDelete: () -> Unit,
) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(vertical = 2.dp),
        colors = CardDefaults.cardColors(containerColor = Surface),
        border = BorderStroke(
            1.dp,
            when {
                isDownloaded -> Success.copy(alpha = 0.4f)
                progress != null -> Info.copy(alpha = 0.4f)
                else -> Border
            },
        ),
        shape = RoundedCornerShape(8.dp),
    ) {
        Column(Modifier.padding(10.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(
                        "${issue.title} #${issue.issue}",
                        style = MaterialTheme.typography.bodyMedium,
                        fontWeight = FontWeight.Medium,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                    )
                    Text(
                        "${issue.availablePages} páginas • #${issue.orderNum}",
                        style = MaterialTheme.typography.bodySmall,
                        color = TextSecondary,
                    )
                }
                when {
                    progress != null -> CircularProgressIndicator(
                        progress = { progress },
                        modifier = Modifier.size(28.dp),
                        strokeWidth = 3.dp,
                        color = Info,
                    )
                    isDownloaded -> IconButton(onClick = onDelete, modifier = Modifier.size(32.dp)) {
                        Icon(Icons.Default.DeleteOutline, "Apagar", tint = Danger, modifier = Modifier.size(20.dp))
                    }
                    hasConnection -> IconButton(onClick = onDownload, modifier = Modifier.size(32.dp)) {
                        Icon(Icons.Default.CloudDownload, "Baixar", tint = Info, modifier = Modifier.size(20.dp))
                    }
                    else -> Icon(Icons.Default.CloudOff, null, tint = TextSecondary, modifier = Modifier.size(20.dp))
                }
            }

            if (progress != null) {
                Spacer(Modifier.height(4.dp))
                LinearProgressIndicator(
                    progress = { progress },
                    modifier = Modifier.fillMaxWidth().height(3.dp),
                    color = Info,
                    trackColor = Surface2,
                )
            } else if (issue.downloadedPages in 1 until issue.availablePages) {
                Spacer(Modifier.height(4.dp))
                LinearProgressIndicator(
                    progress = { issue.downloadedPages.toFloat() / issue.availablePages },
                    modifier = Modifier.fillMaxWidth().height(3.dp),
                    color = Accent,
                    trackColor = Surface2,
                )
                Text(
                    "${issue.downloadedPages}/${issue.availablePages} páginas",
                    style = MaterialTheme.typography.labelSmall,
                    color = TextSecondary,
                )
            }
        }
    }
}
