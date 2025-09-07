package org.example.client

import org.springframework.boot.autoconfigure.SpringBootApplication
import org.springframework.boot.runApplication
import org.springframework.context.annotation.Bean
import org.springframework.messaging.rsocket.RSocketRequester
import org.springframework.messaging.rsocket.RSocketStrategies
import org.springframework.util.MimeTypeUtils
import reactor.util.retry.Retry
import java.time.Duration

@SpringBootApplication
class ClientApplication {
    @Bean
    fun rSocketRequester(builder: RSocketRequester.Builder, strategies: RSocketStrategies, clientProps: ClientProps): RSocketRequester {
        return builder
            .dataMimeType(MimeTypeUtils.APPLICATION_JSON)
            .rsocketStrategies(strategies)
            .rsocketConnector { connector ->
                connector.reconnect(
                    Retry.fixedDelay(20, Duration.ofSeconds(1))
                        .doBeforeRetry { signal -> println("RSocket reconnect attempt #${'$'}{signal.totalRetries()+1}") }
                )
            }
            .tcp(clientProps.host, clientProps.port)
    }
}

fun main(args: Array<String>) {
    runApplication<ClientApplication>(*args)
} 