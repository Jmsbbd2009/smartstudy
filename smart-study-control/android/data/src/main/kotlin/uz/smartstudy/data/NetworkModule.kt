package uz.smartstudy.data
import android.content.Context
import androidx.room.Room
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Singleton
import javax.inject.Qualifier
import kotlinx.serialization.json.*
import okhttp3.*
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.RequestBody.Companion.toRequestBody
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
@Qualifier @Retention(AnnotationRetention.BINARY) annotation class ApiBaseUrl
@Module @InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides fun studyData(repository:StudyRepository):StudyData=repository
    @Provides @Singleton fun database(@ApplicationContext context:Context):StudyDatabase = Room.databaseBuilder(context,StudyDatabase::class.java,"study.db").addMigrations(MIGRATION_1_2).build()
    @Provides @Singleton fun api(vault:TokenVault,@ApiBaseUrl baseUrl:String):StudyApi {
        val json=Json { ignoreUnknownKeys=true;explicitNulls=false }
        // The hosted free API can take over 50 seconds to wake from idle.
        val bare=OkHttpClient.Builder()
            .connectTimeout(java.time.Duration.ofSeconds(15))
            .readTimeout(java.time.Duration.ofSeconds(90))
            .writeTimeout(java.time.Duration.ofSeconds(90))
            .callTimeout(java.time.Duration.ofSeconds(120))
            .build()
        val client=bare.newBuilder().addInterceptor { chain ->
            val builder=chain.request().newBuilder()
            vault.token()?.let { builder.header("Authorization","Bearer $it") }
            chain.proceed(builder.build())
        }.authenticator { _,response ->
            if(response.priorResponse!=null || response.request.url.encodedPath.contains("auth/")) null
            else synchronized(vault) {
                val stored=vault.read()
                val current=stored?.get("access_token")?.jsonPrimitive?.content
                if(current!=null && response.request.header("Authorization")!="Bearer $current") {
                    response.request.newBuilder().header("Authorization","Bearer $current").build()
                } else {
                    val refresh=stored?.get("refresh_token")?.jsonPrimitive?.content
                    if(refresh==null) null else {
                        val payload=buildJsonObject { put("refresh_token",refresh) }
                        runCatching {
                            bare.newCall(Request.Builder().url(baseUrl+"auth/refresh").post(payload.toString().toRequestBody("application/json".toMediaType())).build()).execute().use { rotated ->
                                if(!rotated.isSuccessful) { if(rotated.code==401) vault.clear();null }
                                else {
                                    val data=json.parseToJsonElement(rotated.body!!.string()).jsonObject
                                    vault.save(data)
                                    response.request.newBuilder().header("Authorization","Bearer ${data["access_token"]!!.jsonPrimitive.content}").build()
                                }
                            }
                        }.getOrNull()
                    }
                }
            }
        }.build()
        return Retrofit.Builder().baseUrl(baseUrl).client(client).addConverterFactory(json.asConverterFactory("application/json".toMediaType())).build().create(StudyApi::class.java)
    }
}
