package uz.smartstudy.data
import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import kotlinx.serialization.json.*
import javax.inject.Inject
import javax.inject.Singleton
import dagger.hilt.android.qualifiers.ApplicationContext
@Singleton class TokenVault @Inject constructor(@ApplicationContext context:Context):Credentials {
    private val preferences=context.getSharedPreferences("credentials",Context.MODE_PRIVATE)
    private val key: SecretKey get() {
        val store=KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (store.getKey("study.tokens",null) as? SecretKey)?.let { return it }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES,"AndroidKeyStore").apply {
            init(KeyGenParameterSpec.Builder("study.tokens",KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT).setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build())
        }.generateKey()
    }
    @Synchronized override fun read(): JsonObject? = runCatching {
        val raw=preferences.getString("encrypted",null) ?: return null
        val pieces=raw.split(":")
        val cipher=Cipher.getInstance("AES/GCM/NoPadding").apply { init(Cipher.DECRYPT_MODE,key,GCMParameterSpec(128,Base64.decode(pieces[0],Base64.NO_WRAP))) }
        Json.parseToJsonElement(String(cipher.doFinal(Base64.decode(pieces[1],Base64.NO_WRAP)),Charsets.UTF_8)).jsonObject
    }.getOrNull()
    @Synchronized override fun save(value:JsonObject) {
        val cipher=Cipher.getInstance("AES/GCM/NoPadding").apply { init(Cipher.ENCRYPT_MODE,key) }
        val encrypted=cipher.doFinal(value.toString().toByteArray(Charsets.UTF_8))
        check(preferences.edit().putString("encrypted",Base64.encodeToString(cipher.iv,Base64.NO_WRAP)+":"+Base64.encodeToString(encrypted,Base64.NO_WRAP)).commit())
    }
    @Synchronized override fun clear(){ preferences.edit().clear().commit() }
    override fun token()=read()?.get("access_token")?.jsonPrimitive?.content
    override fun userId()=read()?.get("user")?.jsonObject?.get("id")?.jsonPrimitive?.content.orEmpty()
}
