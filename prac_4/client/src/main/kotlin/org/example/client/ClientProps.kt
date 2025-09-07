package org.example.client

import org.springframework.boot.context.properties.ConfigurationProperties
import org.springframework.boot.context.properties.EnableConfigurationProperties
import org.springframework.context.annotation.Configuration

@Configuration
@EnableConfigurationProperties(ClientProps::class)
class ClientPropsConfig

@ConfigurationProperties(prefix = "server.rsocket")
data class ClientProps(
    val host: String = "localhost",
    val port: Int = 7000
) 