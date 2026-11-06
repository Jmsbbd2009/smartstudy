plugins { id("com.android.library"); id("org.jetbrains.kotlin.android"); id("org.jetbrains.kotlin.kapt"); id("com.google.dagger.hilt.android"); id("org.jetbrains.kotlin.plugin.serialization") }
android {
    namespace = "uz.smartstudy.data"
    compileSdk = 35
    defaultConfig { minSdk = 26 }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
}
dependencies {
implementation(project(":domain"))
 implementation("androidx.core:core-ktx:1.16.0")
 implementation("androidx.room:room-runtime:2.7.1")
 implementation("androidx.room:room-ktx:2.7.1")
 kapt("androidx.room:room-compiler:2.7.1")
 implementation("androidx.datastore:datastore-preferences:1.1.4")
 implementation("com.squareup.retrofit2:retrofit:2.11.0")
 implementation("com.squareup.retrofit2:converter-kotlinx-serialization:2.11.0")
 implementation("com.squareup.okhttp3:okhttp:4.12.0")
 implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.8.1")
 implementation("com.google.dagger:hilt-android:2.56.2")
 kapt("com.google.dagger:hilt-compiler:2.56.2")
}

kapt { arguments { arg("room.schemaLocation", "$projectDir/schemas") } }
