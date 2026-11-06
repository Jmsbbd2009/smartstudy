package uz.smartstudy.control
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.test.*
import kotlinx.serialization.json.*
import org.junit.*
import org.junit.Assert.*
import uz.smartstudy.data.*
@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
class StudyViewModelTest {
    private val dispatcher=StandardTestDispatcher()
    @Before fun setup(){Dispatchers.setMain(dispatcher)}
    @After fun cleanup(){Dispatchers.resetMain()}
    private class MemoryCredentials:Credentials {
        var value:JsonObject?=null
        override fun read()=value
        override fun save(value:JsonObject){this.value=value}
        override fun clear(){value=null}
        override fun token()=value?.get("access_token")?.jsonPrimitive?.content
        override fun userId()="test-user"
    }
    private class FakeData(val fail:Boolean):StudyData {
        override val vault=MemoryCredentials()
        var refreshed=false
        override val api=object:StudyApi {
            override suspend fun list(path:String)=emptyList<JsonObject>()
            override suspend fun get(path:String)=buildJsonObject {}
            override suspend fun post(path:String,body:JsonObject,key:String?):JsonObject {
                if(fail)throw java.io.IOException("Offline")
                return buildJsonObject {put("access_token","test-access");put("refresh_token","test-refresh");put("user",buildJsonObject {put("id","test-user")})}
            }
            override suspend fun put(path:String,body:JsonObject)=buildJsonObject {}
            override suspend fun delete(path:String)=buildJsonObject {}
            override suspend fun upload(path:String,file:okhttp3.MultipartBody.Part)=buildJsonObject {}
        }
        override suspend fun learning(key:String):String?=null
        override suspend fun cacheLearning(key:String,document:String){}
        override fun assignments()=flowOf(emptyList<JsonObject>())
        override fun pendingCount()=flowOf(0)
        override suspend fun refreshAssignments(){refreshed=true}
        override suspend fun queueSubmission(id:String,text:String)="test-id"
        override suspend fun flush()=0
        override suspend fun pending()=emptyList<Outbox>()
        override suspend fun discard(key:String){}
    }
    @Test fun failedLoginNeverAuthenticatesOrLeavesBusyState()=runTest(dispatcher) {
        val data=FakeData(true);val vm=StudyViewModel(data)
        vm.auth("ali@example.test","not-a-real-password",null,false)
        advanceUntilIdle()
        assertFalse(vm.state.value.authenticated);assertTrue(vm.state.value.error);assertFalse(vm.state.value.busy)
        assertNull(data.vault.read());assertFalse(data.refreshed)
    }
    @Test fun successfulLoginPersistsCredentialsAndLoadsCache()=runTest(dispatcher) {
        val data=FakeData(false);val vm=StudyViewModel(data)
        vm.auth("ali@example.test","not-a-real-password",null,false)
        advanceUntilIdle()
        assertTrue(vm.state.value.authenticated);assertFalse(vm.state.value.error)
        assertEquals("test-access",data.vault.token());assertTrue(data.refreshed)
    }
}
