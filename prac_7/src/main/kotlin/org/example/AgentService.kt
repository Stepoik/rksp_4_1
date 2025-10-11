package org.example

import org.springframework.stereotype.Service
import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import reactor.core.scheduler.Schedulers
import java.time.Duration

@Service
class AgentService(
    private val repository: AgentRepository
) {
    fun getAll(): Flux<Agent> = Mono.fromCallable { repository.findAll() }
        .flatMapMany { Flux.fromIterable(it) }
        .subscribeOn(Schedulers.boundedElastic())

    fun getById(id: Long): Mono<Agent> = Mono.fromCallable { repository.findById(id) }
        .flatMap { optional -> if (optional.isPresent) Mono.just(optional.get()) else Mono.empty() }
        .subscribeOn(Schedulers.boundedElastic())

    fun getByCodeName(codeName: String): Mono<Agent> = Mono.fromCallable { repository.findByCodeName(codeName) }
        .flatMap { agent -> if (agent != null) Mono.just(agent) else Mono.empty() }
        .subscribeOn(Schedulers.boundedElastic())

    fun create(agent: Agent): Mono<Agent> = Mono.fromCallable { repository.save(agent.copy(id = null)) }
        .subscribeOn(Schedulers.boundedElastic())

    fun update(id: Long, updated: Agent): Mono<Agent> = Mono.fromCallable {
        val existing = repository.findById(id)
        if (existing.isPresent) repository.save(updated.copy(id = id)) else null
    }.flatMap { saved -> if (saved != null) Mono.just(saved) else Mono.empty() }
        .subscribeOn(Schedulers.boundedElastic())

    fun delete(id: Long): Mono<Void> = Mono.fromCallable { repository.deleteById(id) }
        .subscribeOn(Schedulers.boundedElastic())
        .then()

    // Channel: апсерт потока агентов и возврат сохранённых
    fun upsertStream(agents: Flux<Agent>): Flux<Agent> = agents
        .flatMap { agent ->
            Mono.fromCallable { repository.save(agent) }
                .subscribeOn(Schedulers.boundedElastic())
        }

    // Fire-and-Forget: создать без ответа
    fun createFireAndForget(agent: Agent): Mono<Void> = Mono.fromCallable { repository.save(agent.copy(id = null)) }
        .subscribeOn(Schedulers.boundedElastic())
        .then()

    // Fire-and-Forget: удалить без ответа
    fun deleteFireAndForget(id: Long): Mono<Void> = Mono.fromCallable { repository.deleteById(id) }
        .subscribeOn(Schedulers.boundedElastic())
        .then()
} 