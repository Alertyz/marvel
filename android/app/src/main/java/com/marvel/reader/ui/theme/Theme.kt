package com.marvel.reader.ui.theme

import android.app.Activity
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import androidx.core.view.WindowCompat

// Design tokens matching the web version
val BG = Color(0xFF0A0A0F)
val Surface = Color(0xFF12121A)
val Surface2 = Color(0xFF1A1A2E)
val Border = Color(0xFF2A2A3E)
val TextPrimary = Color(0xFFE0E0F0)
val TextSecondary = Color(0xFF8888AA)
val Accent = Color(0xFFF0C040)
val Danger = Color(0xFFE04060)
val Success = Color(0xFF40E080)
val Info = Color(0xFF40A0E0)

private val DarkColorScheme = darkColorScheme(
    primary = Accent,
    secondary = Info,
    tertiary = Success,
    background = BG,
    surface = Surface,
    surfaceVariant = Surface2,
    onPrimary = Color.Black,
    onSecondary = Color.White,
    onBackground = TextPrimary,
    onSurface = TextPrimary,
    onSurfaceVariant = TextSecondary,
    outline = Border,
    error = Danger,
    onError = Color.White,
)

private val AppTypography = Typography(
    headlineLarge = TextStyle(fontWeight = FontWeight.Black, fontSize = 28.sp, letterSpacing = (-1).sp),
    headlineMedium = TextStyle(fontWeight = FontWeight.Bold, fontSize = 22.sp),
    titleLarge = TextStyle(fontWeight = FontWeight.SemiBold, fontSize = 18.sp),
    titleMedium = TextStyle(fontWeight = FontWeight.SemiBold, fontSize = 15.sp),
    bodyLarge = TextStyle(fontWeight = FontWeight.Normal, fontSize = 14.sp),
    bodyMedium = TextStyle(fontWeight = FontWeight.Normal, fontSize = 13.sp),
    bodySmall = TextStyle(fontWeight = FontWeight.Normal, fontSize = 11.sp),
    labelLarge = TextStyle(fontWeight = FontWeight.SemiBold, fontSize = 13.sp),
    labelMedium = TextStyle(fontWeight = FontWeight.Medium, fontSize = 11.sp),
    labelSmall = TextStyle(fontWeight = FontWeight.Medium, fontSize = 9.sp, letterSpacing = 1.sp),
)

@Composable
fun MarvelReaderTheme(content: @Composable () -> Unit) {
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = BG.toArgb()
            window.navigationBarColor = BG.toArgb()
            WindowCompat.getInsetsController(window, view).apply {
                isAppearanceLightStatusBars = false
                isAppearanceLightNavigationBars = false
            }
        }
    }
    MaterialTheme(
        colorScheme = DarkColorScheme,
        typography = AppTypography,
        content = content,
    )
}
