package uz.smartstudy.domain
import org.junit.Assert.*
import org.junit.Test
import java.time.Instant
import java.time.ZoneId
class PolicyTest {
    private val now = Instant.parse("2026-10-30T17:00:00Z")
    @Test fun essentialAlwaysWins() {
        val p = Policy(blocked_packages=listOf("phone"), safety_packages=listOf("phone"), default_blocked=true)
        assertEquals(PolicyReason.ESSENTIAL, PolicyEngine.decide(p,"phone",now,setOf("phone"),false))
    }
    @Test fun precedenceSafetyOverrideSleepStudyRewardDefault() {
        val w=TimeWindow(listOf(5),1260,420)
        val p=Policy(blocked_packages=listOf("game"),safety_packages=listOf("game"),sleep=listOf(w),study=listOf(w),default_blocked=true,override_until="2026-10-31T00:00:00Z")
        fun result(q:Policy,earned:Boolean=true)=PolicyEngine.decide(q,"game",now,emptySet(),earned)
        assertEquals(PolicyReason.SAFETY,result(p))
        assertEquals(PolicyReason.OVERRIDE,result(p.copy(safety_packages=emptyList())))
        val q=p.copy(safety_packages=emptyList(),override_until=null)
        assertEquals(PolicyReason.SLEEP,result(q))
        assertEquals(PolicyReason.STUDY,result(q.copy(sleep=emptyList())))
        assertEquals(PolicyReason.EARNED,result(q.copy(sleep=emptyList(),study=emptyList())))
        assertEquals(PolicyReason.DEFAULT_BLOCK,result(q.copy(sleep=emptyList(),study=emptyList()),false))
    }
    @Test fun midnightUsesPreviousDay() {
        val p=Policy(blocked_packages=listOf("game"),sleep=listOf(TimeWindow(listOf(5),1260,420)))
        assertEquals(PolicyReason.SLEEP,PolicyEngine.decide(p,"game",Instant.parse("2026-10-30T23:00:00Z"),emptySet(),true))
        assertEquals(PolicyReason.EARNED,PolicyEngine.decide(p,"game",Instant.parse("2026-10-31T02:00:00Z"),emptySet(),true))
    }
    @Test fun localFocusBeatsEarnedButParentOverrideStillWins() {
        val p=Policy(blocked_packages=listOf("game"))
        assertEquals(PolicyReason.STUDY,PolicyEngine.decide(p,"game",now,emptySet(),true,true))
        assertEquals(PolicyReason.OVERRIDE,PolicyEngine.decide(p.copy(override_until="2026-10-31T00:00:00Z"),"game",now,emptySet(),true,true))
    }
    @Test fun wallClockChangeCannotExtendElapsedLease() {
        val lease=AccessLease("game",3000,9)
        assertTrue(lease.active(2999,9));assertFalse(lease.active(3000,9));assertFalse(lease.active(10,10));assertFalse(AccessLease("game",3000,-1).active(10,-1))
    }
    @Test fun alarmCrossesWeekendAndDstGap() {
        val zone=ZoneId.of("Europe/Berlin")
        val next=AlarmTimes.next(2,30,setOf(7),Instant.parse("2026-03-28T15:00:00Z"),zone)
        assertEquals(Instant.parse("2026-03-29T01:30:00Z"),next)
    }
}
