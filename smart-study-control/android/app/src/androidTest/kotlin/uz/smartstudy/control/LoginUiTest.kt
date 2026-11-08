package uz.smartstudy.control
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import org.junit.Rule
import org.junit.Test
class LoginUiTest {
    @get:Rule val compose=createAndroidComposeRule<MainActivity>()
    @Test fun emptyCredentialsCannotBeSubmitted() {
        compose.mainClock.advanceTimeBy(2000)
        compose.onNodeWithText(compose.activity.getString(R.string.login_with_password)).performScrollTo().performClick()
        compose.onNodeWithText(compose.activity.getString(R.string.sign_in)).performScrollTo().assertIsNotEnabled()
        compose.onNodeWithText(compose.activity.getString(R.string.student_register)).performScrollTo().performClick()
        compose.onNodeWithText(compose.activity.getString(R.string.name)).assertExists()
    }
}
