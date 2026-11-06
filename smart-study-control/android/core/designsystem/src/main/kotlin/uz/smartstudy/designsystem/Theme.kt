package uz.smartstudy.designsystem
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
private val Light=lightColorScheme(primary=Color(0xFF3262DA),onPrimary=Color.White,secondary=Color(0xFF006D53),background=Color(0xFFF8FAFF),surface=Color.White,onSurface=Color(0xFF101C35))
private val Dark=darkColorScheme(primary=Color(0xFFAFC6FF),secondary=Color(0xFF37CFA2),background=Color(0xFF101C35),surface=Color(0xFF182642))
@Composable fun StudyTheme(content: @Composable () -> Unit) { MaterialTheme(colorScheme=if(isSystemInDarkTheme()) Dark else Light,content=content) }
