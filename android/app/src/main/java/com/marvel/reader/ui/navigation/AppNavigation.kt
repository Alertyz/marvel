package com.marvel.reader.ui.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.MenuBook
import androidx.compose.material.icons.filled.Wifi
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.marvel.reader.MarvelReaderApp
import com.marvel.reader.ui.screens.connect.ConnectScreen
import com.marvel.reader.ui.screens.downloads.DownloadsScreen
import com.marvel.reader.ui.screens.library.LibraryScreen
import com.marvel.reader.ui.screens.reader.ReaderScreen

private sealed class Tab(val route: String, val label: String, val icon: ImageVector) {
    data object Library : Tab("library", "Biblioteca", Icons.Default.MenuBook)
    data object Downloads : Tab("downloads", "Downloads", Icons.Default.Download)
    data object Connect : Tab("connect", "Conexão", Icons.Default.Wifi)
}

@Composable
fun AppNavigation() {
    val context = LocalContext.current
    val app = context.applicationContext as MarvelReaderApp
    val repository = remember { app.repository }
    val navController = rememberNavController()
    val currentBackStack by navController.currentBackStackEntryAsState()
    val currentRoute = currentBackStack?.destination?.route
    val isReaderScreen = currentRoute?.startsWith("reader/") == true
    val tabs = listOf(Tab.Library, Tab.Downloads, Tab.Connect)

    Scaffold(
        bottomBar = {
            if (!isReaderScreen) {
                NavigationBar(containerColor = MaterialTheme.colorScheme.surface) {
                    tabs.forEach { tab ->
                        NavigationBarItem(
                            icon = { Icon(tab.icon, contentDescription = tab.label) },
                            label = {
                                Text(tab.label, style = MaterialTheme.typography.labelSmall)
                            },
                            selected = currentRoute == tab.route,
                            onClick = {
                                if (currentRoute != tab.route) {
                                    navController.navigate(tab.route) {
                                        popUpTo(navController.graph.startDestinationId) {
                                            saveState = true
                                        }
                                        launchSingleTop = true
                                        restoreState = true
                                    }
                                }
                            },
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor = MaterialTheme.colorScheme.primary,
                                selectedTextColor = MaterialTheme.colorScheme.primary,
                                indicatorColor = MaterialTheme.colorScheme.surfaceVariant,
                            ),
                        )
                    }
                }
            }
        },
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = Tab.Library.route,
            modifier = Modifier.padding(padding),
        ) {
            composable(Tab.Library.route) {
                LibraryScreen(
                    repository = repository,
                    onOpenReader = { orderNum, page ->
                        navController.navigate("reader/$orderNum/$page")
                    },
                )
            }
            composable(Tab.Downloads.route) {
                DownloadsScreen(repository = repository)
            }
            composable(Tab.Connect.route) {
                ConnectScreen(repository = repository)
            }
            composable(
                "reader/{orderNum}/{page}",
                arguments = listOf(
                    navArgument("orderNum") { type = NavType.IntType },
                    navArgument("page") { type = NavType.IntType; defaultValue = 1 },
                ),
            ) { backStack ->
                val orderNum = backStack.arguments?.getInt("orderNum") ?: return@composable
                val page = backStack.arguments?.getInt("page") ?: 1
                ReaderScreen(
                    repository = repository,
                    orderNum = orderNum,
                    startPage = page,
                    onBack = { navController.popBackStack() },
                    onNavigateToIssue = { nextOrder ->
                        navController.navigate("reader/$nextOrder/1") {
                            popUpTo("reader/$orderNum/$page") { inclusive = true }
                        }
                    },
                )
            }
        }
    }
}
