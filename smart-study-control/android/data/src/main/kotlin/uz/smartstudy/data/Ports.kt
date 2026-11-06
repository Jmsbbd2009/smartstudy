package uz.smartstudy.data
import kotlinx.coroutines.flow.Flow
import kotlinx.serialization.json.JsonObject
interface Credentials {
    fun read():JsonObject?
    fun save(value:JsonObject)
    fun clear()
    fun token():String?
    fun userId():String
}
interface StudyData {
    val api:StudyApi
    val vault:Credentials
    fun assignments():Flow<List<JsonObject>>
    fun pendingCount():Flow<Int>
    suspend fun learning(key:String):String?
    suspend fun cacheLearning(key:String,document:String)
    suspend fun refreshAssignments()
    suspend fun queueSubmission(id:String,text:String):String
    suspend fun flush():Int
    suspend fun pending():List<Outbox>
    suspend fun discard(key:String)
}
