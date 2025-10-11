package org.example

import org.springframework.data.jpa.repository.JpaRepository
import org.springframework.stereotype.Repository

@Repository
interface AgentRepository : JpaRepository<Agent, Long> {
    fun findByCodeName(codeName: String): Agent?
} 