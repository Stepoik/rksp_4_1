package org.example

import jakarta.persistence.Column
import jakarta.persistence.Entity
import jakarta.persistence.GeneratedValue
import jakarta.persistence.GenerationType
import jakarta.persistence.Id
import jakarta.persistence.Table

@Entity
@Table(name = "agents")
data class Agent(
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Long? = null,

    @Column(nullable = false, unique = true)
    val codeName: String,

    @Column(nullable = false)
    val role: String,

    @Column(nullable = false)
    val country: String,

    @Column(nullable = false)
    val ult: String
) 