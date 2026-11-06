package uz.smartstudy.control.alarms
import android.content.*
import androidx.core.content.ContextCompat
class StudyAlarmReceiver:BroadcastReceiver() {
    override fun onReceive(context:Context,intent:Intent) {
        when(intent.action) {
            "uz.smartstudy.RING" -> {
                AlarmScheduler(context).reschedule()
                runCatching { ContextCompat.startForegroundService(context,Intent(context,AlarmSoundService::class.java).putExtra("id",intent.getIntExtra("id",1))) }
                    .onFailure { AlarmSoundService.notifyMissed(context) }
            }
            "uz.smartstudy.DISMISS" -> {AlarmMission(context).finish("MANUAL_DISMISS");context.stopService(Intent(context,AlarmSoundService::class.java))}
            "uz.smartstudy.SNOOZE" -> {
                AlarmMission(context).finish("SNOOZED")
                context.stopService(Intent(context,AlarmSoundService::class.java))
                runCatching { AlarmScheduler(context).snooze(intent.getIntExtra("id",1)) }
            }
            else -> AlarmScheduler(context).reschedule()
        }
    }
}
