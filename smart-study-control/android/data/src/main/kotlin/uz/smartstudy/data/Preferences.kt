package uz.smartstudy.data
import android.content.Context
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.map
private val Context.studyPreferences by preferencesDataStore("study_preferences")
@Singleton class StudyPreferences @Inject constructor(@ApplicationContext private val context:Context) {
    val reducedMotion=context.studyPreferences.data.map { it[booleanPreferencesKey("reduced_motion")] ?: false }
    suspend fun setReducedMotion(value:Boolean) { context.studyPreferences.edit { it[booleanPreferencesKey("reduced_motion")]=value } }
}
