package uz.smartstudy.sync
import android.Manifest
import android.app.*
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import kotlinx.serialization.json.*
import uz.smartstudy.data.StudyData

object NotificationSync {
    suspend fun refresh(context:Context,repository:StudyData) {
        if(Build.VERSION.SDK_INT>=33 && ContextCompat.checkSelfPermission(context,Manifest.permission.POST_NOTIFICATIONS)!=PackageManager.PERMISSION_GRANTED)return
        val user=repository.vault.userId();if(user.isBlank())return
        val notes=repository.api.list("notifications")
        if(repository.vault.userId()!=user)return
        val manager=context.getSystemService(NotificationManager::class.java)
        manager.createNotificationChannel(NotificationChannel("study_messages",context.getString(R.string.study_notifications),NotificationManager.IMPORTANCE_DEFAULT))
        val prefs=context.getSharedPreferences("message_notifications",Context.MODE_PRIVATE)
        if(prefs.getString("user",null)!=user)clear(context)
        val known=prefs.getStringSet("known",emptySet())!!.toMutableSet()
        notes.filter {it["read"]?.jsonPrimitive?.booleanOrNull!=true}.take(10).forEach {note->
            val id=note["id"]!!.jsonPrimitive.content
            if(known.add(id)) {
                val launch=context.packageManager.getLaunchIntentForPackage(context.packageName)
                val open=launch?.let {PendingIntent.getActivity(context,6001,it,PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT)}
                val notification=NotificationCompat.Builder(context,"study_messages").setSmallIcon(android.R.drawable.ic_dialog_info)
                    .setContentTitle(note["title"]?.jsonPrimitive?.content?.take(150)).setContentText(note["body"]?.jsonPrimitive?.content?.take(1000))
                    .setContentIntent(open).setAutoCancel(true).setVisibility(NotificationCompat.VISIBILITY_PRIVATE).build()
                manager.notify(100_000+(id.hashCode() and 0x7fffffff)%10000,notification)
            }
        }
        prefs.edit().putString("user",user).putStringSet("known",known.takeLastSafe(100)).apply()
    }
    private fun Set<String>.takeLastSafe(n:Int)=toList().takeLast(n).toSet()
    fun clear(context:Context) {
        val prefs=context.getSharedPreferences("message_notifications",Context.MODE_PRIVATE)
        val manager=context.getSystemService(NotificationManager::class.java)
        prefs.getStringSet("known",emptySet())!!.forEach {id->manager.cancel(100_000+(id.hashCode() and 0x7fffffff)%10000)}
        prefs.edit().clear().apply()
    }
}
