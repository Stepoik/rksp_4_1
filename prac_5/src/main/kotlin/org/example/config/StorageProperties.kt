package org.example.config

import org.springframework.boot.context.properties.ConfigurationProperties

@ConfigurationProperties(prefix = "storage")
class StorageProperties {
    var location: String = "uploads"
}


