package uz.smartstudy.control.alarms

import android.app.Activity
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.os.SystemClock
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.label.ImageLabeling
import com.google.mlkit.vision.label.defaults.ImageLabelerOptions
import org.json.JSONArray
import org.json.JSONObject
import uz.smartstudy.control.R
import uz.smartstudy.designsystem.StudyTheme
import uz.smartstudy.devicepolicy.PolicyStore
import uz.smartstudy.domain.PhotoChallenge
import java.util.UUID

class AlarmMission(private val context:Context) {
    private val prefs=context.getSharedPreferences("alarm_missions",Context.MODE_PRIVATE)
    fun begin(id:Int, choices:Set<String>):String {
        finish("REPLACED")
        val target=PhotoChallenge.eligible(choices).toList().randomOrNull().orEmpty()
        check(prefs.edit().putString("occurrence",UUID.randomUUID().toString()).putInt("alarm",id).putString("target",target).putLong("started",SystemClock.elapsedRealtime()).putInt("boot",PolicyStore.boot(context)).putBoolean("active",true).commit())
        return target
    }
    fun active()=prefs.getBoolean("active",false) && prefs.getInt("boot",-1)==PolicyStore.boot(context) && SystemClock.elapsedRealtime()-prefs.getLong("started",0) in 0..300_000
    fun target()=prefs.getString("target","").orEmpty()
    fun occurrence()=prefs.getString("occurrence","").orEmpty()
    @Synchronized fun finish(reason:String, expected:String?=null):Boolean {
        if(!prefs.getBoolean("active",false) || (expected!=null && expected!=occurrence()))return false
        val history=JSONArray(prefs.getString("history","[]"))
        val row=JSONObject().put("alarm",prefs.getInt("alarm",0)).put("occurrence",occurrence()).put("target",target()).put("reason",reason).put("at",System.currentTimeMillis())
        history.put(row)
        val bounded=JSONArray();for(i in maxOf(0,history.length()-100) until history.length())bounded.put(history.get(i))
        check(prefs.edit().putBoolean("active",false).putString("history",bounded.toString()).commit())
        return true
    }
    fun history():List<Pair<Int,String>> {val list=JSONArray(prefs.getString("history","[]"));return (0 until list.length()).reversed().take(10).map {list.getJSONObject(it).let {row->
        val label=when(row.optString("reason")){"PHOTO_MATCH"->R.string.photo_success;"MANUAL_DISMISS","ACCESSIBLE_DISMISS"->R.string.dismiss;"SNOOZED"->R.string.snooze;"TIMEOUT"->R.string.photo_expired;else->R.string.cancel}
        label to java.text.DateFormat.getDateTimeInstance().format(java.util.Date(row.optLong("at")))
    }}}
}
fun objectName(target:String)=when(target){"book"->R.string.object_book;"bottle"->R.string.object_bottle;"plant"->R.string.object_plant;else->R.string.photo_alarm}

class PhotoAlarmActivity:ComponentActivity() {
    override fun onCreate(state:Bundle?) {
        super.onCreate(state)
        setContent { StudyTheme { PhotoMissionScreen(this) } }
    }
}
@Composable private fun PhotoMissionScreen(activity:Activity) {
    val mission=remember {AlarmMission(activity)}
    val occurrence=remember {mission.occurrence()};val target=remember {mission.target()}
    var busy by remember {mutableStateOf(false)};var status by remember {mutableIntStateOf(if(mission.active())R.string.photo_alarm_help else R.string.photo_expired)}
    val labeler=remember {ImageLabeling.getClient(ImageLabelerOptions.Builder().setConfidenceThreshold(0.5f).build())}
    DisposableEffect(Unit){onDispose {labeler.close()}}
    val capture=rememberLauncherForActivityResult(ActivityResultContracts.TakePicturePreview()) { bitmap ->
        if(bitmap==null){status=R.string.photo_cancelled}
        else if(!mission.active() || mission.occurrence()!=occurrence){status=R.string.photo_expired;bitmap.recycle()}
        else {
            busy=true
            labeler.process(InputImage.fromBitmap(bitmap,0)).addOnSuccessListener { labels ->
                if(mission.active() && PhotoChallenge.matches(target,labels.map {it.text to it.confidence}) && mission.finish("PHOTO_MATCH",occurrence)) {
                    activity.stopService(Intent(activity,AlarmSoundService::class.java));status=R.string.photo_success
                } else status=R.string.photo_retry
            }.addOnFailureListener {status=R.string.photo_unavailable}.addOnCompleteListener {busy=false;bitmap.recycle()}
        }
    }
    Surface(Modifier.fillMaxSize()) {Column(Modifier.fillMaxSize().statusBarsPadding().navigationBarsPadding().padding(24.dp),verticalArrangement=Arrangement.spacedBy(20.dp)) {
        Text(stringResource(R.string.photo_alarm),style=MaterialTheme.typography.headlineLarge)
        Text(stringResource(objectName(target)),style=MaterialTheme.typography.displaySmall)
        Text(stringResource(status))
        Text(stringResource(R.string.photo_privacy))
        if(busy)LinearProgressIndicator(Modifier.fillMaxWidth())
        Button(onClick={runCatching {capture.launch(null)}.onFailure {status=R.string.photo_unavailable}},enabled=!busy && mission.active() && target.isNotEmpty(),modifier=Modifier.fillMaxWidth().heightIn(min=52.dp)){Text(stringResource(R.string.take_photo))}
        OutlinedButton(onClick={mission.finish("ACCESSIBLE_DISMISS",occurrence);activity.stopService(Intent(activity,AlarmSoundService::class.java));activity.finish()},modifier=Modifier.fillMaxWidth().heightIn(min=52.dp)){Text(stringResource(R.string.photo_silence))}
    }}
}
