plugins { id("com.android.library"); id("org.jetbrains.kotlin.android"); id("org.jetbrains.kotlin.plugin.compose") }
android {
    namespace = "uz.smartstudy.designsystem"
    compileSdk = 35
    defaultConfig { minSdk = 26 }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
}
android { buildFeatures { compose = true } }
dependencies {
api(platform("androidx.compose:compose-bom:2025.05.01"))
 api("androidx.compose.material3:material3")
 api("androidx.compose.ui:ui")
 api("androidx.compose.foundation:foundation")
}
