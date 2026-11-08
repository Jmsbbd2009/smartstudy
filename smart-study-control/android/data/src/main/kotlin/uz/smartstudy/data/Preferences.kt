package uz.smartstudy.data
import android.content.Context
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.map
private val Context.studyPreferences by preferencesDataStore("study_preferences")
data class ProfileAppearance(val theme:String="sun",val sticker:String="⚡")
@Singleton class StudyPreferences @Inject constructor(@ApplicationContext private val context:Context) {
    fun appearance(user:String)=context.studyPreferences.data.map {
        ProfileAppearance(it[stringPreferencesKey("theme_$user")] ?: "sun", it[stringPreferencesKey("sticker_$user")] ?: "⚡")
    }
    suspend fun setAppearance(user:String,theme:String,sticker:String) {
        require(theme in listOf("sun","navy","blue","mint","violet","ruby","rose","graphite"))
        require(sticker in listOf("⚡","🎓","🚀","👑","📚","🏆","🔥","⭐"))
        context.studyPreferences.edit {
            it[stringPreferencesKey("theme_$user")]=theme
            it[stringPreferencesKey("sticker_$user")]=sticker
        }
    }
    val reducedMotion=context.studyPreferences.data.map { it[booleanPreferencesKey("reduced_motion")] ?: false }
    suspend fun setReducedMotion(value:Boolean) { context.studyPreferences.edit { it[booleanPreferencesKey("reduced_motion")]=value } }
}
