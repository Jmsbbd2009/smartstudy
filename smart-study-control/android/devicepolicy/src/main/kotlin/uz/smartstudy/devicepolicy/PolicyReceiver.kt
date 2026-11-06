package uz.smartstudy.devicepolicy
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import kotlinx.serialization.json.Json
import uz.smartstudy.domain.Policy
class PolicyReceiver:BroadcastReceiver() {
    override fun onReceive(context:Context,intent:Intent) {
        val store=PolicyStore(context)
        if(intent.action==Intent.ACTION_BOOT_COMPLETED) store.clearLease()
        runCatching { PolicyEnforcer.apply(context,Json { ignoreUnknownKeys=true }.decodeFromString<Policy>(store.policy)) }
    }
}
