package com.marvel.reader.ui.screens.reader

import android.net.Uri
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.ImageNotSupported
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Slider
import androidx.compose.material3.SliderDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.zIndex
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import coil3.compose.AsyncImage
import coil3.request.ImageRequest
import coil3.request.crossfade
import com.marvel.reader.data.db.IssueEntity
import com.marvel.reader.data.repository.ComicRepository
import com.marvel.reader.ui.theme.Accent
import com.marvel.reader.ui.theme.Danger
import com.marvel.reader.ui.theme.Info
import com.marvel.reader.ui.theme.Success
import com.marvel.reader.ui.theme.Surface
import com.marvel.reader.ui.theme.Surface2
import com.marvel.reader.ui.theme.TextPrimary
import com.marvel.reader.ui.theme.TextSecondary
import kotlinx.coroutines.launch

// ═══════════════════════════════════════════════════════════
//  ViewModel
// ═══════════════════════════════════════════════════════════

class ReaderViewModel(
    private val repo: ComicRepository,
    val orderNum: Int,
    startPage: Int,
) : ViewModel() {
    var issue by mutableStateOf<IssueEntity?>(null)
    var totalPages by mutableStateOf(0)
    var currentPage by mutableStateOf(startPage)
    var isRead by mutableStateOf(false)
    var scrollMode by mutableStateOf(false)
    var controlsVisible by mutableStateOf(true)
    var showReport by mutableStateOf(false)
    var isFlagged by mutableStateOf(false)
    var showComplete by mutableStateOf(false)
    var nextIssue by mutableStateOf<IssueEntity?>(null)

    init {
        viewModelScope.launch {
            issue = repo.getIssue(orderNum)
            issue?.let { iss ->
                totalPages = maxOf(iss.downloadedPages, iss.availablePages)
                val progress = repo.getProgress(orderNum)
                isRead = progress?.isRead == true
                currentPage = startPage.coerceIn(1, maxOf(totalPages, 1))
            }
            // Find next readable issue
            val all = repo.getAllIssues()
            nextIssue = all.firstOrNull {
                it.orderNum > orderNum && (it.downloadedPages > 0 || it.availablePages > 0)
            }
        }
    }

    fun getPageModel(page: Int): Any {
        val file = repo.getPageFile(orderNum, page)
        return when {
            file.exists() -> Uri.fromFile(file)
            repo.isConnected -> repo.getPageUrl(orderNum, page) ?: ""
            else -> ""
        }
    }

    fun onPageChanged(page: Int) {
        currentPage = page.coerceIn(1, maxOf(totalPages, 1))
        viewModelScope.launch { repo.updateProgress(orderNum, currentPage) }
    }

    fun toggleRead() {
        viewModelScope.launch { isRead = repo.toggleRead(orderNum) }
    }

    fun markAsRead() {
        viewModelScope.launch { repo.markAsRead(orderNum); isRead = true }
    }

    fun onLastPage() {
        if (!isRead) markAsRead()
        showComplete = true
    }

    fun submitReport(type: String, desc: String) {
        viewModelScope.launch {
            repo.addReport(orderNum, currentPage, type, desc)
            isFlagged = true
            showReport = false
        }
    }
}

// ═══════════════════════════════════════════════════════════
//  Screen
// ═══════════════════════════════════════════════════════════

@Composable
fun ReaderScreen(
    repository: ComicRepository,
    orderNum: Int,
    startPage: Int,
    onBack: () -> Unit,
    onNavigateToIssue: (Int) -> Unit,
) {
    val vm: ReaderViewModel = viewModel(
        key = "reader_$orderNum",
        factory = object : ViewModelProvider.Factory {
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                @Suppress("UNCHECKED_CAST")
                return ReaderViewModel(repository, orderNum, startPage) as T
            }
        },
    )

    // Loading state
    val issue = vm.issue
    if (issue == null) {
        Box(Modifier.fillMaxSize().background(Color.Black), contentAlignment = Alignment.Center) {
            CircularProgressIndicator(color = Accent)
        }
        return
    }

    // No pages state
    if (vm.totalPages == 0) {
        Box(Modifier.fillMaxSize().background(Color.Black), contentAlignment = Alignment.Center) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Icon(Icons.Default.ImageNotSupported, null, tint = TextSecondary, modifier = Modifier.size(48.dp))
                Spacer(Modifier.height(12.dp))
                Text("Sem páginas disponíveis", color = TextSecondary)
                Text("Baixe esta edição primeiro", style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                Spacer(Modifier.height(16.dp))
                OutlinedButton(onClick = onBack) { Text("Voltar") }
            }
        }
        return
    }

    Box(Modifier.fillMaxSize().background(Color.Black)) {

        // ── Content ──
        if (vm.scrollMode) {
            ScrollReader(vm)
        } else {
            PagedReader(vm)
        }

        // ── Top bar ──
        AnimatedVisibility(
            visible = vm.controlsVisible,
            enter = fadeIn() + slideInVertically(),
            exit = fadeOut() + slideOutVertically(),
            modifier = Modifier.align(Alignment.TopCenter).zIndex(10f),
        ) {
            Surface(color = Color.Black.copy(alpha = 0.85f), modifier = Modifier.fillMaxWidth()) {
                Row(
                    Modifier.statusBarsPadding().padding(horizontal = 4.dp, vertical = 4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    IconButton(onClick = onBack) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, "Voltar", tint = TextPrimary)
                    }
                    Text(
                        "${issue.title} #${issue.issue}",
                        style = MaterialTheme.typography.titleMedium,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis,
                        modifier = Modifier.weight(1f),
                    )
                    Text(
                        "${vm.currentPage}/${vm.totalPages}",
                        style = MaterialTheme.typography.bodySmall,
                        color = TextSecondary,
                        modifier = Modifier.padding(end = 12.dp),
                    )
                }
            }
        }

        // ── Bottom bar ──
        AnimatedVisibility(
            visible = vm.controlsVisible,
            enter = fadeIn() + slideInVertically(initialOffsetY = { it }),
            exit = fadeOut() + slideOutVertically(targetOffsetY = { it }),
            modifier = Modifier.align(Alignment.BottomCenter).zIndex(10f),
        ) {
            Surface(color = Color.Black.copy(alpha = 0.85f), modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.navigationBarsPadding().padding(8.dp)) {
                    if (vm.totalPages > 1) {
                        Slider(
                            value = vm.currentPage.toFloat(),
                            onValueChange = { vm.onPageChanged(it.toInt()) },
                            valueRange = 1f..vm.totalPages.toFloat(),
                            modifier = Modifier.fillMaxWidth(),
                            colors = SliderDefaults.colors(
                                thumbColor = Accent,
                                activeTrackColor = Accent,
                            ),
                        )
                    }
                    Row(
                        Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(6.dp),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        // Read toggle
                        FilledTonalButton(
                            onClick = { vm.toggleRead() },
                            modifier = Modifier.height(34.dp),
                            contentPadding = PaddingValues(horizontal = 10.dp),
                            colors = ButtonDefaults.filledTonalButtonColors(
                                containerColor = if (vm.isRead) Success.copy(alpha = 0.2f) else Surface2,
                            ),
                        ) {
                            Text(
                                if (vm.isRead) "✓ Lido" else "Marcar Lido",
                                style = MaterialTheme.typography.labelMedium,
                                color = if (vm.isRead) Success else TextPrimary,
                            )
                        }

                        // Scroll mode toggle
                        FilledTonalButton(
                            onClick = { vm.scrollMode = !vm.scrollMode },
                            modifier = Modifier.height(34.dp),
                            contentPadding = PaddingValues(horizontal = 10.dp),
                            colors = ButtonDefaults.filledTonalButtonColors(
                                containerColor = if (vm.scrollMode) Info.copy(alpha = 0.2f) else Surface2,
                            ),
                        ) {
                            Text(
                                if (vm.scrollMode) "📜 Scroll" else "📄 Página",
                                style = MaterialTheme.typography.labelMedium,
                                color = if (vm.scrollMode) Info else TextPrimary,
                            )
                        }

                        Spacer(Modifier.weight(1f))

                        // Report
                        FilledTonalButton(
                            onClick = { vm.showReport = true },
                            modifier = Modifier.height(34.dp),
                            contentPadding = PaddingValues(horizontal = 10.dp),
                            colors = ButtonDefaults.filledTonalButtonColors(
                                containerColor = if (vm.isFlagged) Danger.copy(alpha = 0.2f) else Surface2,
                            ),
                        ) {
                            Text(
                                if (vm.isFlagged) "⚠️ Reportado" else "⚠️",
                                style = MaterialTheme.typography.labelMedium,
                            )
                        }

                        // Next issue shortcut
                        vm.nextIssue?.let { next ->
                            FilledTonalButton(
                                onClick = { onNavigateToIssue(next.orderNum) },
                                modifier = Modifier.height(34.dp),
                                contentPadding = PaddingValues(horizontal = 10.dp),
                                colors = ButtonDefaults.filledTonalButtonColors(
                                    containerColor = Info.copy(alpha = 0.2f),
                                ),
                            ) {
                                Text("→", style = MaterialTheme.typography.titleMedium, color = Info)
                            }
                        }
                    }
                }
            }
        }

        // ── Issue complete overlay ──
        if (vm.showComplete) {
            Box(
                Modifier
                    .fillMaxSize()
                    .background(Color.Black.copy(alpha = 0.85f))
                    .clickable { /* consume taps */ },
                contentAlignment = Alignment.Center,
            ) {
                Card(
                    colors = CardDefaults.cardColors(containerColor = Surface),
                    modifier = Modifier.padding(32.dp).fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                ) {
                    Column(
                        Modifier.padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                    ) {
                        Text("🎉", style = MaterialTheme.typography.headlineLarge)
                        Spacer(Modifier.height(8.dp))
                        Text("Edição concluída!", style = MaterialTheme.typography.titleLarge, color = Accent)
                        Spacer(Modifier.height(4.dp))
                        Text(
                            "${issue.title} #${issue.issue}",
                            style = MaterialTheme.typography.bodyMedium,
                            color = TextSecondary,
                        )
                        Spacer(Modifier.height(20.dp))

                        vm.nextIssue?.let { next ->
                            Button(
                                onClick = { onNavigateToIssue(next.orderNum) },
                                modifier = Modifier.fillMaxWidth(),
                                colors = ButtonDefaults.buttonColors(containerColor = Accent),
                            ) {
                                Text(
                                    "Próximo: ${next.title} #${next.issue}",
                                    fontWeight = FontWeight.Bold,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis,
                                )
                            }
                            Spacer(Modifier.height(8.dp))
                        }
                        OutlinedButton(onClick = onBack, modifier = Modifier.fillMaxWidth()) {
                            Text("Voltar à Biblioteca")
                        }
                    }
                }
            }
        }

        // ── Report dialog ──
        if (vm.showReport) {
            ReportDialog(
                issue = issue,
                page = vm.currentPage,
                totalPages = vm.totalPages,
                onDismiss = { vm.showReport = false },
                onSubmit = { type, desc -> vm.submitReport(type, desc) },
            )
        }
    }
}

// ═══════════════════════════════════════════════════════════
//  Paged Reader (HorizontalPager with pinch-zoom & double-tap)
// ═══════════════════════════════════════════════════════════

@Composable
private fun PagedReader(vm: ReaderViewModel) {
    val context = LocalContext.current
    val pagerState = rememberPagerState(
        initialPage = (vm.currentPage - 1).coerceAtLeast(0),
        pageCount = { vm.totalPages },
    )

    LaunchedEffect(pagerState.currentPage) {
        val page = pagerState.currentPage + 1
        vm.onPageChanged(page)
        if (page >= vm.totalPages) vm.onLastPage()
    }

    HorizontalPager(
        state = pagerState,
        modifier = Modifier.fillMaxSize(),
        beyondViewportPageCount = 2,
    ) { index ->
        val page = index + 1
        var scale by remember { mutableFloatStateOf(1f) }
        var offset by remember { mutableStateOf(Offset.Zero) }

        Box(
            Modifier
                .fillMaxSize()
                .pointerInput(Unit) {
                    detectTapGestures(
                        onTap = { vm.controlsVisible = !vm.controlsVisible },
                        onDoubleTap = { pos ->
                            if (scale > 1f) {
                                scale = 1f; offset = Offset.Zero
                            } else {
                                scale = 2.5f
                                offset = Offset(
                                    (size.width / 2f - pos.x) * 1.5f,
                                    (size.height / 2f - pos.y) * 1.5f,
                                )
                            }
                        },
                    )
                }
                .pointerInput(Unit) {
                    detectTransformGestures { _, pan, zoom, _ ->
                        scale = (scale * zoom).coerceIn(1f, 5f)
                        if (scale > 1f) {
                            offset = Offset(offset.x + pan.x, offset.y + pan.y)
                        } else {
                            offset = Offset.Zero
                        }
                    }
                },
            contentAlignment = Alignment.Center,
        ) {
            val model = vm.getPageModel(page)
            AsyncImage(
                model = ImageRequest.Builder(context).data(model).crossfade(true).build(),
                contentDescription = "Página $page",
                contentScale = ContentScale.Fit,
                modifier = Modifier
                    .fillMaxSize()
                    .graphicsLayer(
                        scaleX = scale, scaleY = scale,
                        translationX = offset.x, translationY = offset.y,
                    ),
            )
        }
    }
}

// ═══════════════════════════════════════════════════════════
//  Scroll Reader (continuous vertical scroll)
// ═══════════════════════════════════════════════════════════

@Composable
private fun ScrollReader(vm: ReaderViewModel) {
    val context = LocalContext.current
    val listState = rememberLazyListState(
        initialFirstVisibleItemIndex = (vm.currentPage - 1).coerceAtLeast(0),
    )

    LaunchedEffect(listState.firstVisibleItemIndex) {
        val page = listState.firstVisibleItemIndex + 1
        vm.onPageChanged(page)
        if (page >= vm.totalPages) vm.onLastPage()
    }

    LazyColumn(
        state = listState,
        modifier = Modifier
            .fillMaxSize()
            .pointerInput(Unit) {
                detectTapGestures(onTap = { vm.controlsVisible = !vm.controlsVisible })
            },
    ) {
        items(vm.totalPages) { index ->
            val page = index + 1
            val model = vm.getPageModel(page)
            AsyncImage(
                model = ImageRequest.Builder(context).data(model).crossfade(true).build(),
                contentDescription = "Página $page",
                contentScale = ContentScale.FillWidth,
                modifier = Modifier.fillMaxWidth(),
            )
        }

        // Next issue separator at the bottom
        vm.nextIssue?.let { next ->
            item {
                Box(
                    Modifier
                        .fillMaxWidth()
                        .clickable { /* handled by navigation */ }
                        .background(Surface)
                        .padding(20.dp),
                    contentAlignment = Alignment.Center,
                ) {
                    Text(
                        "Próximo: ${next.title} #${next.issue} →",
                        style = MaterialTheme.typography.titleMedium,
                        color = Accent,
                        fontWeight = FontWeight.SemiBold,
                    )
                }
            }
        }
    }
}

// ═══════════════════════════════════════════════════════════
//  Report Dialog
// ═══════════════════════════════════════════════════════════

@Composable
private fun ReportDialog(
    issue: IssueEntity,
    page: Int,
    totalPages: Int,
    onDismiss: () -> Unit,
    onSubmit: (type: String, description: String) -> Unit,
) {
    var selectedType by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }

    val reportTypes = listOf(
        "missing_images" to "🖼️ Imagens faltando",
        "wrong_order" to "🔀 Ordem errada",
        "bad_quality" to "👎 Qualidade ruim",
        "wrong_issue" to "❌ Edição errada",
        "other" to "📝 Outro",
    )

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = Surface,
        title = { Text("⚠️ Reportar Problema", color = Danger) },
        text = {
            Column {
                Text(
                    "${issue.title} #${issue.issue} — Página $page/$totalPages",
                    style = MaterialTheme.typography.bodySmall,
                    color = TextSecondary,
                )
                Spacer(Modifier.height(12.dp))
                Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    reportTypes.forEach { (type, label) ->
                        FilterChip(
                            selected = selectedType == type,
                            onClick = { selectedType = type },
                            label = { Text(label, style = MaterialTheme.typography.bodySmall) },
                            modifier = Modifier.fillMaxWidth(),
                        )
                    }
                }
                Spacer(Modifier.height(12.dp))
                OutlinedTextField(
                    value = description,
                    onValueChange = { description = it },
                    placeholder = { Text("Detalhes (opcional)...") },
                    modifier = Modifier.fillMaxWidth(),
                    minLines = 2,
                    maxLines = 4,
                    colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = Accent),
                )
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    if (selectedType.isNotEmpty()) onSubmit(selectedType, description.trim())
                },
                colors = ButtonDefaults.buttonColors(containerColor = Danger),
                enabled = selectedType.isNotEmpty(),
            ) {
                Text("Enviar")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) { Text("Cancelar") }
        },
    )
}
