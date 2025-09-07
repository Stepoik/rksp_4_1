package org.example.client

import org.springframework.stereotype.Service
import org.springframework.messaging.rsocket.RSocketRequester
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono

@Service
class AgentClient(private val requester: RSocketRequester) {
    // Request-Stream
    fun findAll(): Flux<Agent> = requester
        .route("agents.findAll")
        .retrieveFlux(Agent::class.java)

    // Request-Response
    fun findById(id: Long): Mono<Agent> = requester
        .route("agents.findById.{id}", id)
        .retrieveMono(Agent::class.java)

    // Request-Response
    fun create(agent: Agent): Mono<Agent> = requester
        .route("agents.create")
        .data(agent)
        .retrieveMono(Agent::class.java)

    // Request-Response
    fun update(id: Long, agent: Agent): Mono<Agent> = requester
        .route("agents.update.{id}", id)
        .data(agent)
        .retrieveMono(Agent::class.java)

    // Request-Response
    fun delete(id: Long): Mono<Void> = requester
        .route("agents.delete.{id}", id)
        .retrieveMono(Void::class.java)
        .then()

    // Fire-and-Forget
    fun createFnf(agent: Agent): Mono<Void> = requester
        .route("agents.create.ff")
        .data(agent)
        .send()

    // Fire-and-Forget
    fun deleteFnf(id: Long): Mono<Void> = requester
        .route("agents.delete.ff.{id}", id)
        .send()

    // Channel
    fun upsertStream(incoming: Flux<Agent>): Flux<Agent> = requester
        .route("agents.upsert.stream")
        .data(incoming, Agent::class.java)
        .retrieveFlux(Agent::class.java)
} 