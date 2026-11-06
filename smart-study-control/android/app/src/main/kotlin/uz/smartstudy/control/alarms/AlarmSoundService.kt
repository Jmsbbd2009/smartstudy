package uz.smartstudy.control.alarms
import android.app.*
import android.content.*
import android.media.*
import android.os.*
import androidx.core.app.NotificationCompat
import uz.smartstudy.control.R
class AlarmSoundService:Service() {
    private var ringtone:Ringtone?=null
    private val handler=Handler(Looper.getMainLooper())
    override fun onBind(intent:Intent?)=null
    override fun onStartCommand(intent:Intent?,flags:Int,startId:Int):Int {
        val id=intent?.getIntExtra("id",1) ?: 1
        channel(this)
        val alarm=AlarmScheduler(this).alarms().find {it.id==id}
        val target=AlarmMission(this).begin(id,if(alarm?.photo==true) alarm.objects else emptySet())
        val mission=PendingIntent.getActivity(this,717,Intent(this,PhotoAlarmActivity::class.java),PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val dismiss=PendingIntent.getBroadcast(this,1,Intent(this,StudyAlarmReceiver::class.java).setAction("uz.smartstudy.DISMISS"),PendingIntent.FLAG_IMMUTABLE)
        val snooze=PendingIntent.getBroadcast(this,2,Intent(this,StudyAlarmReceiver::class.java).setAction("uz.smartstudy.SNOOZE").putExtra("id",id),PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val notification=NotificationCompat.Builder(this,"study_alarm")
            .setSmallIcon(android.R.drawable.ic_lock_idle_alarm).setContentTitle(getString(R.string.wake_up)).setContentText(getString(if(target.isNotEmpty()) objectName(target) else R.string.alarm_help))
            .setCategory(NotificationCompat.CATEGORY_ALARM).setPriority(NotificationCompat.PRIORITY_HIGH)
            .setContentIntent(mission).setOngoing(true).addAction(0,getString(R.string.dismiss),dismiss).addAction(0,getString(R.string.snooze),snooze).build()
        startForeground(717,notification)
        ringtone?.stop()
        ringtone=RingtoneManager.getRingtone(this,RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM))?.apply {
            audioAttributes=AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ALARM).setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build()
            if(Build.VERSION.SDK_INT>=28) isLooping=true
            play()
        }
        val vibrator=getSystemService(Vibrator::class.java)
        if(vibrator.hasVibrator()) vibrator.vibrate(VibrationEffect.createWaveform(longArrayOf(0,400,500),0))
        handler.removeCallbacksAndMessages(null)
        handler.postDelayed({AlarmMission(this).finish("TIMEOUT");stopSelf()},5*60_000L) // Bounded, always dismissible; no challenge gate.
        return START_NOT_STICKY
    }
    override fun onDestroy(){ ringtone?.stop();getSystemService(Vibrator::class.java).cancel();handler.removeCallbacksAndMessages(null);super.onDestroy() }
    companion object {
        private fun channel(context:Context) { context.getSystemService(NotificationManager::class.java).createNotificationChannel(NotificationChannel("study_alarm",context.getString(R.string.alarms),NotificationManager.IMPORTANCE_HIGH).apply { setSound(null,null) }) }
        fun notifyMissed(context:Context) {
            channel(context)
            runCatching { context.getSystemService(NotificationManager::class.java).notify(718,NotificationCompat.Builder(context,"study_alarm").setSmallIcon(android.R.drawable.ic_lock_idle_alarm).setContentTitle(context.getString(R.string.missed_alarm)).setContentText(context.getString(R.string.permission_help)).build()) }
        }
    }
}
