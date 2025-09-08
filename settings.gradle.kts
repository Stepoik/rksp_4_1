plugins {
    id("org.gradle.toolchains.foojay-resolver-convention") version "0.8.0"
}
rootProject.name = "rksp_4_1"

include(":prac_4:client")
include(":prac_4:server")
include(":prac_5")