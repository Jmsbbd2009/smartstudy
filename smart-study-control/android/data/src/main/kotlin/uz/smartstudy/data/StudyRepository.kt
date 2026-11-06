package uz.smartstudy.data
import androidx.room.withTransaction
import kotlinx.coroutines.flow.map
import kotlinx.serialization.json.*
import retrofit2.HttpException
import java.io.IOException
import java.util.UUID
import javax.inject.Inject
import javax.inject.Singleton

@Singleton class StudyRepository @Inject constructor(override val api:StudyApi,override val vault:TokenVault,private val database:StudyDatabase):StudyData {
    private val dao get()=database.dao()
    override suspend fun learning(key:String)=dao.learning(vault.userId(),key)
    override suspend fun cacheLearning(key:String,document:String) {
        require(document.length<=2_000_000)
        dao.saveLearning(LearningCache(vault.userId(),key,document))
    }
    override fun assignments()=dao.assignments(vault.userId()).map { rows -> rows.map { Json.parseToJsonElement(it.document).jsonObject } }
    override fun pendingCount()=dao.pendingCount(vault.userId())
    suspend override fun refreshAssignments() {
        val user=vault.userId();val rows=api.list("assignments")
        check(vault.userId()==user) { "Account changed during synchronization" }
        database.withTransaction { dao.clearCache(user);dao.cache(rows.map { CachedAssignment(user,it["id"]!!.jsonPrimitive.content,it.toString()) }) }
    }
    suspend override fun queueSubmission(id:String,text:String):String {
        val key=UUID.randomUUID().toString()
        dao.enqueue(Outbox(key,vault.userId(),"assignments/$id/submit",buildJsonObject { put("text",text) }.toString()))
        return key
    }
    suspend override fun flush():Int {
        val user=vault.userId();var sent=0
        for(row in dao.pending(user)) {
            if(vault.userId()!=user) break
            if(row.error!=null) continue
            // Outbox is deliberately restricted to immutable assignment submissions.
            if(!Regex("assignments/[a-fA-F0-9-]{36}/submit").matches(row.path)) { dao.markError(row.key,user,"Invalid queued operation");continue }
            try {
                api.post(row.path,Json.parseToJsonElement(row.body).jsonObject,row.key)
                dao.remove(row.key,user);sent++
            } catch(e:HttpException) {
                if(e.code() in listOf(400,403,404,409,422)) dao.markError(row.key,user,"HTTP ${e.code()}; review required") else throw e
            }
        }
        return sent
    }
    suspend override fun pending()=dao.pending(vault.userId())
    suspend override fun discard(key:String)=dao.remove(key,vault.userId())
}
