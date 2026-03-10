package com.marvel.reader

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.marvel.reader.ui.navigation.AppNavigation
import com.marvel.reader.ui.theme.MarvelReaderTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            MarvelReaderTheme {
                AppNavigation()
            }
        }
    }
}
