package uz.smartstudy.devicepolicy

import android.app.admin.DevicePolicyManager
import android.app.AlarmManager
import android.app.PendingIntent
import android.content.*
import android.content.pm.ApplicationInfo
import android.os.Build
import android.os.SystemClock
import android.provider.Settings
import android.telecom.TelecomManager
import android.view.inputmethod.InputMethodManager
import android.view.accessibility.AccessibilityManager
import uz.smartstudy.domain.*
import java.time.Instant

interface PackageControl {
    val managed: Boolean
    fun suspendPackage(pkg: String, suspend: Boolean): Boolean
}
class DeviceController(private val context: Context): PackageControl {
    private val dpm=context.getSystemService(DevicePolicyManager::class.java)
    private val admin=ComponentName(context,StudyAdminReceiver::class.java)
    override val managed get()=dpm?.isDeviceOwnerApp(context.packageName)==true
    override fun suspendPackage(pkg:String,suspend:Boolean): Boolean {
        if(!managed) return false
        if(suspend && pkg in protectedPackages()) return false
        if(suspend && runCatching { context.packageManager.getApplicationInfo(pkg,0).flags and ApplicationInfo.FLAG_SYSTEM != 0 }.getOrDefault(true)) return false
        return runCatching {
            val failed=dpm.setPackagesSuspended(admin,arrayOf(pkg),suspend)
            failed.isEmpty() && dpm.isPackageSuspended(admin,pkg)==suspend
        }.getOrDefault(false)
    }
    fun uninstallProtected():Boolean = managed && runCatching { dpm.isUninstallBlocked(admin,context.packageName) }.getOrDefault(false)
    fun protectUninstall(pkg:String,enabled:Boolean): Boolean {
        if(!managed) return false
        return runCatching { dpm.setUninstallBlocked(admin,pkg,enabled); dpm.isUninstallBlocked(admin,pkg)==enabled }.getOrDefault(false)
    }
    @Suppress("DEPRECATION")
    fun visibleApps(): List<Pair<String,String>> = context.packageManager.queryIntentActivities(
        Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER),0
    ).map { it.activityInfo.packageName to it.loadLabel(context.packageManager).toString() }.distinctBy { it.first }.sortedBy { it.second }
    @Suppress("DEPRECATION")
    fun protectedPackages(): Set<String> {
        val pm=context.packageManager
        val protected=mutableSetOf(context.packageName,"com.android.settings","com.android.systemui","com.android.phone","com.android.server.telecom")
        // Conservative baseline: never suspend a visible system app.
        visibleApps().forEach { (pkg,_) -> runCatching { if(pm.getApplicationInfo(pkg,0).flags and ApplicationInfo.FLAG_SYSTEM != 0) protected.add(pkg) } }
        pm.resolveActivity(Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_HOME),0)?.activityInfo?.packageName?.let(protected::add)
        context.getSystemService(TelecomManager::class.java)?.defaultDialerPackage?.let(protected::add)
        android.provider.Telephony.Sms.getDefaultSmsPackage(context)?.let(protected::add)
        context.getSystemService(InputMethodManager::class.java)?.enabledInputMethodList?.forEach { protected.add(it.packageName) }
        context.getSystemService(AccessibilityManager::class.java)?.getEnabledAccessibilityServiceList(-1)?.forEach { protected.add(it.resolveInfo.serviceInfo.packageName) }
        return protected
    }
}
class PolicyStore(context:Context) {
    private val prefs=context.getSharedPreferences("managed_policy",Context.MODE_PRIVATE)
    var policy: String
        get()=prefs.getString("document","{}")!!
        set(value) { prefs.edit().putString("document",value).commit() }
    var version: Int
        get()=prefs.getInt("version",0)
        set(value) { prefs.edit().putInt("version",value).commit() }
    var deviceId: String
        get()=prefs.getString("device","")!!
        set(value) { prefs.edit().putString("device",value).commit() }
    var managedPackages: Set<String>
        get()=prefs.getStringSet("packages",emptySet())!!.toSet()
        set(value) { prefs.edit().putStringSet("packages",value).commit() }
    var uninstallPackages: Set<String>
        get()=prefs.getStringSet("uninstall",emptySet())!!.toSet()
        set(value) { prefs.edit().putStringSet("uninstall",value).commit() }
    var leasePackage: String
        get()=prefs.getString("leasePackage","")!!
        set(value) { prefs.edit().putString("leasePackage",value).commit() }
    var leaseDeadline: Long
        get()=prefs.getLong("leaseDeadline",0)
        set(value) { prefs.edit().putLong("leaseDeadline",value).commit() }
    var leaseBoot: Int
        get()=prefs.getInt("leaseBoot",-1)
        set(value) { prefs.edit().putInt("leaseBoot",value).commit() }
    fun leaseActive(context:Context,pkg:String)=leasePackage==pkg && AccessLease(pkg,leaseDeadline,leaseBoot).active(SystemClock.elapsedRealtime(),boot(context))
    var focusDeadline: Long
        get()=prefs.getLong("focusDeadline",0)
        set(value) { prefs.edit().putLong("focusDeadline",value).commit() }
    var focusBoot: Int
        get()=prefs.getInt("focusBoot",-1)
        set(value) { prefs.edit().putInt("focusBoot",value).commit() }
    fun focusActive(context:Context)=focusBoot==boot(context) && SystemClock.elapsedRealtime()<focusDeadline
    fun clearLease(){ leaseDeadline=0;leasePackage="";leaseBoot=-1 }
    companion object { fun boot(context:Context)=runCatching { Settings.Global.getInt(context.contentResolver,Settings.Global.BOOT_COUNT,-1) }.getOrDefault(-1) }
}
object PolicyEnforcer {
    fun apply(context:Context,policy:Policy):List<String> {
        val store=PolicyStore(context);val controller=DeviceController(context)
        if(!controller.managed) return emptyList() // Explicit voluntary mode, no fabricated OS enforcement.
        val failures=mutableListOf<String>()
        val candidates=store.managedPackages+policy.blocked_packages+policy.safety_packages
        val tracked=store.managedPackages.toMutableSet()
        candidates.forEach { pkg ->
            val block=PolicyEngine.decide(policy,pkg,Instant.now(),controller.protectedPackages(),store.leaseActive(context,pkg),store.focusActive(context)).blocked
            // Journal before OS mutation, so process death cannot strand an untracked suspension.
            if(block) { tracked.add(pkg);store.managedPackages=tracked }
            if(!controller.suspendPackage(pkg,block)) failures.add(pkg)
            else if(!block) { tracked.remove(pkg);store.managedPackages=tracked }
        }
        val desiredUninstall=if(policy.uninstall_protection) setOf(context.packageName) else emptySet()
        (store.uninstallPackages+desiredUninstall).forEach { pkg ->
            val enabled=pkg in desiredUninstall
            if(enabled) store.uninstallPackages=store.uninstallPackages+pkg
            if(!controller.protectUninstall(pkg,enabled)) failures.add("uninstall:$pkg")
            else if(!enabled) store.uninstallPackages=store.uninstallPackages-pkg
        }
        schedule(context,store)
        return failures
    }
    fun cleanup(context:Context):List<String> {
        val store=PolicyStore(context);val c=DeviceController(context);val failures=mutableListOf<String>()
        store.managedPackages.forEach { if(!c.suspendPackage(it,false)) failures.add(it) else store.managedPackages=store.managedPackages-it }
        store.uninstallPackages.forEach { if(!c.protectUninstall(it,false)) failures.add("uninstall:$it") else store.uninstallPackages=store.uninstallPackages-it }
        if(failures.isEmpty()) { store.policy="{}";store.clearLease() }
        return failures
    }
    private fun schedule(context:Context,store:PolicyStore) {
        val manager=context.getSystemService(AlarmManager::class.java)
        val operation=PendingIntent.getBroadcast(context,909,Intent(context,PolicyReceiver::class.java).setAction("uz.smartstudy.POLICY_TICK"),PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val elapsed=SystemClock.elapsedRealtime()
        val nextBoundary=elapsed+(60_000-System.currentTimeMillis()%60_000)
        val deadline=store.leaseDeadline.takeIf { it>elapsed } ?: Long.MAX_VALUE
        val target=minOf(nextBoundary,deadline)
        // Exact alarms are reserved for user-facing clock alarms. Policy ticks are best effort unless owner power exemptions allow exact scheduling.
        runCatching {
            manager.setAndAllowWhileIdle(AlarmManager.ELAPSED_REALTIME_WAKEUP,nextBoundary,operation)
            val expiry=PendingIntent.getBroadcast(context,910,Intent(context,PolicyReceiver::class.java).setAction("uz.smartstudy.LEASE_EXPIRED"),PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
            if(deadline!=Long.MAX_VALUE && (Build.VERSION.SDK_INT<31 || manager.canScheduleExactAlarms()))
                manager.setExactAndAllowWhileIdle(AlarmManager.ELAPSED_REALTIME_WAKEUP,deadline,expiry)
            else manager.cancel(expiry)
        }
    }
}
