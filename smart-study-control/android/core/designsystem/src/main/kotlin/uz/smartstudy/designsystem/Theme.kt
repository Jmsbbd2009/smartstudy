package uz.smartstudy.designsystem
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private val StudyDark = darkColorScheme(
    primary = Color(0xFF7297FF),
    onPrimary = Color(0xFF08152F),
    secondary = Color(0xFF37CFA2),
    onSecondary = Color(0xFF06291F),
    tertiary = Color(0xFFFFC857),
    background = Color(0xFF101C35),
    onBackground = Color(0xFFF5F7FC),
    surface = Color(0xFF182642),
    onSurface = Color(0xFFF5F7FC),
    surfaceVariant = Color(0xFF223352),
    onSurfaceVariant = Color(0xFFB8C4D8),
    outline = Color(0xFF526482),
    error = Color(0xFFFF7D89),
)

@Composable
fun StudyTheme(accent:String="sun", content: @Composable () -> Unit) {
    val primary=when(accent) {
        "blue" -> Color(0xFF315DD8)
        "mint" -> Color(0xFF087F64)
        "violet" -> Color(0xFF7545C8)
        "ruby" -> Color(0xFFB32632)
        "rose" -> Color(0xFFB13B76)
        "graphite" -> Color(0xFF454F60)
        else -> Color(0xFF9F4800)
    }
    val light=lightColorScheme(
        primary=primary, onPrimary=Color.White,
        primaryContainer=Color(0xFFFFEACD), onPrimaryContainer=Color(0xFF472600),
        secondary=Color(0xFF087F64), onSecondary=Color.White,
        secondaryContainer=Color(0xFFD8F8EB), onSecondaryContainer=Color(0xFF064E3B),
        tertiary=Color(0xFFF77F00), background=Color(0xFFF7F9FF),
        onBackground=Color(0xFF1A1A1A), surface=Color.White, onSurface=Color(0xFF1A1A1A),
        surfaceVariant=Color(0xFFEDF1F8), onSurfaceVariant=Color(0xFF53627A),
        outline=Color(0xFF7A879C), outlineVariant=Color(0xFFDDE4F0),
    )
    MaterialTheme(
        colorScheme = if(accent=="navy") StudyDark else light,
        shapes = Shapes(
            extraSmall = androidx.compose.foundation.shape.RoundedCornerShape(10.dp),
            small = androidx.compose.foundation.shape.RoundedCornerShape(14.dp),
            medium = androidx.compose.foundation.shape.RoundedCornerShape(20.dp),
            large = androidx.compose.foundation.shape.RoundedCornerShape(26.dp),
            extraLarge = androidx.compose.foundation.shape.RoundedCornerShape(32.dp),
        ),
        typography = Typography(
            headlineLarge = TextStyle(fontSize = 32.sp, lineHeight = 40.sp, fontWeight = FontWeight.Bold),
            headlineMedium = TextStyle(fontSize = 28.sp, lineHeight = 36.sp, fontWeight = FontWeight.SemiBold),
            titleLarge = TextStyle(fontSize = 22.sp, lineHeight = 30.sp, fontWeight = FontWeight.SemiBold),
            titleMedium = TextStyle(fontSize = 18.sp, lineHeight = 26.sp, fontWeight = FontWeight.Medium),
            bodyLarge = TextStyle(fontSize = 17.sp, lineHeight = 26.sp),
            bodyMedium = TextStyle(fontSize = 16.sp, lineHeight = 24.sp),
            bodySmall = TextStyle(fontSize = 14.sp, lineHeight = 21.sp),
            labelLarge = TextStyle(fontSize = 16.sp, lineHeight = 22.sp, fontWeight = FontWeight.SemiBold),
            labelMedium = TextStyle(fontSize = 14.sp, lineHeight = 20.sp, fontWeight = FontWeight.Medium),
            labelSmall = TextStyle(fontSize = 13.sp, lineHeight = 18.sp, fontWeight = FontWeight.Medium),
        ),
        content = content,
    )
}
