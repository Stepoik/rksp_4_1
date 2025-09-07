package org.example

import org.springframework.messaging.handler.annotation.DestinationVariable
import org.springframework.messaging.handler.annotation.MessageMapping
import org.springframework.stereotype.Controller
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono

@Controller
class AgentRSocketController(
    private val service: AgentService
) {
    // Request-Stream
    @MessageMapping("agents.findAll")
    fun findAll(): Flux<Agent> = service.getAll()

    // Request-Response
    @MessageMapping("agents.findById.{id}")
    fun findById(@DestinationVariable id: Long): Mono<Agent> = service.getById(id)

    // Request-Response
    @MessageMapping("agents.findByCodeName.{code}")
    fun findByCodeName(@DestinationVariable("code") codeName: String): Mono<Agent> = service.getByCodeName(codeName)

    // Request-Response
    @MessageMapping("agents.create")
    fun create(agent: Agent): Mono<Agent> = service.create(agent)

    // Request-Response
    @MessageMapping("agents.update.{id}")
    fun update(@DestinationVariable id: Long, agent: Agent): Mono<Agent> = service.update(id, agent)

    // Fire-and-Forget
    @MessageMapping("agents.create.ff")
    fun createFireAndForget(agent: Agent): Mono<Void> = service.createFireAndForget(agent)

    // Fire-and-Forget
    @MessageMapping("agents.delete.ff.{id}")
    fun deleteFireAndForget(@DestinationVariable id: Long): Mono<Void> = service.deleteFireAndForget(id)

    // Channel (bi-directional): клиент шлёт поток агентов, сервер возвращает поток сохранённых
    @MessageMapping("agents.upsert.stream")
    fun upsertStream(agents: Flux<Agent>): Flux<Agent> = service.upsertStream(agents)

    // Request-Response
    @MessageMapping("agents.delete.{id}")
    fun delete(@DestinationVariable id: Long): Mono<Void> = service.delete(id)
} 