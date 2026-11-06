pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement { repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS); repositories { google(); mavenCentral() } }
rootProject.name = "SmartStudyControl"
include(":app", ":domain", ":data", ":devicepolicy", ":core:designsystem", ":sync")
