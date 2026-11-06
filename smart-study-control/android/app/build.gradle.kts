plugins {
    id("com.android.application"); id("org.jetbrains.kotlin.android"); id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.plugin.serialization"); id("org.jetbrains.kotlin.kapt"); id("com.google.dagger.hilt.android")
}
val debugApi = providers.gradleProperty("DEBUG_API_URL").orElse("http://10.0.2.2:8000/api/v1/")
val releaseApi = providers.gradleProperty("API_URL").orElse("https://configure-api.invalid/api/v1/")
android {
    namespace = "uz.smartstudy.control"
    compileSdk = 35
    defaultConfig {
        applicationId = "uz.smartstudy.control"
        minSdk = 26; targetSdk = 35; versionCode = 4; versionName = "0.3.1"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }
    buildFeatures { compose = true; buildConfig = true }
    buildTypes {
        debug { buildConfigField("String", "API_URL", "\"${debugApi.get()}\""); manifestPlaceholders["cleartext"] = "true"; buildConfigField("String", "ADMIN_WEB_URL", "\"${providers.gradleProperty("DEBUG_ADMIN_WEB_URL").orElse("http://10.0.2.2:5173/").get()}\"") }
        release {
            buildConfigField("String", "API_URL", "\"${releaseApi.get()}\"")
            manifestPlaceholders["cleartext"] = "false"
            buildConfigField("String", "ADMIN_WEB_URL", "\"${providers.gradleProperty("ADMIN_WEB_URL").orElse("https://configure-admin.invalid/").get()}\"")
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
}
tasks.matching { it.name == "preReleaseBuild" }.configureEach {
    doFirst { require(releaseApi.get().startsWith("https://") && !releaseApi.get().contains("configure-api.invalid")) { "Pass -PAPI_URL=https://your-host/api/v1/ for release" } }
}
dependencies {
    implementation(project(":domain")); implementation(project(":data")); implementation(project(":devicepolicy")); implementation(project(":sync")); implementation(project(":core:designsystem"))
    implementation("androidx.activity:activity-compose:1.10.1")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.9.0")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.9.0")
    implementation("androidx.navigation:navigation-compose:2.9.0")
    implementation("androidx.hilt:hilt-navigation-compose:1.2.0")
    implementation("androidx.work:work-runtime-ktx:2.10.1")
    implementation("androidx.core:core-ktx:1.16.0")
    implementation("com.google.dagger:hilt-android:2.56.2")
    kapt("com.google.dagger:hilt-compiler:2.56.2")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.8.1")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.10.2")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.10.2")
    androidTestImplementation(platform("androidx.compose:compose-bom:2025.05.01"))
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    androidTestImplementation("androidx.test.ext:junit:1.2.1")
    debugImplementation("androidx.compose.ui:ui-test-manifest")
}
dependencies { implementation("com.squareup.retrofit2:retrofit:2.11.0") }

dependencies {
 androidTestImplementation("androidx.test:core-ktx:1.6.1")
 androidTestImplementation("androidx.room:room-runtime:2.7.1")
 androidTestImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.10.2")
}

android { sourceSets.getByName("androidTest").assets.srcDir(project(":data").file("schemas")) }
dependencies { androidTestImplementation("androidx.room:room-testing:2.7.1") }

dependencies {
 implementation("com.google.mlkit:image-labeling:17.0.9")

}
