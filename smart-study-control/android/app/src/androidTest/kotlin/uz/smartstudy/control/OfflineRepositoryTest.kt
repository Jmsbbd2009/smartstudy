package uz.smartstudy.control
import androidx.test.core.app.ApplicationProvider
import androidx.room.Room
import android.content.Context
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.*
import org.junit.Test
import org.junit.Assert.*
import uz.smartstudy.data.*
import java.io.IOException
class OfflineRepositoryTest {
    @Test fun networkFailureKeepsOriginalIdempotencyKeyUntilSuccessfulRetry()=runBlocking {
        val context=ApplicationProvider.getApplicationContext<Context>()
        val database=Room.inMemoryDatabaseBuilder(context,StudyDatabase::class.java).build()
        val vault=TokenVault(context)
        vault.save(buildJsonObject {put("access_token","instrumentation-test");put("user",buildJsonObject {put("id","student-test")})})
        val sent=mutableListOf<String?>();var fail=true
        val api=object:StudyApi {
            override suspend fun list(path:String)=emptyList<JsonObject>()
            override suspend fun get(path:String)=buildJsonObject {}
            override suspend fun post(path:String,body:JsonObject,key:String?):JsonObject {sent.add(key);if(fail)throw IOException("offline");return buildJsonObject {put("id","accepted")}}
            override suspend fun put(path:String,body:JsonObject)=buildJsonObject {}
            override suspend fun delete(path:String)=buildJsonObject {}
            override suspend fun upload(path:String,file:okhttp3.MultipartBody.Part)=buildJsonObject {}
        }
        try {
            val repository=StudyRepository(api,vault,database)
            val key=repository.queueSubmission("00000000-0000-0000-0000-000000000001","1/2+1/4=3/4")
            assertTrue(runCatching {repository.flush()}.isFailure)
            assertEquals(key,repository.pending().single().key)
            fail=false
            assertEquals(1,repository.flush())
            assertTrue(repository.pending().isEmpty())
            assertEquals(listOf(key,key),sent)
        } finally {vault.clear();database.close()}
    }
}
