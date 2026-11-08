package uz.smartstudy.control

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import kotlinx.serialization.json.*
import uz.smartstudy.control.alarms.AlarmScheduler

@Composable
fun StudentOverview(vm:StudyViewModel,state:StudyState,navigate:(String)->Unit) {
    val context=LocalContext.current
    val alarms=remember {AlarmScheduler(context).alarms().filter{it.enabled}}
    var wallet by remember {mutableStateOf<JsonObject?>(null)}
    var plan by remember {mutableStateOf<JsonObject?>(null)}
    var loaded by remember {mutableStateOf(false)}
    LaunchedEffect(Unit){vm.run{
        wallet=vm.repository.api.get("rewards/wallet")
        val first=vm.repository.api.list("reading/plans").firstOrNull()
        plan=first?.let{vm.repository.api.get("reading/plans/${it.text("id")}")}
        loaded=true
    }}
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),verticalArrangement=Arrangement.spacedBy(16.dp)) {
        Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween) {
            Column(Modifier.weight(1f)) {
                Text("Bugungi reja",style=MaterialTheme.typography.headlineMedium)
                Text("Kichik qadamlar, katta natijalar",style=MaterialTheme.typography.bodySmall)
            }
            FilledTonalButton(onClick={navigate("rewards")}){Text("🎁 ${wallet?.text("available") ?: "—"} min")}
        }
        OutlinedCard(Modifier.fillMaxWidth()) { Column(Modifier.padding(18.dp),verticalArrangement=Arrangement.spacedBy(10.dp)) {
            Text("O‘QUV FAOLIYATI",style=MaterialTheme.typography.labelSmall)
            Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceEvenly) {
                TextButton(onClick={navigate("profile/reading")}){Column{Text("📚");Text("Mutolaa",style=MaterialTheme.typography.labelSmall)}}
                TextButton(onClick={navigate("focus")}){Column{Text("⏱");Text("Fokus",style=MaterialTheme.typography.labelSmall)}}
                TextButton(onClick={navigate("profile/results")}){Column{Text("🏆");Text("Natijalar",style=MaterialTheme.typography.labelSmall)}}
            }
        } }
        Card(onClick={navigate("alarms")},modifier=Modifier.fillMaxWidth(),colors=CardDefaults.cardColors(containerColor=MaterialTheme.colorScheme.primaryContainer)) {
            Row(Modifier.padding(20.dp),horizontalArrangement=Arrangement.spacedBy(14.dp)) {
                Text("⏰",style=MaterialTheme.typography.headlineMedium)
                Column(Modifier.weight(1f)) {
                    Text("AQLLI BUDILNIK",style=MaterialTheme.typography.labelSmall)
                    Text(alarms.firstOrNull()?.let{"%02d:%02d".format(it.hour,it.minute)+" · Faol"} ?: "Budilnik sozlang",style=MaterialTheme.typography.titleLarge)
                    Text("Uyg‘onish vaqti va takrorlash kunlari",style=MaterialTheme.typography.bodySmall)
                }
                Text("›")
            }
        }
        OutlinedCard(Modifier.fillMaxWidth()) { Column(Modifier.padding(20.dp),verticalArrangement=Arrangement.spacedBy(12.dp)) {
            Text("📖 MUTOLAA REJASI",style=MaterialTheme.typography.labelLarge,color=MaterialTheme.colorScheme.primary)
            if(plan!=null) {
                val p=plan!!
                val percent=p["progress"]?.jsonObject?.text("self_reported_percent")?.toFloatOrNull() ?: 0f
                Text(p.text("book_title"),style=MaterialTheme.typography.titleLarge)
                Text("${p.text("start_page")}–${p.text("end_page")}-betlar · ${percent.toInt()}%")
                LinearProgressIndicator(progress={percent.coerceIn(0f,100f)/100f},modifier=Modifier.fillMaxWidth())
                Text("Belgilangan sahifalarni o‘qing, keyin tushunishingizni testda tekshiring.",style=MaterialTheme.typography.bodySmall)
            } else Text(if(loaded) "Hozircha kitob biriktirilmagan" else "Kitob rejasi olinmoqda…")
            Button(onClick={navigate("books")},modifier=Modifier.fillMaxWidth()){Text("📚 Kutubxonani ochish")}
        } }
        Card(onClick={navigate("apps")},modifier=Modifier.fillMaxWidth(),colors=CardDefaults.cardColors(containerColor=MaterialTheme.colorScheme.secondaryContainer)) {
            Column(Modifier.padding(20.dp)) {
                Text("Ilovalarni ochish →",style=MaterialTheme.typography.titleLarge)
                Text("Rag‘bat daqiqalarini ishlating. Oila jadvali va qurilma rejimi hisobga olinadi.",style=MaterialTheme.typography.bodySmall)
            }
        }
        OutlinedButton(onClick={navigate("assignments")},modifier=Modifier.fillMaxWidth()) {
            Text("Vazifalar · ${state.assignments.count{it.text("status")!="APPROVED"}} kutilmoqda")
        }
        Text("Tanaffus va zarur aloqa doim muhim.",style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
    }
}
