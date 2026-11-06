package uz.smartstudy.sync
import android.content.Context
import androidx.work.*
import uz.smartstudy.data.StudyRepository
import kotlinx.serialization.json.buildJsonObject

class LocationStopWorker(context:Context,params:WorkerParameters,private val repository:StudyRepository):CoroutineWorker(context,params) {
    override suspend fun doWork():Result {
        val owner=inputData.getString("owner") ?: return Result.failure()
        val share=inputData.getString("share") ?: return Result.failure()
        if(runAttemptCount>12)return Result.failure()
        if(repository.vault.userId()!=owner)return Result.retry()
        return try {repository.api.post("location/shares/$share/stop",buildJsonObject {});Result.success()}
        catch(e:retrofit2.HttpException){if(e.code() in listOf(403,404))Result.success() else Result.retry()}
        catch(e:java.io.IOException){Result.retry()}
    }
    companion object {
        fun enqueue(context:Context,owner:String,share:String) {
            if(owner.isBlank() || share.isBlank())return
            WorkManager.getInstance(context).enqueueUniqueWork("stop-location-$share",ExistingWorkPolicy.KEEP,
                OneTimeWorkRequestBuilder<LocationStopWorker>().setInputData(workDataOf("owner" to owner,"share" to share))
                    .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build()).build())
        }
    }
}
