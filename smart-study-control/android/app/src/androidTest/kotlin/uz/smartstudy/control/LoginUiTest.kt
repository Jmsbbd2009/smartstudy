package uz.smartstudy.control
import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import org.junit.Rule
import org.junit.Test
class LoginUiTest {
    @get:Rule val compose=createAndroidComposeRule<MainActivity>()
    @Test fun emptyCredentialsCannotBeSubmitted() {
        val label=compose.activity.getString(R.string.sign_in)
        compose.onNodeWithText(label).assertIsDisplayed().assertIsNotEnabled()
        compose.onNodeWithText(compose.activity.getString(R.string.register)).performClick()
        compose.onNodeWithText(compose.activity.getString(R.string.name)).assertIsDisplayed()
    }
}
