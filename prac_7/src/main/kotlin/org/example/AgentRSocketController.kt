package org.example

import org.springframework.stereotype.Controller
import org.springframework.web.bind.annotation.*
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono

@Controller
class AgentRSocketController(
    private val service: AgentService
) {
    @GetMapping("/agents")
    fun findAll(): Flux<Agent> = service.getAll()

    @GetMapping("/agents/{id}")
    fun findById(@PathVariable id: Long): Mono<Agent> = service.getById(id)

    @GetMapping("/agents/code/{code}")
    fun findByCodeName(@PathVariable("code") codeName: String): Mono<Agent> = service.getByCodeName(codeName)

    @PostMapping("/agents")
    fun create(agent: Agent): Mono<Agent> = service.create(agent)

    @PutMapping("/agents/{id}")
    fun update(@PathVariable id: Long, agent: Agent): Mono<Agent> = service.update(id, agent)

    @DeleteMapping("/agents/{id}")
    fun delete(@PathVariable id: Long): Mono<Void> = service.deleteFireAndForget(id)
} 