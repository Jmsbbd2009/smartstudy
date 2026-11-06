plugins { id("com.android.library"); id("org.jetbrains.kotlin.android") }
android {
    namespace = "uz.smartstudy.devicepolicy"
    compileSdk = 35
    defaultConfig { minSdk = 26 }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
}
dependencies {
implementation(project(":domain"))
 implementation("androidx.core:core-ktx:1.16.0")
}

dependencies { implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.8.1") }
