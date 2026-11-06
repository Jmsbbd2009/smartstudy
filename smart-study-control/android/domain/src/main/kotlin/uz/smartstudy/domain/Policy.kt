package uz.smartstudy.domain

import kotlinx.serialization.Serializable
import java.time.Instant
import java.time.ZoneId
import java.time.ZonedDateTime

@Serializable
data class TimeWindow(val days: List<Int>, val start_minute: Int, val end_minute: Int) {
    fun active(local: ZonedDateTime): Boolean {
        val minute = local.hour * 60 + local.minute
        val today = local.dayOfWeek.value
        return if (start_minute < end_minute) today in days && minute in start_minute until end_minute
        else (today in days && minute >= start_minute) || (((today + 5) % 7 + 1) in days && minute < end_minute)
    }
}
@Serializable
data class Policy(
    val blocked_packages: List<String> = emptyList(),
    val essential_packages: List<String> = emptyList(),
    val safety_packages: List<String> = emptyList(),
    val study: List<TimeWindow> = emptyList(),
    val sleep: List<TimeWindow> = emptyList(),
    val timezone: String = "Asia/Tashkent",
    val default_blocked: Boolean = false,
    val uninstall_protection: Boolean = false,
    val override_until: String? = null
)
enum class PolicyReason(val blocked: Boolean) {
    ESSENTIAL(false), SAFETY(true), OVERRIDE(false), SLEEP(true), STUDY(true), EARNED(false), DEFAULT_BLOCK(true), ALLOW(false)
}
object PolicyEngine {
    fun decide(policy: Policy, pkg: String, now: Instant, protected: Set<String>, earned: Boolean, focusActive: Boolean = false): PolicyReason {
        if (pkg in protected || pkg in policy.essential_packages) return PolicyReason.ESSENTIAL
        if (pkg in policy.safety_packages) return PolicyReason.SAFETY
        if (policy.override_until?.let { runCatching { now < Instant.parse(it) }.getOrDefault(false) } == true) return PolicyReason.OVERRIDE
        if (pkg !in policy.blocked_packages) return PolicyReason.ALLOW
        val local = now.atZone(ZoneId.of(policy.timezone))
        if (policy.sleep.any { it.active(local) }) return PolicyReason.SLEEP
        if (policy.study.any { it.active(local) }) return PolicyReason.STUDY
        if (focusActive) return PolicyReason.STUDY
        if (earned) return PolicyReason.EARNED
        return if (policy.default_blocked) PolicyReason.DEFAULT_BLOCK else PolicyReason.ALLOW
    }
}
@Serializable
data class AccessLease(val packageName: String, val deadlineElapsed: Long, val bootId: Int) {
    fun active(elapsed: Long, currentBoot: Int) = bootId >= 0 && bootId == currentBoot && elapsed < deadlineElapsed && elapsed >= 0
}
object AlarmTimes {
    fun next(hour: Int, minute: Int, weekdays: Set<Int>, after: Instant, zone: ZoneId): Instant {
        require(hour in 0..23 && minute in 0..59 && weekdays.isNotEmpty() && weekdays.all { it in 1..7 })
        val today = after.atZone(zone).toLocalDate()
        return (0..7).map { today.plusDays(it.toLong()).atTime(hour, minute).atZone(zone) }
            .first { it.dayOfWeek.value in weekdays && it.toInstant() > after }.toInstant()
    }
}
