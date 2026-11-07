package uz.smartstudy.control

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.PasswordVisualTransformation
import kotlinx.serialization.json.*

@Composable fun TelegramSignIn(vm:StudyViewModel,login:String) {
    val context=LocalContext.current
    var challenge by remember {mutableStateOf<JsonObject?>(null)};var code by remember {mutableStateOf("")}
    Text(stringResource(R.string.login_telegram_help),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
    Action(R.string.telegram_signin,login.isNotBlank()){vm.run {val result=vm.repository.api.post("auth/telegram/login/start",body("login" to login));challenge=result;context.startActivity(Intent(Intent.ACTION_VIEW,Uri.parse(result.text("deep_link"))))}}
    challenge?.let {pending->
        Action(R.string.open_telegram){runCatching {context.startActivity(Intent(Intent.ACTION_VIEW,Uri.parse(pending.text("deep_link"))))}}
        Input(R.string.telegram_code,code){code=it.filter(Char::isDigit).take(6)}
        Action(R.string.confirm_code,code.length==6){vm.run {
            val response=vm.repository.api.post("auth/telegram/login/finish",buildJsonObject {put("challenge_id",pending.text("challenge_id"));put("verifier",pending.text("verifier"));put("code",code)})
            vm.acceptSession(response)
        }}
    }
}
@Composable fun RenewPasswordScreen(vm:StudyViewModel) {
    var old by remember {mutableStateOf("")};var fresh by remember {mutableStateOf("")}
    Page(R.string.renew_password) {
        Text(stringResource(R.string.renew_help))
        OutlinedTextField(old,{old=it},label={Text(stringResource(R.string.password))},visualTransformation=PasswordVisualTransformation())
        OutlinedTextField(fresh,{fresh=it},label={Text(stringResource(R.string.new_password))},visualTransformation=PasswordVisualTransformation())
        Action(R.string.save,old.isNotBlank() && fresh.length>=12){vm.run {
            vm.acceptSession(vm.repository.api.post("auth/password",buildJsonObject {put("current_password",old);put("new_password",fresh)}))
        }}
        Action(R.string.logout){vm.logout()}
    }
}
@Composable fun StaffSecurityScreen(vm:StudyViewModel) {
    val context=LocalContext.current
    var password by remember {mutableStateOf("")};var challenge by remember {mutableStateOf<JsonObject?>(null)}
    Page(R.string.account_security) {
        Text(stringResource(R.string.staff_security_help))
        OutlinedTextField(password,{password=it},label={Text(stringResource(R.string.password))},visualTransformation=PasswordVisualTransformation())
        Action(R.string.telegram_link,password.isNotBlank()){vm.run {val result=vm.repository.api.post("auth/telegram/link/start",body("password" to password));challenge=result;context.startActivity(Intent(Intent.ACTION_VIEW,Uri.parse(result.text("deep_link"))))}}
        challenge?.let {pending->
            Action(R.string.open_telegram){runCatching {context.startActivity(Intent(Intent.ACTION_VIEW,Uri.parse(pending.text("deep_link"))))}}
            Action(R.string.telegram_link_confirm){vm.run {vm.repository.api.post("auth/telegram/link/finish",buildJsonObject {put("challenge_id",pending.text("challenge_id"));put("verifier",pending.text("verifier"));put("password",password)});challenge=null}}
        }
    }
}
