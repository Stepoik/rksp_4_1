package org.example.client

import org.springframework.boot.CommandLineRunner
import org.springframework.context.annotation.Bean
import org.springframework.context.annotation.Configuration
import reactor.core.publisher.Flux

@Configuration
class DemoRunnerConfig {
    @Bean
    fun demoRunner(client: AgentClient) = CommandLineRunner {
        // Request-Stream
        client.findAll().take(3).doOnNext { println("RS findAll -> $it") }.blockLast()

        // Request-Response create
        val reyna = client.create(Agent(codeName = "Reyna", role = "Duelist", country = "Mexico", ult = "Empress"))
            .doOnNext { println("RR create -> $it") }
            .block()

        if (reyna != null) {
            // Request-Response findById
            client.findById(reyna.id!!).doOnNext { println("RR findById -> $it") }.block()

            // Request-Response update
            client.update(reyna.id, reyna.copy(role = "OP-Duelist"))
                .doOnNext { println("RR update -> $it") }
                .block()

            // Fire-and-Forget delete (создадим отдельно и удалим)
            client.createFnf(Agent(codeName = "Skye", role = "Initiator", country = "Australia", ult = "Seekers")).block()
            client.deleteFnf(reyna.id).block()
        }

        // Channel upsert stream
        val stream = Flux.just(
            Agent(codeName = "Breach", role = "Initiator", country = "Sweden", ult = "Rolling Thunder"),
            Agent(codeName = "Viper", role = "Controller", country = "USA", ult = "Vipers Pit")
        )
        client.upsertStream(stream).doOnNext { println("CHANNEL upsert -> $it") }.blockLast()

        // Request-Response delete (проверка маршрута RR)
        client.delete(9999).onErrorResume { _ -> reactor.core.publisher.Mono.empty() }.block()
    }
} 