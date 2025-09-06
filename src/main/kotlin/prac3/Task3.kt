package org.example.prac3

import io.reactivex.rxjava3.core.Observable
import io.reactivex.rxjava3.schedulers.Schedulers
import kotlin.random.Random

data class UserFriend(val userId: Int, val friendId: Int)

val usersList = List(100) {
    UserFriend(Random.nextInt(1, 30), Random.nextInt(1, 30))
}

fun main() {
    println(usersList)
    Observable.range(0, 10)
        .flatMap(::getFriends)
        .blockingSubscribe(::println)
}

fun getFriends(userId: Int): Observable<UserFriend> {
    return Observable.fromArray(*usersList.toTypedArray())
        .filter { it.userId == userId }
}