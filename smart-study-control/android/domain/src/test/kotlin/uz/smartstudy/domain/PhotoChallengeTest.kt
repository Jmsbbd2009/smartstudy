package uz.smartstudy.domain
import org.junit.Assert.*
import org.junit.Test
class PhotoChallengeTest {
    @Test fun unrelatedOrUncertainPhotoDoesNotCompleteAlarm(){
        assertFalse(PhotoChallenge.matches("book",listOf("Bottle" to 0.99f)))
        assertFalse(PhotoChallenge.matches("book",listOf("Book" to 0.79f)))
        assertFalse(PhotoChallenge.matches("book",listOf("Book" to Float.NaN)))
    }
    @Test fun configuredSafeObjectAndConfidentMatchCompleteTask(){
        assertEquals(setOf("book"),PhotoChallenge.eligible(setOf("book","knife","medicine")))
        assertTrue(PhotoChallenge.matches("bottle",listOf("Bottle" to 0.93f)))
    }
}
