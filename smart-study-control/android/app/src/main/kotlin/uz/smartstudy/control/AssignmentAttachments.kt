package uz.smartstudy.control

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.JsonObject
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import uz.smartstudy.data.StudyApi
import java.io.ByteArrayOutputStream

internal data class PickedAttachment(val uri: Uri, val name: String)

internal object AssignmentAttachments {
    const val MAX_BYTES = 10 * 1024 * 1024
    private val allowed = setOf("application/pdf", "image/jpeg", "image/png")
    fun withinLimit(size: Int) = size in 1..MAX_BYTES

    fun validSignature(type: String, bytes: ByteArray): Boolean = when (type) {
        "application/pdf" -> bytes.startsWith(byteArrayOf(0x25, 0x50, 0x44, 0x46, 0x2d))
        "image/jpeg" -> bytes.startsWith(byteArrayOf(0xff.toByte(), 0xd8.toByte(), 0xff.toByte()))
        "image/png" -> bytes.startsWith(byteArrayOf(0x89.toByte(), 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a))
        else -> false
    }

    private fun ByteArray.startsWith(prefix: ByteArray) = size >= prefix.size && prefix.indices.all { this[it] == prefix[it] }

    fun mediaType(context: Context, uri: Uri): String? =
        context.contentResolver.getType(uri)?.substringBefore(';')?.lowercase()
            ?.let { if (it == "image/jpg") "image/jpeg" else it }
            ?.takeIf(allowed::contains)

    fun displayName(context: Context, uri: Uri): String {
        val raw = runCatching {
            context.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)
                ?.use { cursor -> if (cursor.moveToFirst()) cursor.getString(0) else null }
        }.getOrNull().orEmpty().ifBlank { "attachment" }
        return raw.substringAfterLast('/').substringAfterLast('\\')
            .replace(Regex("[\\r\\n\\u0000]"), "_").take(180).ifBlank { "attachment" }
    }

    suspend fun upload(context: Context, api: StudyApi, assignmentId: String, item: PickedAttachment): JsonObject =
        withContext(Dispatchers.IO) {
            val type = requireNotNull(mediaType(context, item.uri)) { "Choose a PDF, JPEG, or PNG file" }
            val stream = requireNotNull(context.contentResolver.openInputStream(item.uri)) { "The selected file cannot be read" }
            val output = ByteArrayOutputStream()
            stream.use { input ->
                val buffer = ByteArray(16 * 1024)
                while (true) {
                    val count = input.read(buffer)
                    if (count < 0) break
                    require(output.size() + count <= MAX_BYTES) { "Attachments must be 10 MiB or smaller" }
                    output.write(buffer, 0, count)
                }
            }
            val bytes = output.toByteArray()
            require(withinLimit(bytes.size)) { "The selected file is empty or exceeds 10 MiB" }
            require(validSignature(type, bytes)) { "The file contents do not match the selected file type" }
            val body = bytes.toRequestBody(type.toMediaType())
            val part = MultipartBody.Part.createFormData("file", item.name, body)
            api.upload("assignments/$assignmentId/attachments", part)
        }
}
