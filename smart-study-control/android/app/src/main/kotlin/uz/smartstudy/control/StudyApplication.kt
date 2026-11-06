package uz.smartstudy.control
import android.app.Application
import androidx.work.Configuration
import uz.smartstudy.sync.StudyWorkerFactory
import dagger.hilt.android.HiltAndroidApp
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import uz.smartstudy.data.ApiBaseUrl
import javax.inject.Inject
@HiltAndroidApp class StudyApplication:Application(),Configuration.Provider {
    @Inject lateinit var workerFactory:StudyWorkerFactory
    override val workManagerConfiguration get()=Configuration.Builder().setWorkerFactory(workerFactory).build()
    override fun onCreate(){ super.onCreate();uz.smartstudy.sync.SyncWorker.schedule(this) }
}
@Module @InstallIn(SingletonComponent::class) object AppModule {
    @Provides @ApiBaseUrl fun baseUrl():String=BuildConfig.API_URL
}
