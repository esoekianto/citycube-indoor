allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}
subprojects {
    project.evaluationDependsOn(":app")
    pluginManager.withPlugin("com.android.library") {
        extensions.configure<com.android.build.gradle.LibraryExtension> {
            compileSdk = 36
        }
        // mapbox_maps_flutter_mobile 3.x targets AGP 9 built-in Kotlin and no
        // longer applies kotlin-android itself. Flutter 3.44 still builds with
        // the Kotlin Gradle Plugin (android.builtInKotlin=false), so apply it
        // here before the plugin's build script reaches its `kotlin {}` block.
        if (project.name == "mapbox_maps_flutter_mobile") {
            apply(plugin = "org.jetbrains.kotlin.android")
        }
    }
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
