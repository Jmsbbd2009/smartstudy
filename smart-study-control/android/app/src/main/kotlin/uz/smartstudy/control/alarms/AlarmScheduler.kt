package uz.smartstudy.control.alarms
import android.app.*
import android.content.*
import android.os.Build
import uz.smartstudy.domain.AlarmTimes
import java.time.*
import org.json.JSONArray
import org.json.JSONObject

data class LocalAlarm(val id:Int,val hour:Int,val minute:Int,val days:Set<Int>,val enabled:Boolean=true,val photo:Boolean=false,val objects:Set<String> = setOf("book","bottle"))
class AlarmScheduler(private val context:Context) {
    private val prefs=context.getSharedPreferences("clock_alarms",Context.MODE_PRIVATE)
    private val manager=context.getSystemService(AlarmManager::class.java)
    fun alarms():List<LocalAlarm> = runCatching {
        val values=JSONArray(prefs.getString("alarms","[]"))
        (0 until values.length()).map { i -> val v=values.getJSONObject(i);val d=v.getJSONArray("days");LocalAlarm(v.getInt("id"),v.getInt("hour"),v.getInt("minute"),(0 until d.length()).map { d.getInt(it) }.toSet(),v.getBoolean("enabled"),v.optBoolean("photo",false),v.optJSONArray("objects")?.let { o -> (0 until o.length()).map {o.getString(it)}.toSet() } ?: setOf("book","bottle")) }
    }.getOrDefault(emptyList())
    fun save(alarm:LocalAlarm):Boolean {
        val all=alarms().filter { it.id!=alarm.id }+alarm
        persist(all)
        return schedule(alarm)
    }
    fun remove(id:Int) { persist(alarms().filter { it.id!=id });manager.cancel(operation(id)) }
    private fun persist(alarms:List<LocalAlarm>) {
        val array=JSONArray()
        alarms.forEach { a -> array.put(JSONObject().put("id",a.id).put("hour",a.hour).put("minute",a.minute).put("days",JSONArray(a.days.toList())).put("enabled",a.enabled).put("photo",a.photo).put("objects",JSONArray(a.objects.toList()))) }
        check(prefs.edit().putString("alarms",array.toString()).commit())
    }
    fun reschedule()=alarms().forEach { schedule(it) }
    fun canExact()=Build.VERSION.SDK_INT<31 || manager.canScheduleExactAlarms()
    fun schedule(alarm:LocalAlarm):Boolean {
        if(!alarm.enabled) { manager.cancel(operation(alarm.id));return true }
        val target=AlarmTimes.next(alarm.hour,alarm.minute,alarm.days,Instant.now(),ZoneId.systemDefault()).toEpochMilli()
        return try {
            if(canExact()) manager.setAlarmClock(AlarmManager.AlarmClockInfo(target,PendingIntent.getActivity(context,alarm.id,Intent(context,uz.smartstudy.control.MainActivity::class.java),PendingIntent.FLAG_IMMUTABLE)),operation(alarm.id))
            else manager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP,target,operation(alarm.id))
            canExact()
        } catch(e:SecurityException) {
            manager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP,target,operation(alarm.id));false
        }
    }
    fun snooze(id:Int) {
        val time=System.currentTimeMillis()+5*60_000L
        if(canExact()) manager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP,time,operation(id))
        else manager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP,time,operation(id))
    }
    private fun operation(id:Int)=PendingIntent.getBroadcast(context,id,Intent(context,StudyAlarmReceiver::class.java).setAction("uz.smartstudy.RING").putExtra("id",id),PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
}
