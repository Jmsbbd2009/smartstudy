plugins { id("com.android.library"); id("org.jetbrains.kotlin.android"); id("org.jetbrains.kotlin.kapt"); id("com.google.dagger.hilt.android"); id("org.jetbrains.kotlin.plugin.serialization") }
android {
    namespace = "uz.smartstudy.sync"
    compileSdk = 35
    defaultConfig { minSdk = 26 }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
}
dependencies {
implementation(project(":data"))
 implementation(project(":domain"))
 implementation(project(":devicepolicy"))
 implementation("androidx.work:work-runtime-ktx:2.10.1")
 implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.8.1")
 implementation("com.google.dagger:hilt-android:2.56.2")
 kapt("com.google.dagger:hilt-compiler:2.56.2")
}
dependencies { implementation("com.squareup.retrofit2:retrofit:2.11.0") }
