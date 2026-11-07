package uz.smartstudy.control
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import uz.smartstudy.data.*
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.serialization.json.*
import retrofit2.HttpException

data class StudyState(val authenticated:Boolean=false,val busy:Boolean=false,val error:Boolean=false,val notice:Int?=null,val assignments:List<JsonObject> = emptyList(),val queued:Int=0)
@HiltViewModel class StudyViewModel @Inject constructor(val repository:StudyData):ViewModel() {
    private val mutable=MutableStateFlow(StudyState(authenticated=repository.vault.token()!=null))
    val state=mutable.asStateFlow()
    private var observation:Job?=null
    init { if(mutable.value.authenticated) observe() }
    val user get()=repository.vault.read()?.get("user")?.jsonObject
    private fun observe() {
        observation?.cancel()
        observation=viewModelScope.launch {
            launch { repository.assignments().collect { rows -> mutable.update { it.copy(assignments=rows) } } }
            launch { repository.pendingCount().collect { count -> mutable.update { it.copy(queued=count) } } }
        }
    }
    fun run(block:suspend ()->Unit) { viewModelScope.launch {
        mutable.update { it.copy(busy=true,error=false,notice=null) }
        try { block() } catch(e:CancellationException) { throw e } catch(e:Exception) { mutable.update { it.copy(error=true) } }
        finally { mutable.update { it.copy(busy=false) } }
    } }
    fun auth(email:String,password:String,name:String?,parent:Boolean) = run {
        val data=buildJsonObject { if(name!=null) put("phone",email) else put("email",email);put("password",password);if(name!=null) {put("name",name);put("role",if(parent) "PARENT" else "STUDENT")} }
        val response=repository.api.post(if(name==null) "auth/login" else "auth/register",data)
        acceptSession(response)
    }
    suspend fun acceptSession(response:JsonObject) {
        repository.vault.save(response);mutable.value=StudyState(authenticated=true);observe()
        if(response["user"]?.jsonObject?.get("must_change_password")?.jsonPrimitive?.booleanOrNull!=true)repository.refreshAssignments()
    }
    fun logout()=run {
        repository.vault.read()?.get("refresh_token")?.let { token -> runCatching { repository.api.post("auth/logout",buildJsonObject { put("refresh_token",token) }) } }
        observation?.cancel();repository.vault.clear();mutable.value=StudyState()
    }
    fun refresh()=run { repository.flush();repository.refreshAssignments();mutable.update { it.copy(notice=R.string.success) } }
    fun submit(id:String,text:String)=run {
        repository.queueSubmission(id,text)
        runCatching { repository.flush();repository.refreshAssignments() }
        mutable.update { it.copy(notice=R.string.queued) }
    }
}
fun JsonObject.text(key:String)=this[key]?.jsonPrimitive?.contentOrNull.orEmpty()
fun body(vararg pairs:Pair<String,String>)=buildJsonObject { pairs.forEach { (k,v)->put(k,v) } }
