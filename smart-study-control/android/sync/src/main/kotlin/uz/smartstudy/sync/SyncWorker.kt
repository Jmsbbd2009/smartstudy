package uz.smartstudy.sync
import android.content.Context
import android.os.SystemClock
import javax.inject.Inject
import androidx.work.*
import uz.smartstudy.data.*
import uz.smartstudy.devicepolicy.*
import uz.smartstudy.domain.Policy
import kotlinx.serialization.json.*
import java.time.Instant
import java.util.concurrent.TimeUnit
import kotlin.math.max

class SyncWorker(context:Context,params:WorkerParameters,private val repository:StudyRepository):CoroutineWorker(context,params) {
    override suspend fun doWork():Result {
        if(repository.vault.userId().isEmpty()) return Result.success()
        return try { repository.flush();repository.refreshAssignments();NotificationSync.refresh(applicationContext,repository);DeviceSync.sync(applicationContext,repository);Result.success() }
        catch(e:java.io.IOException) { Result.retry() }
        catch(e:retrofit2.HttpException) { if(e.code() in listOf(401,403,404,422)) Result.failure() else Result.retry() }
        catch(e:Exception) { Result.failure() }
    }
    companion object {
        fun schedule(context:Context) {
            val constraints=Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()
            WorkManager.getInstance(context).enqueueUniquePeriodicWork("study-sync",ExistingPeriodicWorkPolicy.KEEP,
                PeriodicWorkRequestBuilder<SyncWorker>(15,TimeUnit.MINUTES).setConstraints(constraints).build())
        }
        fun now(context:Context) {
            WorkManager.getInstance(context).enqueueUniqueWork("study-sync-now",ExistingWorkPolicy.KEEP,
                OneTimeWorkRequestBuilder<SyncWorker>().setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()).build())
        }
    }
}
object DeviceSync {
    private val json=Json { ignoreUnknownKeys=true }
    suspend fun sync(context:Context,repository:StudyData) {
        val store=PolicyStore(context)
        if(store.deviceId.isEmpty()) return
        val remote=repository.api.get("devices/${store.deviceId}/policies")
        val version=remote["version"]!!.jsonPrimitive.int
        if(version<store.version) error("Policy version rollback refused")
        if(remote["deprovision_requested"]?.jsonPrimitive?.boolean==true) {
            val failures=PolicyEnforcer.cleanup(context)
            repository.api.post("devices/${store.deviceId}/sync",buildJsonObject { put("applied_version",version);put("device_owner",DeviceController(context).managed);put("uninstall_blocked",DeviceController(context).uninstallProtected());put("cleanup_complete",failures.isEmpty());put("failures",JsonArray(failures.map(::JsonPrimitive))) })
            if(failures.isEmpty()) { store.version=0;store.deviceId="" }
            return
        }
        store.policy=remote["document"]!!.toString();store.version=version
        val p=json.decodeFromString<Policy>(store.policy)
        val failures=PolicyEnforcer.apply(context,p)
        repository.api.post("devices/${store.deviceId}/sync",buildJsonObject {
            put("applied_version",version);put("device_owner",DeviceController(context).managed);put("uninstall_blocked",DeviceController(context).uninstallProtected());put("failures",JsonArray(failures.map(::JsonPrimitive)))
            if(remote["management_authorized"]?.jsonPrimitive?.boolean==true) {
                val controller=DeviceController(context);val protected=controller.protectedPackages()
                put("eligible_apps",JsonArray(controller.visibleApps().filter {it.first !in protected}.take(100).map { (pkg,label)->buildJsonObject {put("package",pkg);put("label",label.take(120).ifBlank {pkg})} }))
            }
        })
        // Only restore a lease on the same boot. A server wall-clock value alone never extends a local lease.
        if(store.leaseBoot!=PolicyStore.boot(context)) store.clearLease()
    }
    suspend fun redeem(context:Context,repository:StudyData,pkg:String,minutes:Int) {
        val store=PolicyStore(context)
        check(store.deviceId.isNotEmpty()) { "Device registration required" }
        val controller=DeviceController(context)
        if(controller.managed && android.os.Build.VERSION.SDK_INT>=31)
            check(context.getSystemService(android.app.AlarmManager::class.java).canScheduleExactAlarms()) { "Exact alarm permission is required before managed timed access" }
        val started=SystemClock.elapsedRealtime()
        val lease=repository.api.post("rewards/redeem",buildJsonObject { put("device_id",store.deviceId);put("package",pkg);put("minutes",minutes) },java.util.UUID.randomUUID().toString())
        val id=lease["id"]!!.jsonPrimitive.content
        // In standard mode, this is a voluntary timed allowance and is labeled as such in UI.
        val applied=if(controller.managed) controller.suspendPackage(pkg,false) else true
        try {
            val ack=repository.api.post("rewards/sessions/$id/ack",buildJsonObject { put("applied",applied) })
            if(ack["status"]!!.jsonPrimitive.content=="ACTIVE") {
                store.leasePackage=pkg;store.leaseBoot=PolicyStore.boot(context);store.leaseDeadline=started+minutes*60_000L
                PolicyEnforcer.apply(context,json.decodeFromString<Policy>(store.policy))
            } else error("Unlock failed; reserved minutes were refunded")
        } catch(e:Exception) {
            // An unacknowledged unsuspension must not persist while offline.
            store.clearLease();PolicyEnforcer.apply(context,json.decodeFromString<Policy>(store.policy));throw e
        }
    }
}

class StudyWorkerFactory @Inject constructor(private val repository:StudyRepository):WorkerFactory() {
    override fun createWorker(appContext:Context,workerClassName:String,workerParameters:WorkerParameters):ListenableWorker? =
        when(workerClassName) {
            SyncWorker::class.java.name -> SyncWorker(appContext,workerParameters,repository)
            LocationStopWorker::class.java.name -> LocationStopWorker(appContext,workerParameters,repository)
            else -> null
        }
}
