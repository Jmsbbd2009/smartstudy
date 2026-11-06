package uz.smartstudy.data
import kotlinx.serialization.json.JsonObject
import okhttp3.MultipartBody
import retrofit2.http.*
interface StudyApi {
    @GET suspend fun list(@Url path:String): List<JsonObject>
    @GET suspend fun get(@Url path:String): JsonObject
    @POST suspend fun post(@Url path:String,@Body body:JsonObject,@Header("Idempotency-Key") key:String?=null): JsonObject
    @PUT suspend fun put(@Url path:String,@Body body:JsonObject): JsonObject
    @DELETE suspend fun delete(@Url path:String): JsonObject
    @Multipart @POST suspend fun upload(@Url path:String,@Part file:MultipartBody.Part):JsonObject
}
