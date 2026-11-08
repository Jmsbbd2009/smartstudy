package uz.smartstudy.control

import android.os.Build
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import kotlinx.serialization.json.*
import uz.smartstudy.data.ProfileAppearance
import uz.smartstudy.data.StudyPreferences
import uz.smartstudy.devicepolicy.DeviceController

@Composable
private fun ProfilePage(title:String,back:()->Unit,content:@Composable ColumnScope.()->Unit) {
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),verticalArrangement=Arrangement.spacedBy(16.dp)) {
        TextButton(onClick=back) { Text("‹ Profilga qaytish") }
        Text(title,style=MaterialTheme.typography.headlineMedium)
        content()
    }
}

@Composable
fun ProfileHome(vm:StudyViewModel,sticker:String,navigate:(String)->Unit) {
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(20.dp),verticalArrangement=Arrangement.spacedBy(14.dp)) {
        Text("Profil",style=MaterialTheme.typography.headlineLarge)
        Card(Modifier.fillMaxWidth(),colors=CardDefaults.cardColors(containerColor=MaterialTheme.colorScheme.primaryContainer)) {
            Column(Modifier.padding(24.dp),verticalArrangement=Arrangement.spacedBy(8.dp)) {
                Text(sticker,style=MaterialTheme.typography.displayMedium)
                Text(vm.user?.text("name").orEmpty(),style=MaterialTheme.typography.titleLarge)
                Text(when(vm.user?.text("role")) {"STUDENT"->"O‘quvchi";"PARENT"->"Ota-ona";"TEACHER"->"O‘qituvchi";"SUPER_ADMIN"->"Bosh administrator";else->"Maktab administratori"})
            }
        }
        val items=listOf(
            Triple("profile/theme","🎨","Mavzu va status belgisi"),
            Triple("profile/reading","📚","Mutolaa tarixi"),
            Triple("profile/results","📊","Test natijalari va bonuslar"),
            Triple("profile/sessions","📱","Qurilma va kirish seanslari"),
            Triple("profile/security","🔒","Oila va qurilma himoyasi"),
            Triple("settings","⚙","Til, maxfiylik va sozlamalar"),
        )
        items.forEach { (route,icon,label) ->
            OutlinedCard(onClick={navigate(route)},modifier=Modifier.fillMaxWidth()) {
                Row(Modifier.fillMaxWidth().padding(20.dp),horizontalArrangement=Arrangement.spacedBy(14.dp)) {
                    Text(icon);Text(label,Modifier.weight(1f),style=MaterialTheme.typography.titleSmall);Text("›")
                }
            }
        }
        Text("Smart Study ${BuildConfig.VERSION_NAME}",style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
fun ProfileTheme(vm:StudyViewModel,back:()->Unit) {
    val context=LocalContext.current
    val prefs=remember {StudyPreferences(context.applicationContext)}
    val id=vm.user?.text("id").orEmpty()
    val appearance by remember(id){prefs.appearance(id)}.collectAsStateWithLifecycle(ProfileAppearance())
    ProfilePage("Mavzu va status",back) {
        Card(Modifier.fillMaxWidth(),colors=CardDefaults.cardColors(containerColor=MaterialTheme.colorScheme.primaryContainer)) {
            Column(Modifier.padding(24.dp)) {
                Text("${vm.user?.text("name").orEmpty()} ${appearance.sticker}",style=MaterialTheme.typography.titleLarge)
                Text("Jonli ko‘rinish",style=MaterialTheme.typography.bodySmall)
            }
        }
        Text("Rang mavzusi",style=MaterialTheme.typography.titleMedium)
        val themes=listOf("sun" to "☀ Quyosh", "navy" to "🌙 Deep Navy", "blue" to "🔵 Electric Blue", "mint" to "🌿 Mint", "violet" to "🟣 Binafsha", "ruby" to "🔴 Ruby", "rose" to "🌸 Rose", "graphite" to "◼ Grafit")
        themes.chunked(2).forEach { row -> Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
            row.forEach { (key,label) -> FilterChip(selected=appearance.theme==key,onClick={vm.run{prefs.setAppearance(id,key,appearance.sticker)}},label={Text(label)},modifier=Modifier.weight(1f).heightIn(min=48.dp)) }
        } }
        Text("Ism yonidagi belgi",style=MaterialTheme.typography.titleMedium)
        listOf("⚡","🎓","🚀","👑","📚","🏆","🔥","⭐").chunked(4).forEach { row -> Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
            row.forEach { emoji -> FilterChip(selected=appearance.sticker==emoji,onClick={vm.run{prefs.setAppearance(id,appearance.theme,emoji)}},label={Text(emoji)},modifier=Modifier.weight(1f).heightIn(min=48.dp)) }
        } }
        Text("Tanlov shu qurilmadagi hisobingiz uchun saqlanadi. Emoji ko‘rinishi qurilma shriftiga bog‘liq.",style=MaterialTheme.typography.bodySmall)
    }
}

@Composable
fun ProfileReading(vm:StudyViewModel,results:Boolean,back:()->Unit,openBooks:()->Unit) {
    var plans by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    var attempts by remember {mutableStateOf<List<Pair<String,JsonObject>>>(emptyList())}
    var loaded by remember {mutableStateOf(false)}
    fun load() { vm.run {
        loaded=false
        val summaries=vm.repository.api.list("reading/plans").take(20)
        val details=mutableListOf<JsonObject>()
        val completed=mutableListOf<Pair<String,JsonObject>>()
        for(p in summaries) {
            details.add(vm.repository.api.get("reading/plans/${p.text("id")}"))
            if(results) completed.addAll(vm.repository.api.list("reading/plans/${p.text("id")}/attempts").map{p.text("book_title") to it})
        }
        plans=details;attempts=completed;loaded=true
    } }
    LaunchedEffect(Unit){load()}
    ProfilePage(if(results) "Natijalar va bonuslar" else "Mutolaa tarixi",back) {
        OutlinedButton(onClick={load()}){Text("Yangilash")}
        if(!loaded) Text("Ma’lumot olinmoqda. Ulanishda xato bo‘lsa, qayta urinib ko‘ring.")
        else if(plans.isEmpty()) Text("Hozircha o‘qish rejasi yo‘q. Ustoz yoki ota-ona kitob biriktirganda shu yerda ko‘rinadi.")
        else {
            Text("Oxirgi ${plans.size} ta o‘qish rejasi",style=MaterialTheme.typography.bodySmall)
            if(results) {
                val scores=attempts.mapNotNull{it.second["result"]?.jsonObject?.text("percent")?.toDoubleOrNull()}
                if(scores.isNotEmpty()) Text("O‘rtacha natija: ${"%.1f".format(scores.average())}%",style=MaterialTheme.typography.headlineMedium)
                if(attempts.isEmpty()) Text("Topshirilgan testlar hali yo‘q.")
                attempts.forEach { (title,a) ->
                    val result=a["result"]?.jsonObject
                    val reward=result?.get("reward")?.jsonObject
                    OutlinedCard(Modifier.fillMaxWidth()) { Column(Modifier.padding(18.dp),verticalArrangement=Arrangement.spacedBy(8.dp)) {
                        Text(title,style=MaterialTheme.typography.titleMedium)
                        Text(a.text("finished_at"),style=MaterialTheme.typography.bodySmall)
                        Text("${result?.text("percent").orEmpty()}%",style=MaterialTheme.typography.headlineMedium)
                        Text(when(reward?.text("state")) {"GRANTED"->"+${reward?.text("minutes").orEmpty()} daqiqa berilgan";"ALREADY_GRANTED"->"Bonus avval berilgan";else->"Bonus uchun tasdiq talab qilinishi mumkin"})
                        a["review"]?.jsonArray?.forEach { review -> Text("${review.jsonObject.text("source_page")}-bet: ${review.jsonObject.text("explanation")}",style=MaterialTheme.typography.bodySmall) }
                        TextButton(onClick=openBooks){Text("Kitobni qayta ko‘rish →")}
                    } }
                }
            } else plans.forEach { p ->
                val progress=p["progress"]?.jsonObject
                val percent=progress?.text("self_reported_percent")?.toFloatOrNull() ?: 0f
                OutlinedCard(Modifier.fillMaxWidth()) { Column(Modifier.padding(18.dp),verticalArrangement=Arrangement.spacedBy(10.dp)) {
                    Text(p.text("book_title"),style=MaterialTheme.typography.titleMedium)
                    Text("${p.text("start_page")}–${p.text("end_page")}-betlar")
                    LinearProgressIndicator(progress={percent.coerceIn(0f,100f)/100f},modifier=Modifier.fillMaxWidth())
                    Text("${percent.toInt()}% · "+when {percent>=100->"Belgilangan betlar tugatilgan";percent>0->"Jarayonda";else->"Rejada"})
                    Text("Test bilan tekshirilgan: ${progress?.text("checked_percent").orEmpty()}%",style=MaterialTheme.typography.bodySmall)
                    TextButton(onClick=openBooks){Text("Mutolaani davom ettirish →")}
                } }
            }
            Text("O‘qilgan betlar o‘quvchining belgilashiga asoslanadi; tushunish darajasi alohida test bilan tekshiriladi.",style=MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable
fun ProfileSessions(vm:StudyViewModel,back:()->Unit) {
    var sessions by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    var loaded by remember {mutableStateOf(false)}
    var confirm by remember {mutableStateOf<String?>(null)}
    fun load(){vm.run{sessions=vm.repository.api.list("profile/sessions");loaded=true}}
    LaunchedEffect(Unit){load()}
    ProfilePage("Qurilmalar va seanslar",back) {
        Card(Modifier.fillMaxWidth(),colors=CardDefaults.cardColors(containerColor=MaterialTheme.colorScheme.secondaryContainer)) { Column(Modifier.padding(20.dp)) {
            Text("📱 ${Build.MANUFACTURER} ${Build.MODEL}",style=MaterialTheme.typography.titleMedium)
            Text("Bu telefon · Android ${Build.VERSION.RELEASE}")
            Text("Smart Study ${BuildConfig.VERSION_NAME}")
        } }
        Text("IP yoki joylashuv bu ro‘yxat uchun yig‘ilmaydi. Pastdagi yozuvlar hisobga kirish seanslaridir.",style=MaterialTheme.typography.bodySmall)
        OutlinedButton(onClick={load()}){Text("Yangilash")}
        if(!loaded) Text("Seanslar olinmoqda. Xato bo‘lsa qayta urinib ko‘ring.")
        sessions.forEach { session -> OutlinedCard(Modifier.fillMaxWidth()) { Column(Modifier.padding(18.dp)) {
            val current=session.text("current")=="true"
            Text(if(current) "✓ Joriy seans" else "Boshqa faol seans",style=MaterialTheme.typography.titleMedium)
            Text("Yangilangan: ${session.text("renewed_at")}",style=MaterialTheme.typography.bodySmall)
            if(!current) TextButton(onClick={confirm=session.text("id")}){Text("Seansni yakunlash")}
        } } }
        if(sessions.any{it.text("current")!="true"}) OutlinedButton(onClick={confirm="others"}){Text("Boshqa barcha seanslarni yakunlash")}
    }
    confirm?.let { target -> AlertDialog(onDismissRequest={confirm=null},title={Text("Seansni yakunlaysizmi?")},text={Text("Tanlangan seanslarda qayta kirish talab etiladi.")},confirmButton={TextButton(onClick={confirm=null;vm.run{
        if(target=="others") vm.repository.api.post("profile/sessions/terminate-others",buildJsonObject{}) else vm.repository.api.delete("profile/sessions/$target")
        sessions=vm.repository.api.list("profile/sessions")
    }}){Text("Yakunlash")}},dismissButton={TextButton(onClick={confirm=null}){Text("Bekor qilish")}}) }
}

@Composable
fun ProfileSecurity(back:()->Unit,navigate:(String)->Unit) {
    val context=LocalContext.current
    val controller=remember {DeviceController(context)}
    ProfilePage("Oila va qurilma himoyasi",back) {
        Text(if(controller.managed) "🛡 Boshqariladigan qurilma" else "📱 Oddiy Android rejimi",style=MaterialTheme.typography.titleLarge)
        Text(if(controller.uninstallProtected()) "O‘chirishdan himoya faol" else "O‘chirishdan tizim himoyasi faol emas")
        Text("Kuchli ilova cheklovlari Device Owner sifatida rasmiy sozlangan qurilmada ishlaydi. Oddiy APK tizim sozlamalari yoki o‘chirish oynasini PIN bilan to‘sib qo‘ya olmaydi.")
        Text("Oila boshqaruvi bog‘langan ota-onaning autentifikatsiya qilingan hisobidan amalga oshiriladi. Favqulodda aloqa va budilnikni o‘chirish imkoniyati saqlanadi.")
        Button(onClick={navigate("device")},modifier=Modifier.fillMaxWidth()){Text("Qurilma holati va sinxronlash")}
        OutlinedButton(onClick={navigate("family")},modifier=Modifier.fillMaxWidth()){Text("Oila bilan bog‘lanish")}
        OutlinedButton(onClick={navigate("settings")},modifier=Modifier.fillMaxWidth()){Text("Ruxsatlar va maxfiylik")}
    }
}
