package uz.smartstudy.control.location
import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.SystemClock
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.core.content.ContextCompat
import kotlinx.serialization.json.*
import uz.smartstudy.control.*
import uz.smartstudy.control.R
import uz.smartstudy.sync.LocationStopWorker

@Composable fun LocationScreen(vm:StudyViewModel) {
    val context=LocalContext.current;val child=vm.repository.vault.userId()
    var consent by remember {mutableStateOf(false)};var permission by remember {mutableStateOf(false)}
    var latest by remember {mutableStateOf<JsonObject?>(null)};var minutes by remember {mutableStateOf("60")}
    fun allowed()=ContextCompat.checkSelfPermission(context,Manifest.permission.ACCESS_COARSE_LOCATION)==PackageManager.PERMISSION_GRANTED && (Build.VERSION.SDK_INT<33 || ContextCompat.checkSelfPermission(context,Manifest.permission.POST_NOTIFICATIONS)==PackageManager.PERMISSION_GRANTED)
    val request=rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()){permission=allowed()}
    LaunchedEffect(Unit){permission=allowed();vm.run {latest=vm.repository.api.get("location/children/$child/latest")}}
    Page(R.string.location_sharing) {
        Text(stringResource(R.string.location_help))
        Row {Checkbox(consent,{consent=it});Text(stringResource(R.string.location_consent))}
        Input(R.string.minutes,minutes){minutes=it}
        Action(R.string.location_permission){request.launch(arrayOf(Manifest.permission.ACCESS_COARSE_LOCATION,Manifest.permission.ACCESS_FINE_LOCATION)+if(Build.VERSION.SDK_INT>=33)arrayOf(Manifest.permission.POST_NOTIFICATIONS) else emptyArray())}
        Action(R.string.location_start,consent && permission && minutes.toIntOrNull() in 1..240 && latest?.get("active")?.jsonPrimitive?.booleanOrNull!=true){vm.run {
            val duration=minutes.toInt();val start=SystemClock.elapsedRealtime()
            val share=vm.repository.api.post("location/shares",buildJsonObject {put("minutes",duration);put("sharing_consent",true)})
            try {ContextCompat.startForegroundService(context,Intent(context,VisibleLocationService::class.java).putExtra("share",share.text("id")).putExtra("owner",child).putExtra("expires_elapsed",start+duration*60_000L));latest=share}
            catch(e:Exception){LocationStopWorker.enqueue(context,child,share.text("id"));throw e}
        }}
        if(latest?.get("active")?.jsonPrimitive?.booleanOrNull==true){
            Text(stringResource(R.string.location_visible))
            Action(R.string.location_stop){
                context.stopService(Intent(context,VisibleLocationService::class.java))
                LocationStopWorker.enqueue(context,child,latest!!.text("id"));latest=null
            }
        }
        Action(R.string.sync){vm.run {latest=vm.repository.api.get("location/children/$child/latest")}}
    }
}
