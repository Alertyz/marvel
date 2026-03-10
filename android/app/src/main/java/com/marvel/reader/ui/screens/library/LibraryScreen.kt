package com.marvel.reader.ui.screens.library

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.CloudOff
import androidx.compose.material.icons.filled.RadioButtonUnchecked
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.ScrollableTabRow
import androidx.compose.material3.Tab
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import com.marvel.reader.data.db.IssueEntity
import com.marvel.reader.data.db.ProgressEntity
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

private val SERIES_COLORS = listOf(
    Color(0xFFE04060), Color(0xFF40A0E0), Color(0xFF40E080), Color(0xFFF0C040),
    Color(0xFFC060E0), Color(0xFFE08040), Color(0xFF60E0C0), Color(0xFFE060A0),
    Color(0xFF80A0E0), Color(0xFFA0E040), Color(0xFFE0A060), Color(0xFF6080E0),
)

private data class IssueWithProgress(
    val issue: IssueEntity,
    val progress: ProgressEntity?,
) {
    val isRead get() = progress?.isRead == true
    val currentPage get() = progress?.currentPage ?: 1
}

class LibraryViewModel(private val repo: ComicRepository) : ViewModel() {
    var issues by mutableStateOf<List<IssueEntity>>(emptyList())
    var progressMap by mutableStateOf<Map<Int, ProgressEntity>>(emptyMap())
    var flagged by mutableStateOf<Set<Int>>(emptySet())
    var searchQuery by mutableStateOf("")
    var selectedPhase by mutableStateOf("")

    init {
        viewModelScope.launch { repo.issuesFlow().collect { issues = it } }
        viewModelScope.launch {
            repo.progressFlow().collect { list -> progressMap = list.associateBy { it.orderNum } }
        }
        viewModelScope.launch { repo.flaggedFlow().collect { flagged = it.toSet() } }
    }

    val phases get() = issues.map { it.phase }.distinct()
    val totalIssues get() = issues.size
    val readCount get() = issues.count { progressMap[it.orderNum]?.isRead == true }

    fun getBookmarkOrder(): Int? {
        for (iss in issues) {
            if (progressMap[iss.orderNum]?.isRead != true) return iss.orderNum
        }
        return null
    }

    fun toggleRead(orderNum: Int) {
        viewModelScope.launch { repo.toggleRead(orderNum) }
    }

    fun markAllBefore(orderNum: Int) {
        viewModelScope.launch { repo.markAllBeforeAsRead(orderNum) }
    }

    fun getFilteredGrouped(): List<Pair<String, List<IssueWithProgress>>> {
        val filtered = issues.filter { iss ->
            val matchSearch = searchQuery.isEmpty() ||
                iss.title.contains(searchQuery, ignoreCase = true) ||
                iss.issue.toString().contains(searchQuery) ||
                (iss.event ?: "").contains(searchQuery, ignoreCase = true)
            val matchPhase = selectedPhase.isEmpty() || iss.phase == selectedPhase
            matchSearch && matchPhase
        }
        return filtered
            .groupBy { it.phase }
            .map { (phase, list) ->
                phase to list.map { IssueWithProgress(it, progressMap[it.orderNum]) }
            }
    }

    /** Stable color by series title. */
    fun seriesColor(title: String): Color {
        val idx = issues.map { it.title }.distinct().indexOf(title)
        return if (idx >= 0) SERIES_COLORS[idx % SERIES_COLORS.size] else Accent
    }
}

@Composable
fun LibraryScreen(
    repository: ComicRepository,
    onOpenReader: (orderNum: Int, page: Int) -> Unit,
) {
    val vm: LibraryViewModel = viewModel(
        factory = object : ViewModelProvider.Factory {
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                @Suppress("UNCHECKED_CAST") return LibraryViewModel(repository) as T
            }
        },
    )

    val phases = vm.getFilteredGrouped()
    val total = vm.totalIssues
    val readCount = vm.readCount
    val pct = if (total > 0) readCount * 100 / total else 0

    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 12.dp),
    ) {
        // ── Header ──
        item("header") {
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("Marvel Comic Reader", style = MaterialTheme.typography.headlineLarge, color = Accent)
                Text(
                    "Krakoa → From the Ashes → Shadows of Tomorrow",
                    style = MaterialTheme.typography.bodySmall,
                    color = TextSecondary,
                )
                Spacer(Modifier.height(16.dp))
            }
        }

        // ── Stats row ──
        item("stats") {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                StatCard("Total", "$total", Accent, Modifier.weight(1f))
                StatCard("Lidas", "$readCount", Success, Modifier.weight(1f))
                StatCard("Faltam", "${total - readCount}", Danger, Modifier.weight(1f))
                StatCard("$pct%", "Progresso", Info, Modifier.weight(1f))
            }
            Spacer(Modifier.height(8.dp))
            LinearProgressIndicator(
                progress = { if (total > 0) readCount.toFloat() / total else 0f },
                modifier = Modifier.fillMaxWidth().height(4.dp).clip(RoundedCornerShape(2.dp)),
                color = Accent,
                trackColor = Surface2,
            )
            Spacer(Modifier.height(16.dp))
        }

        // ── Search + filters ──
        item("controls") {
            OutlinedTextField(
                value = vm.searchQuery,
                onValueChange = { vm.searchQuery = it },
                placeholder = { Text("Buscar série ou edição...") },
                leadingIcon = { Icon(Icons.Default.Search, null, modifier = Modifier.size(20.dp)) },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = Accent,
                    unfocusedContainerColor = Surface,
                ),
                shape = RoundedCornerShape(12.dp),
            )
            Spacer(Modifier.height(8.dp))

            if (vm.phases.size > 1) {
                val allPhases = listOf("") + vm.phases
                ScrollableTabRow(
                    selectedTabIndex = allPhases.indexOf(vm.selectedPhase).coerceAtLeast(0),
                    edgePadding = 0.dp,
                    containerColor = Color.Transparent,
                    divider = {},
                ) {
                    Tab(
                        selected = vm.selectedPhase.isEmpty(),
                        onClick = { vm.selectedPhase = "" },
                    ) {
                        Text(
                            "Todas",
                            Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                            style = MaterialTheme.typography.labelMedium,
                        )
                    }
                    vm.phases.forEach { phase ->
                        Tab(
                            selected = vm.selectedPhase == phase,
                            onClick = { vm.selectedPhase = phase },
                        ) {
                            Text(
                                phase,
                                Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                                style = MaterialTheme.typography.labelMedium,
                                maxLines = 1,
                            )
                        }
                    }
                }
            }

            Spacer(Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                AssistChip(
                    onClick = { /* scroll handled externally */ },
                    label = { Text("📍 Bookmark", style = MaterialTheme.typography.labelMedium) },
                )
                val bookmarkOrder = vm.getBookmarkOrder()
                if (bookmarkOrder != null) {
                    AssistChip(
                        onClick = { vm.markAllBefore(bookmarkOrder) },
                        label = {
                            Text("✓ Marcar anteriores", style = MaterialTheme.typography.labelMedium)
                        },
                    )
                }
            }
            Spacer(Modifier.height(12.dp))
        }

        // ── Empty state ──
        if (total == 0) {
            item("empty") {
                Box(
                    Modifier.fillMaxWidth().padding(40.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(Icons.Default.CloudOff, null, tint = TextSecondary, modifier = Modifier.size(48.dp))
                        Spacer(Modifier.height(12.dp))
                        Text("Biblioteca vazia", style = MaterialTheme.typography.titleMedium, color = TextSecondary)
                        Text("Conecte ao PC e sincronize", style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                    }
                }
            }
        }

        // ── Phase sections ──
        phases.forEach { (phaseName, issueList) ->
            val readInPhase = issueList.count { it.isRead }
            val bookmarkOrder = vm.getBookmarkOrder()
            val isBookmarkPhase = issueList.any { !it.isRead && it.issue.orderNum == bookmarkOrder }

            item(key = "phase_$phaseName") {
                PhaseHeader(phaseName, readInPhase, issueList.size, isBookmarkPhase)
            }

            var lastEvent = ""
            issueList.forEach { iwp ->
                val event = iwp.issue.event
                if (event != null && event != lastEvent) {
                    lastEvent = event
                    item(key = "ev_${phaseName}_${event}_${iwp.issue.orderNum}") {
                        EventBanner(event)
                    }
                } else if (event == null && lastEvent.isNotEmpty()) {
                    lastEvent = ""
                }

                item(key = "iss_${iwp.issue.orderNum}") {
                    IssueCard(
                        iwp = iwp,
                        color = vm.seriesColor(iwp.issue.title),
                        isFlagged = iwp.issue.orderNum in vm.flagged,
                        isBookmark = iwp.issue.orderNum == bookmarkOrder,
                        onTap = { onOpenReader(iwp.issue.orderNum, iwp.currentPage) },
                        onToggleRead = { vm.toggleRead(iwp.issue.orderNum) },
                    )
                }
            }

            item(key = "sp_$phaseName") { Spacer(Modifier.height(8.dp)) }
        }

        item("bottom_spacer") { Spacer(Modifier.height(80.dp)) }
    }
}

// ── Components ──────────────────────────────────────────────

@Composable
private fun StatCard(top: String, bottom: String, color: Color, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = Surface),
        border = BorderStroke(1.dp, Border),
        shape = RoundedCornerShape(10.dp),
    ) {
        Column(Modifier.padding(10.dp), horizontalAlignment = Alignment.CenterHorizontally) {
            Text(top, style = MaterialTheme.typography.titleLarge, color = color, fontWeight = FontWeight.Bold)
            Text(bottom, style = MaterialTheme.typography.labelSmall, color = TextSecondary)
        }
    }
}

@Composable
private fun PhaseHeader(name: String, read: Int, total: Int, isBookmarkPhase: Boolean) {
    Card(
        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
        colors = CardDefaults.cardColors(containerColor = Surface),
        border = BorderStroke(1.dp, if (isBookmarkPhase) Danger else Border),
        shape = RoundedCornerShape(10.dp),
    ) {
        Row(
            Modifier.padding(horizontal = 14.dp, vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(name, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
            Text(
                "$read/$total",
                style = MaterialTheme.typography.labelMedium,
                color = TextSecondary,
                modifier = Modifier
                    .background(Surface2, RoundedCornerShape(20.dp))
                    .padding(horizontal = 8.dp, vertical = 2.dp),
            )
        }
    }
}

@Composable
private fun EventBanner(event: String) {
    Box(
        Modifier
            .fillMaxWidth()
            .padding(vertical = 2.dp)
            .background(
                Brush.horizontalGradient(listOf(Surface2, Color.Transparent)),
                RoundedCornerShape(4.dp),
            )
            .padding(start = 12.dp, top = 6.dp, bottom = 6.dp),
    ) {
        Text(event, style = MaterialTheme.typography.labelMedium, color = Accent, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
private fun IssueCard(
    iwp: IssueWithProgress,
    color: Color,
    isFlagged: Boolean,
    isBookmark: Boolean,
    onTap: () -> Unit,
    onToggleRead: () -> Unit,
) {
    val iss = iwp.issue
    Card(
        onClick = onTap,
        modifier = Modifier.fillMaxWidth().padding(vertical = 2.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (iwp.isRead) Surface.copy(alpha = 0.5f) else Surface,
        ),
        border = BorderStroke(
            1.dp,
            when {
                isBookmark -> Danger
                iss.downloadedPages > 0 -> Success.copy(alpha = 0.5f)
                else -> Border
            },
        ),
        shape = RoundedCornerShape(8.dp),
    ) {
        Row(
            Modifier.padding(horizontal = 10.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(Modifier.size(8.dp).clip(CircleShape).background(color))
            Spacer(Modifier.width(8.dp))

            Column(Modifier.weight(1f)) {
                Text(
                    "${iss.title} #${iss.issue}${if (isFlagged) " ⚠️" else ""}",
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Medium,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                )
                Row {
                    Text("${iss.year}", style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                    if (iss.downloadedPages > 0) {
                        Spacer(Modifier.width(6.dp))
                        Text(
                            "📱 ${iss.downloadedPages}p",
                            style = MaterialTheme.typography.bodySmall,
                            color = Success,
                        )
                    }
                }
            }

            if (isBookmark) {
                Text("📍", modifier = Modifier.padding(end = 4.dp))
            }

            Text(
                "#${iss.orderNum}",
                style = MaterialTheme.typography.labelSmall,
                color = TextSecondary,
                modifier = Modifier
                    .background(Surface2, RoundedCornerShape(10.dp))
                    .padding(horizontal = 5.dp, vertical = 1.dp),
            )
            Spacer(Modifier.width(6.dp))

            IconButton(onClick = onToggleRead, modifier = Modifier.size(28.dp)) {
                if (iwp.isRead) {
                    Icon(Icons.Default.CheckCircle, "Lida", tint = Success, modifier = Modifier.size(20.dp))
                } else {
                    Icon(Icons.Default.RadioButtonUnchecked, "Não lida", tint = TextSecondary, modifier = Modifier.size(20.dp))
                }
            }
        }
    }
}
