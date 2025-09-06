package org.example.prac3

import io.reactivex.rxjava3.core.Observable
import io.reactivex.rxjava3.core.Observable.merge
import io.reactivex.rxjava3.schedulers.Schedulers
import kotlin.random.Random

fun main() {
    third()
}

fun first() {
    val numsProducer = createNumsProducer(1000)

    numsProducer
        .scan(0) { t1, t2 -> t1 + 1 }
        .blockingSubscribe { t1 -> println(t1) }
}

fun second() {
    val numsProducer1 = createNumsProducer(1000)
        .subscribeOn(Schedulers.io())
        .delay(10)
    val numsProducer2 = createNumsProducer(1000)
        .subscribeOn(Schedulers.io())
        .delay(10)
    merge(numsProducer1, numsProducer2)
        .blockingSubscribe {
            println(it)
        }
}

fun third() {
    val result = Observable.range(1, Random.nextInt(1, 100))
        .doOnEach { println(it) }
        .last(1)
        .blockingGet()
    println(result)
}

fun createNumsProducer(count: Int): Observable<Int> {
    return Observable.range(1, count)
//        .map { Random.nextInt(0, 1000) }
}