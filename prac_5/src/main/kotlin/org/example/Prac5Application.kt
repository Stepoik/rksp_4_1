package org.example

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication
import org.springframework.boot.context.properties.EnableConfigurationProperties
import org.example.config.StorageProperties

@SpringBootApplication
@EnableConfigurationProperties(StorageProperties::class)
class Prac5Application

fun main(args: Array<String>) {
    runApplication<Prac5Application>(*args)
}