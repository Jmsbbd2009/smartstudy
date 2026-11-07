package uz.smartstudy.control

import android.Manifest
import android.app.AlarmManager
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.SystemClock
import android.provider.Settings
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.navigation.compose.*
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.delay
import kotlinx.serialization.json.*
import uz.smartstudy.designsystem.StudyTheme
import uz.smartstudy.devicepolicy.*
import uz.smartstudy.sync.*
import uz.smartstudy.control.alarms.*
import uz.smartstudy.domain.Policy
import uz.smartstudy.control.location.LocationScreen
import uz.smartstudy.domain.PhotoChallenge

@AndroidEntryPoint class MainActivity:ComponentActivity() {
    override fun onCreate(savedInstanceState:Bundle?) { super.onCreate(savedInstanceState);setContent { StudyTheme { StudyApp() } } }
}
@Composable fun StudyApp(vm:StudyViewModel=hiltViewModel()) {
    var introShown by remember { mutableStateOf(false) }
    LaunchedEffect(Unit) { delay(1850); introShown = true }
    if (!introShown) {
        SmartStudySplash()
        return
    }
    val state by vm.state.collectAsStateWithLifecycle()
    val context=LocalContext.current
    Surface(Modifier.fillMaxSize()) {
        if(!state.authenticated) LoginScreen(vm,state) else if(vm.user?.get("must_change_password")?.jsonPrimitive?.booleanOrNull==true) RenewPasswordScreen(vm) else {
            val nav=rememberNavController()
            Column(Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding()) {
                Row(Modifier.fillMaxWidth().padding(12.dp),horizontalArrangement=Arrangement.SpaceBetween) {
                    Column(Modifier.weight(1f)) {
                        Text("SMART STUDY",style=MaterialTheme.typography.titleMedium,color=MaterialTheme.colorScheme.primary)
                        Text(vm.user?.text("name").orEmpty(),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant,maxLines=1)
                    }
                    TextButton(onClick={vm.refresh();SyncWorker.now(context)}) { Text(stringResource(R.string.sync)) }
                    TextButton(onClick={NotificationSync.clear(context);vm.logout()}) { Text(stringResource(R.string.logout)) }
                }
                if(state.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
                if(state.error) Text(stringResource(R.string.error),color=MaterialTheme.colorScheme.error,modifier=Modifier.padding(12.dp))
                state.notice?.let { Text(stringResource(it),modifier=Modifier.padding(12.dp)) }
                if(state.queued>0) TextButton(onClick={nav.navigate("offline")}) { Text(stringResource(R.string.offline)+": ${state.queued}") }
                NavHost(nav,startDestination="home",modifier=Modifier.weight(1f)) {
                    composable("home") { HomeScreen(vm){nav.navigate(it)} }
                    composable("assignments") { Page(R.string.assignments) {
                        if(state.assignments.isEmpty()) Text(stringResource(R.string.empty))
                        state.assignments.forEach { task -> Card(modifier=Modifier.fillMaxWidth().padding(vertical=5.dp),onClick={nav.navigate("assignment/${task.text("id")}")}) { Column(Modifier.padding(18.dp)) { Text(task.text("title"),style=MaterialTheme.typography.titleMedium);Text(task.text("subject")+" · "+task.text("status")) } } }
                    } }
                    composable("assignment/{id}") { entry -> AssignmentScreen(vm,entry.arguments!!.getString("id")!!) }
                    composable("location") { LocationScreen(vm) }
                    composable("staff-security") { StaffSecurityScreen(vm) }
                    composable("books") { BookLearningScreen(vm) }
                    composable("tutor") { TutorScreen(vm) }
                    composable("quizzes") { QuizLibrary(vm){nav.navigate("quiz/$it")} }
                    composable("quiz/{id}") { entry -> QuizScreen(vm,entry.arguments!!.getString("id")!!) }
                    composable("apps") { AppsScreen(vm) }
                    composable("rewards") { RewardsScreen(vm) }
                    composable("focus") { FocusScreen(vm) }
                    composable("alarms") { AlarmsScreen() }
                    composable("family") { FamilyScreen(vm) }
                    composable("create") { CreateAssignment(vm) }
                    composable("device") { DeviceScreen(vm) }
                    composable("reports") { ReportsScreen(vm) }
                    composable("notifications") { NotificationsScreen(vm) }
                    composable("offline") { QueueScreen(vm) }
                    composable("sleep") { Page(R.string.sleep) { Text(stringResource(R.string.sleep_help));Text(PolicyStore(context).policy) } }
                    composable("settings") { SettingsScreen(vm) }
                }
            }
        }
    }
}
@Composable fun Page(title:Int,content:@Composable ColumnScope.()->Unit) {
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(horizontal=20.dp,vertical=16.dp),verticalArrangement=Arrangement.spacedBy(14.dp)) {
        Text(stringResource(title),style=MaterialTheme.typography.headlineMedium)
        content()
    }
}
@Composable fun Input(label:Int,value:String,change:(String)->Unit) { OutlinedTextField(value,onValueChange=change,label={Text(stringResource(label))},modifier=Modifier.fillMaxWidth()) }
@Composable fun Action(label:Int,enabled:Boolean=true,action:()->Unit) { Button(onClick=action,enabled=enabled,modifier=Modifier.fillMaxWidth().heightIn(min=48.dp)) { Text(stringResource(label)) } }
@Composable fun LoginScreen(vm:StudyViewModel,state:StudyState) {
    var email by remember { mutableStateOf("") };var password by remember { mutableStateOf("") };var name by remember { mutableStateOf("") }
    var registering by remember { mutableStateOf(false) };var passwordMode by remember { mutableStateOf(false) }
    Page(R.string.app_name) {
        androidx.compose.foundation.Image(
            painter = androidx.compose.ui.res.painterResource(R.drawable.smartstudy_logo),
            contentDescription = stringResource(R.string.app_name),
            contentScale = androidx.compose.ui.layout.ContentScale.Fit,
            modifier = Modifier.fillMaxWidth().height(112.dp).padding(horizontal = 12.dp)
        )
        Spacer(Modifier.height(8.dp))
        Text("SMART STUDY",style=MaterialTheme.typography.labelLarge,color=MaterialTheme.colorScheme.primary)
        Text("Learn. Achieve. Unlock.",style=MaterialTheme.typography.headlineLarge)
        Text(stringResource(R.string.login_subtitle),style=MaterialTheme.typography.bodyLarge,color=MaterialTheme.colorScheme.onSurfaceVariant)
        Spacer(Modifier.height(18.dp))
        Input(R.string.phone_or_login,email){email=it}
        if(passwordMode || registering) OutlinedTextField(password,{password=it},label={Text(stringResource(R.string.password))},visualTransformation=PasswordVisualTransformation(),modifier=Modifier.fillMaxWidth(),minLines=1)
        if(registering) {
            Input(R.string.name,name){name=it}
        }
        if(state.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
        if(state.error) Text(stringResource(R.string.error),color=MaterialTheme.colorScheme.error)
        if(!registering && !passwordMode) TelegramSignIn(vm,email)
        if(passwordMode || registering) Action(if(registering) R.string.register else R.string.sign_in,!state.busy && email.isNotBlank() && password.isNotBlank() && (!registering || (name.isNotBlank() && password.length >= 12))) { vm.auth(email,password,if(registering) name else null,false) }
        TextButton(onClick={if(registering){registering=false;passwordMode=false}else passwordMode=!passwordMode}) { Text(stringResource(if(registering) R.string.sign_in else if(passwordMode) R.string.login_with_telegram else R.string.login_with_password)) }
        TextButton(onClick={registering=true;passwordMode=true}) { Text(stringResource(R.string.student_register)) }
    }
}
@Composable fun HomeScreen(vm:StudyViewModel,navigate:(String)->Unit) {
    LaunchedEffect(Unit) { vm.refresh() }
    val state by vm.state.collectAsStateWithLifecycle()
    if(vm.user?.text("role")=="STUDENT") {
        StudentDashboard(vm,state,navigate)
        return
    }
    Page(R.string.home) {
        androidx.compose.foundation.Image(
            painter = androidx.compose.ui.res.painterResource(R.drawable.smartstudy_logo),
            contentDescription = stringResource(R.string.app_name),
            contentScale = androidx.compose.ui.layout.ContentScale.Fit,
            modifier = Modifier.fillMaxWidth().height(76.dp).padding(horizontal = 30.dp)
        )
        Text(vm.user?.text("name").orEmpty(),style=MaterialTheme.typography.headlineLarge)
        Text("${state.assignments.count { it.text("status")=="APPROVED" }} / ${state.assignments.size}",style=MaterialTheme.typography.displayMedium)
        LinearProgressIndicator(progress={if(state.assignments.isEmpty()) 0f else state.assignments.count {it.text("status")=="APPROVED"}.toFloat()/state.assignments.size},modifier=Modifier.fillMaxWidth())
        val items=when(vm.user?.text("role")) {
            "TEACHER" -> listOf("books" to R.string.books,"assignments" to R.string.assignments,"quizzes" to R.string.quizzes,"staff-security" to R.string.account_security,"notifications" to R.string.notifications,"settings" to R.string.settings)
            "SUPER_ADMIN" -> listOf("books" to R.string.books,"assignments" to R.string.assignments,"staff-security" to R.string.staff_security,"notifications" to R.string.notifications,"settings" to R.string.settings)
            "PARENT" -> listOf("family" to R.string.family,"create" to R.string.create_assignment,"assignments" to R.string.assignments,"books" to R.string.books,"reports" to R.string.reports,"staff-security" to R.string.account_security,"notifications" to R.string.notifications,"settings" to R.string.settings)
            else -> listOf("staff-security" to R.string.account_security,"notifications" to R.string.notifications,"settings" to R.string.settings)
        }
        items.forEach { (route,label) -> OutlinedButton(onClick={navigate(route)},modifier=Modifier.fillMaxWidth().heightIn(min=52.dp)) { Text(stringResource(label)) } }
    }
}
@Composable private fun StudentDashboard(vm:StudyViewModel,state:StudyState,navigate:(String)->Unit) {
    var wallet by remember { mutableStateOf<JsonObject?>(null) }
    LaunchedEffect(Unit) { vm.run { wallet=vm.repository.api.get("rewards/wallet") } }
    Page(R.string.home) {
        androidx.compose.foundation.Image(
            painter = androidx.compose.ui.res.painterResource(R.drawable.smartstudy_logo),
            contentDescription = stringResource(R.string.app_name),
            contentScale = androidx.compose.ui.layout.ContentScale.Fit,
            modifier = Modifier.fillMaxWidth().height(96.dp).padding(horizontal = 20.dp)
        )
        Card(Modifier.fillMaxWidth()) {
            androidx.compose.foundation.Image(
                painter = androidx.compose.ui.res.painterResource(R.drawable.student_reading),
                contentDescription = stringResource(R.string.study_illustration),
                contentScale = androidx.compose.ui.layout.ContentScale.Crop,
                modifier = Modifier.fillMaxWidth().height(172.dp)
            )
        }
        Text(stringResource(R.string.student_greeting,vm.user?.text("name").orEmpty()),style=MaterialTheme.typography.headlineLarge)
        Text(stringResource(R.string.today_learning),style=MaterialTheme.typography.bodyLarge,color=MaterialTheme.colorScheme.onSurfaceVariant)
        Card(Modifier.fillMaxWidth(),colors=CardDefaults.cardColors(containerColor=MaterialTheme.colorScheme.primaryContainer)) {
            Column(Modifier.padding(24.dp),verticalArrangement=Arrangement.spacedBy(14.dp)) {
                Text(stringResource(R.string.books),style=MaterialTheme.typography.headlineMedium)
                Text(stringResource(R.string.books_home_subtitle),style=MaterialTheme.typography.bodyLarge)
                Button(onClick={navigate("books")},modifier=Modifier.fillMaxWidth().heightIn(min=58.dp)) { Text(stringResource(R.string.open_library),style=MaterialTheme.typography.titleMedium) }
            }
        }
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(22.dp),verticalArrangement=Arrangement.spacedBy(10.dp)) {
                Text(stringResource(R.string.assignments),style=MaterialTheme.typography.titleLarge)
                Text("${state.assignments.count { it.text("status") != "APPROVED" }}",style=MaterialTheme.typography.displayMedium,color=MaterialTheme.colorScheme.tertiary)
                Text(stringResource(R.string.assignments_home_subtitle),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
                OutlinedButton(onClick={navigate("assignments")},modifier=Modifier.fillMaxWidth().heightIn(min=54.dp)) { Text(stringResource(R.string.open_assignments)) }
            }
        }
        Card(Modifier.fillMaxWidth(),colors=CardDefaults.cardColors(containerColor=MaterialTheme.colorScheme.surfaceVariant)) {
            Row(Modifier.fillMaxWidth().padding(20.dp),horizontalArrangement=Arrangement.SpaceBetween) {
                Column {
                    Text(stringResource(R.string.available),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
                    Text(wallet?.text("available")?.ifBlank { "0" } ?: "—",style=MaterialTheme.typography.headlineMedium)
                }
                Button(onClick={navigate("apps")},modifier=Modifier.heightIn(min=52.dp)) { Text(stringResource(R.string.apps)) }
            }
        }
        Row(horizontalArrangement=Arrangement.spacedBy(12.dp)) {
            OutlinedButton(onClick={navigate("tutor")},modifier=Modifier.weight(1f).heightIn(min=64.dp)) { Text(stringResource(R.string.tutor)) }
            OutlinedButton(onClick={navigate("quizzes")},modifier=Modifier.weight(1f).heightIn(min=64.dp)) { Text(stringResource(R.string.quizzes)) }
        }
        Row(horizontalArrangement=Arrangement.spacedBy(12.dp)) {
            OutlinedButton(onClick={navigate("rewards")},modifier=Modifier.weight(1f).heightIn(min=64.dp)) { Text(stringResource(R.string.rewards)) }
            OutlinedButton(onClick={navigate("focus")},modifier=Modifier.weight(1f).heightIn(min=64.dp)) { Text(stringResource(R.string.focus)) }
        }
        Row(horizontalArrangement=Arrangement.spacedBy(12.dp)) {
            OutlinedButton(onClick={navigate("alarms")},modifier=Modifier.weight(1f).heightIn(min=64.dp)) { Text(stringResource(R.string.alarms)) }
            OutlinedButton(onClick={navigate("reports")},modifier=Modifier.weight(1f).heightIn(min=64.dp)) { Text(stringResource(R.string.reports)) }
        }
        Row(horizontalArrangement=Arrangement.spacedBy(12.dp)) {
            OutlinedButton(onClick={navigate("notifications")},modifier=Modifier.weight(1f).heightIn(min=64.dp)) { Text(stringResource(R.string.notifications)) }
            OutlinedButton(onClick={navigate("settings")},modifier=Modifier.weight(1f).heightIn(min=64.dp)) { Text(stringResource(R.string.settings)) }
        }
        OutlinedButton(onClick={navigate("location")},modifier=Modifier.fillMaxWidth().heightIn(min=54.dp)) { Text(stringResource(R.string.location_sharing)) }
        Row(horizontalArrangement=Arrangement.spacedBy(12.dp)) {
            OutlinedButton(onClick={navigate("family")},modifier=Modifier.weight(1f).heightIn(min=64.dp)) { Text(stringResource(R.string.family)) }
            OutlinedButton(onClick={navigate("device")},modifier=Modifier.weight(1f).heightIn(min=64.dp)) { Text(stringResource(R.string.device_status)) }
        }
        OutlinedButton(onClick={navigate("sleep")},modifier=Modifier.fillMaxWidth().heightIn(min=54.dp)) { Text(stringResource(R.string.sleep)) }
        OutlinedButton(onClick={navigate("staff-security")},modifier=Modifier.fillMaxWidth().heightIn(min=54.dp)) { Text(stringResource(R.string.account_security)) }
    }
}
@Composable fun AssignmentScreen(vm:StudyViewModel,id:String) {
    val state by vm.state.collectAsStateWithLifecycle()
    var detail by remember { mutableStateOf<JsonObject?>(null) };var text by remember { mutableStateOf("") };var review by remember { mutableStateOf<JsonObject?>(null) }
    val task=detail ?: state.assignments.firstOrNull {it.text("id")==id}
    fun load(){vm.run {detail=vm.repository.api.get("assignments/$id")} }
    LaunchedEffect(id){load()}
    Page(R.string.assignments) {
        Text(task?.text("title").orEmpty(),style=MaterialTheme.typography.titleLarge)
        Text(task?.text("description").orEmpty());Text(task?.text("status").orEmpty())
        if(vm.user?.text("role")=="STUDENT") { Input(R.string.answer,text){text=it};Action(R.string.submit,text.isNotBlank()){vm.submit(id,text)} }
        detail?.get("submissions")?.jsonArray?.reversed()?.forEach { element ->
            val sub=element.jsonObject
            Card(Modifier.fillMaxWidth()) { Column(Modifier.padding(16.dp),verticalArrangement=Arrangement.spacedBy(10.dp)) {
                Text(sub.text("text"));Text(sub.text("status"))
                Action(R.string.review) {vm.run { review=vm.repository.api.post("ai/evaluate-homework?submission_id=${sub.text("id")}",buildJsonObject {}) }}
                if(vm.user?.text("role")!="STUDENT") {
                    Action(R.string.approved) {vm.run {vm.repository.api.post("submissions/${sub.text("id")}/approve",buildJsonObject {});detail=vm.repository.api.get("assignments/$id");vm.repository.refreshAssignments()} }
                    Action(R.string.revision) {vm.run {vm.repository.api.post("submissions/${sub.text("id")}/review",body("decision" to "REVISION_REQUESTED"));detail=vm.repository.api.get("assignments/$id")} }
                }
            } }
        }
        review?.let { Text(it.text("feedback"));Text("${it.text("correct")} / ${it.text("total")}") }
        detail?.get("attachments")?.jsonArray?.forEach { file ->
            Text(file.jsonObject.text("filename") + " · " + file.jsonObject.text("media_type"))
        }
    }
}
@Composable fun TutorScreen(vm:StudyViewModel) {
    var message by remember { mutableStateOf("") };var response by remember { mutableStateOf<JsonObject?>(null) }
    Page(R.string.tutor) { Input(R.string.message,message){message=it};Action(R.string.ask,message.isNotBlank()){vm.run {response=vm.repository.api.post("ai/tutor",body("message" to message))}}
        response?.let { Text(it.text("explanation"));it["hints"]?.jsonArray?.forEach { hint->Text("• "+hint.jsonPrimitive.content) };it["practice"]?.jsonArray?.forEach { q->Text(q.jsonPrimitive.content) } }
    }
}
@Composable fun QuizLibrary(vm:StudyViewModel,open:(String)->Unit) {
    var quizzes by remember { mutableStateOf<List<JsonObject>>(emptyList()) }
    LaunchedEffect(Unit){vm.run {quizzes=vm.repository.api.list("quizzes")} }
    Page(R.string.quizzes){ if(quizzes.isEmpty()) Text(stringResource(R.string.empty));quizzes.forEach {q -> OutlinedButton(onClick={open(q.text("id"))},modifier=Modifier.fillMaxWidth()){Text(q.text("title"))} } }
}
@Composable fun QuizScreen(vm:StudyViewModel,id:String) {
    var quiz by remember { mutableStateOf<JsonObject?>(null) };var started by remember { mutableStateOf(false) };var results by remember { mutableStateOf<JsonObject?>(null) }
    val answers=remember { mutableStateMapOf<String,String>() }
    LaunchedEffect(id){vm.run {quiz=vm.repository.api.get("quizzes/$id")} }
    Page(R.string.quizzes) {
        Text(quiz?.text("title").orEmpty());Text(quiz?.text("time_limit_seconds").orEmpty()+" s")
        if(!started) Action(R.string.start,quiz!=null){vm.run {vm.repository.api.post("quizzes/$id/start",buildJsonObject {});started=true} }
        if(started && results==null) {
            quiz?.get("questions")?.jsonArray?.forEach { e -> val q=e.jsonObject
                Text(q.text("prompt"),style=MaterialTheme.typography.titleMedium)
                q["options"]?.jsonArray?.forEach { o -> val option=o.jsonPrimitive.content
                    Row { RadioButton(selected=answers[q.text("id")]==option,onClick={answers[q.text("id")]=option});Text(option,modifier=Modifier.padding(top=14.dp)) }
                }
            }
            Action(R.string.finish){vm.run { results=vm.repository.api.post("quizzes/$id/finish",buildJsonObject {put("answers",buildJsonObject {answers.forEach {(k,v)->put(k,v)} })}) } }
        }
        results?.let { Text(it.text("score"),style=MaterialTheme.typography.displayMedium);it["explanations"]?.jsonArray?.forEach { e->Text(e.jsonObject.text("answer")+": "+e.jsonObject.text("explanation")) } }
    }
}
@Composable fun AppsScreen(vm:StudyViewModel) {
    val context=LocalContext.current;val controller=remember {DeviceController(context)}
    var minutes by remember {mutableStateOf("15")}
    val policy=runCatching {Json.decodeFromString<Policy>(PolicyStore(context).policy)}.getOrDefault(Policy())
    Page(R.string.apps) {
        Text(stringResource(if(controller.managed) R.string.managed else R.string.voluntary));Text(stringResource(R.string.essential_help))
        Input(R.string.minutes,minutes){minutes=it}
        controller.visibleApps().filter {it.first in policy.blocked_packages}.forEach {(pkg,label)->
            Card(Modifier.fillMaxWidth()) {Column(Modifier.padding(16.dp)) {Text(label);Text(pkg);Action(R.string.unlock,minutes.toIntOrNull() in 1..120){vm.run {DeviceSync.redeem(context,vm.repository,pkg,minutes.toInt());} } } }
        }
        if(policy.blocked_packages.isEmpty()) Text(stringResource(R.string.empty))
    }
}
@Composable fun RewardsScreen(vm:StudyViewModel) {
    var wallet by remember {mutableStateOf<JsonObject?>(null)};var ledger by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    LaunchedEffect(Unit){vm.run {wallet=vm.repository.api.get("rewards/wallet");ledger=vm.repository.api.list("rewards/ledger")} }
    Page(R.string.rewards){Text(stringResource(R.string.available));Text(wallet?.text("available").orEmpty(),style=MaterialTheme.typography.displayLarge);ledger.forEach {Text(it.text("kind")+"  "+it.text("delta"))} }
}
@Composable fun FocusScreen(vm:StudyViewModel) {
    val context=LocalContext.current;val prefs=remember {context.getSharedPreferences("focus_timer",0)}
    var subject by remember {mutableStateOf("")};var minutes by remember {mutableStateOf("25")}
    var deadline by remember {mutableLongStateOf(if(prefs.getInt("boot",-1)==PolicyStore.boot(context)) prefs.getLong("deadline",0) else 0)}
    var remaining by remember {mutableLongStateOf(0)}
    LaunchedEffect(Unit) {
        vm.run {
            val active=vm.repository.api.list("focus").firstOrNull {it.text("status")=="ACTIVE"}
            if(active!=null && deadline==0L) {
                val start=java.time.Instant.parse(active.text("created_at"))
                val duration=active.text("duration_seconds").toLong()
                val left=(duration-java.time.Duration.between(start,java.time.Instant.now()).seconds).coerceIn(0,duration)
                deadline=SystemClock.elapsedRealtime()+left*1000
                prefs.edit().putLong("deadline",deadline).putInt("boot",PolicyStore.boot(context)).putString("session",active.text("id")).apply()
            }
        }
    }
    LaunchedEffect(deadline){while(true){remaining=((deadline-SystemClock.elapsedRealtime())/1000).coerceAtLeast(0);delay(500)} }
    Page(R.string.focus) {
        Text(stringResource(R.string.focus_help));Text("${remaining/60}:${(remaining%60).toString().padStart(2,'0')}",style=MaterialTheme.typography.displayLarge)
        Input(R.string.subject,subject){subject=it};Input(R.string.minutes,minutes){minutes=it}
        Action(R.string.start,deadline==0L && minutes.toIntOrNull() in 1..180 && subject.isNotBlank()){
            deadline=SystemClock.elapsedRealtime()+minutes.toLong()*60_000
            prefs.edit().putLong("deadline",deadline).putInt("boot",PolicyStore.boot(context)).apply()
            val policyStore=PolicyStore(context);policyStore.focusDeadline=deadline;policyStore.focusBoot=PolicyStore.boot(context)
            runCatching {PolicyEnforcer.apply(context,Json.decodeFromString<Policy>(policyStore.policy))}
            vm.run {val session=vm.repository.api.post("focus",buildJsonObject {put("subject",subject);put("duration_seconds",minutes.toInt()*60)});prefs.edit().putString("session",session.text("id")).apply()}
        }
        if(deadline>0) {
            Action(if(remaining==0L) R.string.finish else R.string.cancel){
                val id=prefs.getString("session",null)
                if(id!=null) vm.run {vm.repository.api.post("focus/$id/"+(if(remaining==0L) "complete" else "cancel"),buildJsonObject {})}
                deadline=0;prefs.edit().clear().apply()
                val policyStore=PolicyStore(context);policyStore.focusDeadline=0
                runCatching {PolicyEnforcer.apply(context,Json.decodeFromString<Policy>(policyStore.policy))}
            }
        }
    }
}
@Composable fun AlarmsScreen() {
    val context=LocalContext.current;val scheduler=remember {AlarmScheduler(context)}
    var alarms by remember {mutableStateOf(scheduler.alarms())};var hour by remember {mutableStateOf("7")};var minute by remember {mutableStateOf("0")};var days by remember {mutableStateOf("1,2,3,4,5")}
    var exact by remember {mutableStateOf(scheduler.canExact())}
    var photo by remember {mutableStateOf(true)};var objects by remember {mutableStateOf(setOf("book","bottle"))}
    Page(R.string.alarms){
        Action(R.string.dismiss){AlarmMission(context).finish("MANUAL_DISMISS");context.stopService(Intent(context,AlarmSoundService::class.java))}
        Row {Checkbox(photo,{photo=it});Text(stringResource(R.string.photo_alarm))}
        Text(stringResource(R.string.photo_objects_help))
        PhotoChallenge.objects.keys.forEach {target->Row {Checkbox(target in objects,{selected->objects=if(selected)objects+target else objects-target});Text(stringResource(objectName(target)))}}
        Action(R.string.photo_alarm){context.startActivity(Intent(context,PhotoAlarmActivity::class.java))}
        Text(stringResource(R.string.permission_help));if(!exact) Text(stringResource(R.string.exact_alarm),color=MaterialTheme.colorScheme.error)
        Input(R.string.hour,hour){hour=it};Input(R.string.minute,minute){minute=it};Input(R.string.weekly_days,days){days=it}
        val selected=days.split(",").mapNotNull {it.trim().toIntOrNull()}.toSet()
        Action(R.string.save,hour.toIntOrNull() in 0..23 && minute.toIntOrNull() in 0..59 && selected.isNotEmpty() && selected.all {it in 1..7} && (!photo || objects.isNotEmpty())) {
            exact=scheduler.save(LocalAlarm((System.currentTimeMillis()%Int.MAX_VALUE).toInt(),hour.toInt(),minute.toInt(),selected,photo=photo,objects=objects));alarms=scheduler.alarms()
        }
        AlarmMission(context).history().forEach {(label,time)->Text(stringResource(label)+" · "+time)}
        alarms.forEach {alarm -> Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween){Text("%02d:%02d".format(alarm.hour,alarm.minute));TextButton(onClick={scheduler.remove(alarm.id);alarms=scheduler.alarms()}){Text(stringResource(R.string.remove))}} }
    }
}
@Composable fun FamilyScreen(vm:StudyViewModel) {
    var code by remember {mutableStateOf("")};var generated by remember {mutableStateOf("")};var consent by remember {mutableStateOf(false)};var children by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    val student=vm.user?.text("role")=="STUDENT"
    LaunchedEffect(Unit){if(!student && vm.user?.text("role")=="PARENT")vm.run {children=vm.repository.api.list("families/children")} }
    Page(R.string.family) {
        if(student) {Action(R.string.create_code){vm.run {generated=vm.repository.api.post("families/invite",buildJsonObject {}).text("code")}};Text(generated)}
        Input(R.string.code,code){code=it}
        if(student) Action(R.string.join_class,code.isNotBlank()){vm.run {vm.repository.api.post("classrooms/join",body("code" to code))} }
        else {Row {Checkbox(consent,{consent=it});Text(stringResource(R.string.consent))};Action(R.string.link_child,consent && code.isNotBlank()){vm.run {vm.repository.api.post("families/link-child",buildJsonObject {put("code",code);put("guardian_consent",true)});children=vm.repository.api.list("families/children")}} }
        children.forEach {Text(it.text("name"));SelectionContainerText(it.text("id"))}
    }
}
@Composable fun SelectionContainerText(value:String) { androidx.compose.foundation.text.selection.SelectionContainer {Text(value)} }
@Composable fun CreateAssignment(vm:StudyViewModel) {
    var child by remember {mutableStateOf("")};var title by remember {mutableStateOf("")};var subject by remember {mutableStateOf("")};var description by remember {mutableStateOf("")}
    val context=LocalContext.current
    var selected by remember { mutableStateOf<List<PickedAttachment>>(emptyList()) }
    var createdId by remember { mutableStateOf("") }
    val uploaded=remember { mutableStateSetOf<String>() }
    val uploadedNames=remember { mutableStateListOf<String>() }
    val picker=rememberLauncherForActivityResult(ActivityResultContracts.OpenMultipleDocuments()) { uris ->
        selected=uris.take(5).map { PickedAttachment(it,AssignmentAttachments.displayName(context,it)) }
    }
    Page(R.string.create_assignment){
        Input(R.string.child_id,child){child=it};Input(R.string.title,title){title=it};Input(R.string.subject,subject){subject=it};Input(R.string.description,description){description=it}
        Action(R.string.add_attachments,createdId.isEmpty() && selected.size<5){picker.launch(arrayOf("application/pdf","image/*"))}
        selected.forEach { file -> Text(file.name + " · " + (AssignmentAttachments.mediaType(context,file.uri) ?: stringResource(R.string.unsupported_attachment))) }
        if(createdId.isEmpty()) Action(R.string.save,child.isNotBlank() && title.isNotBlank() && subject.isNotBlank() && selected.all { AssignmentAttachments.mediaType(context,it.uri)!=null }) {
            vm.run {
                val assignment=vm.repository.api.post("assignments",body("student_id" to child,"title" to title,"subject" to subject,"description" to description))
                createdId=assignment.text("id")
                for(file in selected) if(file.uri.toString() !in uploaded) { AssignmentAttachments.upload(context,vm.repository.api,createdId,file);uploaded.add(file.uri.toString());uploadedNames.add(file.name) }
                selected=emptyList()
                vm.repository.refreshAssignments()
            }
        } else {
            Text(stringResource(if(selected.isEmpty()) R.string.assignment_created else R.string.attachments_uploaded_hint))
            uploadedNames.forEach { Text(it) }
            Action(R.string.upload_attachments,selected.isNotEmpty()) {
                vm.run {
                    for(file in selected) if(file.uri.toString() !in uploaded) { AssignmentAttachments.upload(context,vm.repository.api,createdId,file);uploaded.add(file.uri.toString());uploadedNames.add(file.name) }
                    selected=emptyList()
                    vm.repository.refreshAssignments()
                }
            }
        }
    }
}
@Composable fun DeviceScreen(vm:StudyViewModel) {
    val context=LocalContext.current;val controller=remember {DeviceController(context)};val store=remember {PolicyStore(context)}
    var id by remember {mutableStateOf(store.deviceId)}
    Page(R.string.device_status){
        Text(stringResource(if(controller.managed) R.string.managed else R.string.voluntary));Text(stringResource(R.string.device_help));Text(id)
        Text(stringResource(if(controller.uninstallProtected()) R.string.protection_active else R.string.protection_inactive))
        if(id.isEmpty()) Action(R.string.enroll){vm.run {val d=vm.repository.api.post("devices",body("name" to Build.MODEL));id=d.text("id");store.deviceId=id} }
        else Action(R.string.sync){vm.run {DeviceSync.sync(context,vm.repository)} }
        Text("${store.version}")
    }
}
@Composable fun ReportsScreen(vm:StudyViewModel) {
    var report by remember {mutableStateOf<JsonObject?>(null)}
    LaunchedEffect(Unit){vm.run {report=vm.repository.api.get("reports/weekly")} }
    Page(R.string.reports){report?.let {Text(stringResource(R.string.approved)+": "+it.text("approved")+" / "+it.text("assigned"));Text(stringResource(R.string.focus)+": "+it.text("focus_seconds")+" s");Text(stringResource(R.string.rewards)+": "+it.text("reward_minutes_earned"))} }
}
@Composable fun NotificationsScreen(vm:StudyViewModel) {
    var rows by remember {mutableStateOf<List<JsonObject>>(emptyList())}
    LaunchedEffect(Unit){vm.run {rows=vm.repository.api.list("notifications")} }
    Page(R.string.notifications){if(rows.isEmpty()) Text(stringResource(R.string.empty));rows.forEach {n->Card(Modifier.fillMaxWidth()){Column(Modifier.padding(16.dp)){Text(n.text("title"));Text(n.text("body"));if(n.text("read")!="true")Action(R.string.ack){vm.run {vm.repository.api.post("notifications/${n.text("id")}/read",buildJsonObject {});rows=vm.repository.api.list("notifications")}}}}} }
}
@Composable fun QueueScreen(vm:StudyViewModel) {
    var rows by remember {mutableStateOf<List<uz.smartstudy.data.Outbox>>(emptyList())}
    LaunchedEffect(Unit){vm.run {rows=vm.repository.pending()} }
    Page(R.string.offline){Text(stringResource(R.string.queue_help));Action(R.string.retry){vm.run {vm.repository.flush();rows=vm.repository.pending()}};rows.forEach {row->Text(row.body);row.error?.let {Text(it)};Action(R.string.remove){vm.run {vm.repository.discard(row.key);rows=vm.repository.pending()}}} }
}
@Composable fun SettingsScreen(vm:StudyViewModel) {
    val context=LocalContext.current
    val launcher=rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()){}
    Page(R.string.settings){
        Text(stringResource(R.string.privacy_text))
        Action(R.string.notifications){if(Build.VERSION.SDK_INT>=33)launcher.launch(Manifest.permission.POST_NOTIFICATIONS)else context.startActivity(Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS).putExtra(Settings.EXTRA_APP_PACKAGE,context.packageName))}
        Action(R.string.exact_alarm){if(Build.VERSION.SDK_INT>=31)context.startActivity(Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM,Uri.parse("package:${context.packageName}")))}
        Action(R.string.language){context.startActivity(if(Build.VERSION.SDK_INT>=33)Intent(Settings.ACTION_APP_LOCALE_SETTINGS,Uri.parse("package:${context.packageName}"))else Intent(Settings.ACTION_LOCALE_SETTINGS))}
        Action(R.string.dismiss){AlarmMission(context).finish("MANUAL_DISMISS");context.stopService(Intent(context,AlarmSoundService::class.java))}
        Action(R.string.photo_alarm){context.startActivity(Intent(context,PhotoAlarmActivity::class.java))}
        Action(R.string.delete_request){vm.run {vm.repository.api.post("privacy/deletion-request",buildJsonObject {})}}
    }
}
