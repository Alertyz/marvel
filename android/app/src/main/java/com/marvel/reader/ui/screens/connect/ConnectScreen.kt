package com.marvel.reader.ui.screens.connect

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.CloudDone
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material.icons.filled.Wifi
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
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
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.compose.viewModel
import com.marvel.reader.data.api.HandshakeResponse
import com.marvel.reader.data.repository.ComicRepository
import kotlinx.coroutines.launch

class ConnectViewModel(private val repo: ComicRepository) : ViewModel() {
    var host by mutableStateOf("")
    var port by mutableStateOf("8080")
    var isConnecting by mutableStateOf(false)
    var isSyncing by mutableStateOf(false)
    var connectionResult by mutableStateOf<HandshakeResponse?>(null)
    var error by mutableStateOf<String?>(null)
    var syncDone by mutableStateOf(false)

    init {
        viewModelScope.launch {
            host = repo.getSetting("server_host") ?: ""
            port = repo.getSetting("server_port") ?: "8080"
            if (host.isNotEmpty()) tryReconnect()
        }
    }

    private suspend fun tryReconnect() {
        try {
            isConnecting = true
            error = null
            connectionResult = repo.connect(host, port.toIntOrNull() ?: 8080)
        } catch (_: Exception) {
            connectionResult = null
        } finally {
            isConnecting = false
        }
    }

    fun connect() {
        if (host.isBlank()) {
            error = "Digite o IP do PC"
            return
        }
        viewModelScope.launch {
            try {
                isConnecting = true
                error = null
                connectionResult = null
                connectionResult = repo.connect(host.trim(), port.toIntOrNull() ?: 8080)
            } catch (e: Exception) {
                error = "Falha ao conectar: ${e.message}"
                connectionResult = null
            } finally {
                isConnecting = false
            }
        }
    }

    fun sync() {
        viewModelScope.launch {
            try {
                isSyncing = true
                error = null
                syncDone = false
                repo.syncCatalog()
                repo.syncState()
                syncDone = true
            } catch (e: Exception) {
                error = "Erro no sync: ${e.message}"
            } finally {
                isSyncing = false
            }
        }
    }
}

@Composable
fun ConnectScreen(repository: ComicRepository) {
    val vm: ConnectViewModel = viewModel(
        factory = object : ViewModelProvider.Factory {
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                @Suppress("UNCHECKED_CAST")
                return ConnectViewModel(repository) as T
            }
        },
    )

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(20.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Spacer(Modifier.height(24.dp))

        Icon(
            Icons.Default.Wifi, null,
            tint = MaterialTheme.colorScheme.primary,
            modifier = Modifier.size(56.dp),
        )
        Spacer(Modifier.height(12.dp))
        Text("Conectar ao PC", style = MaterialTheme.typography.headlineMedium)
        Text(
            "Digite o IP exibido pelo servidor no PC",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(28.dp))

        OutlinedTextField(
            value = vm.host,
            onValueChange = { vm.host = it },
            label = { Text("IP do PC") },
            placeholder = { Text("192.168.1.10") },
            singleLine = true,
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Uri,
                imeAction = ImeAction.Next,
            ),
            modifier = Modifier.fillMaxWidth(),
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = MaterialTheme.colorScheme.primary,
            ),
        )
        Spacer(Modifier.height(10.dp))

        OutlinedTextField(
            value = vm.port,
            onValueChange = { vm.port = it },
            label = { Text("Porta") },
            singleLine = true,
            keyboardOptions = KeyboardOptions(
                keyboardType = KeyboardType.Number,
                imeAction = ImeAction.Done,
            ),
            keyboardActions = KeyboardActions(onDone = { vm.connect() }),
            modifier = Modifier.fillMaxWidth(),
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = MaterialTheme.colorScheme.primary,
            ),
        )
        Spacer(Modifier.height(20.dp))

        Button(
            onClick = { vm.connect() },
            modifier = Modifier.fillMaxWidth().height(50.dp),
            enabled = !vm.isConnecting,
            colors = ButtonDefaults.buttonColors(
                containerColor = MaterialTheme.colorScheme.primary,
            ),
        ) {
            if (vm.isConnecting) {
                CircularProgressIndicator(
                    modifier = Modifier.size(20.dp),
                    strokeWidth = 2.dp,
                    color = MaterialTheme.colorScheme.onPrimary,
                )
                Spacer(Modifier.width(8.dp))
            }
            Text(
                if (vm.isConnecting) "Conectando..." else "Conectar",
                fontWeight = FontWeight.Bold,
            )
        }

        // Error
        vm.error?.let { err ->
            Spacer(Modifier.height(12.dp))
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.error.copy(alpha = 0.15f),
                ),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(
                        Icons.Default.Warning, null,
                        tint = MaterialTheme.colorScheme.error,
                        modifier = Modifier.size(20.dp),
                    )
                    Spacer(Modifier.width(8.dp))
                    Text(
                        err,
                        color = MaterialTheme.colorScheme.error,
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
        }

        // Connected state
        vm.connectionResult?.let { hs ->
            Spacer(Modifier.height(16.dp))
            Card(
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.tertiary.copy(alpha = 0.12f),
                ),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(Modifier.padding(16.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            Icons.Default.CheckCircle, null,
                            tint = MaterialTheme.colorScheme.tertiary,
                            modifier = Modifier.size(24.dp),
                        )
                        Spacer(Modifier.width(8.dp))
                        Text(
                            "Conectado!",
                            style = MaterialTheme.typography.titleMedium,
                            color = MaterialTheme.colorScheme.tertiary,
                        )
                    }
                    Spacer(Modifier.height(10.dp))
                    InfoRow("Total edições", "${hs.totalIssues}")
                    InfoRow("Com imagens", "${hs.availableIssues}")
                    InfoRow("Lidas", "${hs.readIssues}")
                }
            }

            Spacer(Modifier.height(16.dp))

            Button(
                onClick = { vm.sync() },
                modifier = Modifier.fillMaxWidth().height(50.dp),
                enabled = !vm.isSyncing,
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.secondary,
                ),
            ) {
                if (vm.isSyncing) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        strokeWidth = 2.dp,
                        color = MaterialTheme.colorScheme.onSecondary,
                    )
                    Spacer(Modifier.width(8.dp))
                }
                Text(
                    if (vm.isSyncing) "Sincronizando..." else "Sincronizar Tudo",
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onSecondary,
                )
            }

            if (vm.syncDone) {
                Spacer(Modifier.height(12.dp))
                Card(
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.tertiary.copy(alpha = 0.12f),
                    ),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Row(Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            Icons.Default.CloudDone, null,
                            tint = MaterialTheme.colorScheme.tertiary,
                            modifier = Modifier.size(20.dp),
                        )
                        Spacer(Modifier.width(8.dp))
                        Text(
                            "Catálogo e progresso sincronizados!",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.tertiary,
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun InfoRow(label: String, value: String) {
    Row(
        Modifier.fillMaxWidth().padding(vertical = 2.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
    ) {
        Text(
            label,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(value, style = MaterialTheme.typography.bodySmall, fontWeight = FontWeight.SemiBold)
    }
}
