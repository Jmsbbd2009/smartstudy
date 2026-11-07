package uz.smartstudy.control

import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun SmartStudySplash() {
    val transition = rememberInfiniteTransition(label = "brand-pulse")
    val scale by transition.animateFloat(
        initialValue = 0.975f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(tween(1150), RepeatMode.Reverse),
        label = "logo-scale",
    )
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Brush.verticalGradient(listOf(Color(0xFF172848), Color(0xFF101C35), Color(0xFF0B1428)))),
        contentAlignment = Alignment.Center,
    ) {
        Column(
            modifier = Modifier.fillMaxWidth().padding(horizontal = 28.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(22.dp),
        ) {
            Image(
                painter = painterResource(R.drawable.smartstudy_logo),
                contentDescription = stringResource(R.string.app_name),
                contentScale = ContentScale.Fit,
                modifier = Modifier.fillMaxWidth().height(142.dp).scale(scale),
            )
            Text(
                text = stringResource(R.string.app_name),
                style = MaterialTheme.typography.headlineMedium,
                color = Color(0xFFF8FAFF),
                fontWeight = FontWeight.Bold,
            )
            Text(
                text = "Learn. Achieve. Unlock.",
                color = Color(0xFFB8C4D8),
                fontSize = 15.sp,
                letterSpacing = 1.1.sp,
            )
            Box(Modifier.padding(top = 10.dp).size(width = 44.dp, height = 3.dp).background(Color(0xFFFFC857)))
        }
    }
}
