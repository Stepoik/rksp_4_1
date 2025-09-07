package org.example.client

data class Agent(
    val id: Long? = null,
    val codeName: String,
    val role: String,
    val country: String,
    val ult: String
) 