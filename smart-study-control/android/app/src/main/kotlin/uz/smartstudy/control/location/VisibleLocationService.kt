package uz.smartstudy.control.location

import android.Manifest
import android.app.*
import android.content.*
import android.content.pm.PackageManager
import android.location.*
import android.os.*
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.*
import kotlinx.serialization.json.*
import uz.smartstudy.control.MainActivity
import uz.smartstudy.control.R
import uz.smartstudy.data.StudyRepository
import uz.smartstudy.sync.LocationStopWorker
import javax.inject.Inject

@AndroidEntryPoint class VisibleLocationService:Service(),LocationListener {
    @Inject lateinit var repository:StudyRepository
    private val scope=CoroutineScope(SupervisorJob()+Dispatchers.IO)
    private lateinit var manager:LocationManager
    private var share="";private var owner="";private var expires=0L;private var lastSent=0L
    override fun onBind(intent:Intent?)=null
    override fun onCreate(){super.onCreate();manager=getSystemService(LocationManager::class.java)}
    override fun onStartCommand(intent:Intent?,flags:Int,startId:Int):Int {
        if(intent?.action==STOP){stopSharing();return START_NOT_STICKY}
        share=intent?.getStringExtra("share").orEmpty();owner=intent?.getStringExtra("owner").orEmpty();expires=intent?.getLongExtra("expires_elapsed",0) ?: 0
        if(share.isBlank() || owner!=repository.vault.userId() || expires<=SystemClock.elapsedRealtime()) {stopSharing();return START_NOT_STICKY}
        val notifications=getSystemService(NotificationManager::class.java)
        notifications.createNotificationChannel(NotificationChannel("visible_location",getString(R.string.location_sharing),NotificationManager.IMPORTANCE_LOW))
        val stop=PendingIntent.getService(this,884,Intent(this,VisibleLocationService::class.java).setAction(STOP),PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val open=PendingIntent.getActivity(this,885,Intent(this,MainActivity::class.java),PendingIntent.FLAG_IMMUTABLE)
        startForeground(884,NotificationCompat.Builder(this,"visible_location").setSmallIcon(android.R.drawable.ic_menu_mylocation)
            .setContentTitle(getString(R.string.location_sharing)).setContentText(getString(R.string.location_visible))
            .setContentIntent(open).setOngoing(true).addAction(0,getString(R.string.location_stop),stop).build())
        getSharedPreferences("visible_location",MODE_PRIVATE).edit().putString("share",share).putString("owner",owner).apply()
        if(ContextCompat.checkSelfPermission(this,Manifest.permission.ACCESS_COARSE_LOCATION)!=PackageManager.PERMISSION_GRANTED){stopSharing();return START_NOT_STICKY}
        try {
            manager.removeUpdates(this)
            val providers=if(ContextCompat.checkSelfPermission(this,Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED) listOf(LocationManager.GPS_PROVIDER,LocationManager.NETWORK_PROVIDER) else listOf(LocationManager.NETWORK_PROVIDER)
            providers.forEach { provider->
                if(manager.isProviderEnabled(provider))manager.requestLocationUpdates(provider,30_000L,10f,this,Looper.getMainLooper())
            }
        } catch(e:SecurityException){stopSharing()}
        scope.launch {
            while(isActive){delay(5_000);if(SystemClock.elapsedRealtime()>=expires || repository.vault.userId()!=owner){withContext(Dispatchers.Main){stopSharing()};break}}
        }
        return START_NOT_STICKY // Sharing never restarts silently after reboot/process death.
    }
    override fun onLocationChanged(location:Location) {
        val elapsed=SystemClock.elapsedRealtime()
        if(elapsed>=expires || repository.vault.userId()!=owner){stopSharing();return}
        if(elapsed-lastSent<25_000 || (SystemClock.elapsedRealtimeNanos()-location.elapsedRealtimeNanos) !in 0..90_000_000_000L)return
        lastSent=elapsed
        scope.launch {
            try {repository.api.post("location/shares/$share/point",buildJsonObject {put("latitude",location.latitude);put("longitude",location.longitude);put("accuracy_m",location.accuracy.toDouble().coerceAtLeast(0.0))})}
            catch(e:retrofit2.HttpException){if(e.code() in listOf(401,403,404,409))withContext(Dispatchers.Main){stopSharing()}}
            catch(e:java.io.IOException){ /* The guardian UI labels stale signal. No cached fixes are replayed. */ }
        }
    }
    override fun onProviderEnabled(provider:String){}
    override fun onProviderDisabled(provider:String){}
    @Suppress("DEPRECATION") override fun onStatusChanged(provider:String?,status:Int,extras:Bundle?){}
    private fun stopSharing(){manager.removeUpdates(this);LocationStopWorker.enqueue(this,owner,share);getSharedPreferences("visible_location",MODE_PRIVATE).edit().clear().apply();stopForeground(STOP_FOREGROUND_REMOVE);stopSelf()}
    override fun onDestroy(){manager.removeUpdates(this);LocationStopWorker.enqueue(this,owner,share);getSharedPreferences("visible_location",MODE_PRIVATE).edit().clear().apply();scope.cancel();super.onDestroy()}
    companion object {const val STOP="uz.smartstudy.LOCATION_STOP"}
}
