package org.example.prac3

import io.reactivex.rxjava3.core.Observable
import io.reactivex.rxjava3.core.Observable.combineLatest
import io.reactivex.rxjava3.schedulers.Schedulers
import java.util.concurrent.TimeUnit
import kotlin.random.Random

private const val TEMPERATURE_THRESHOLD = 25
private const val CO2_THRESHOLD = 70

data class Measures(
    val temperature: Int,
    val co2: Int
)

fun main() {
    val temperatureSensor = Observable.interval(1000, TimeUnit.MILLISECONDS)
        .map { Random.nextInt(15, 30) }
        .subscribeOn(Schedulers.io())

    val co2Sensor = Observable.interval(1000, TimeUnit.MILLISECONDS)
        .map { Random.nextInt(30, 100) }
        .subscribeOn(Schedulers.io())

    val measures = combineLatest(temperatureSensor, co2Sensor) { temperature, co2 ->
        Measures(temperature, co2)
    }

    measures.blockingSubscribe {
        if (it.temperature > TEMPERATURE_THRESHOLD && it.co2 > CO2_THRESHOLD) {
            println("ALARM!!!")
        }
    }
}

fun <T : Any> Observable<T>.delay(millis: Long): Observable<T> {
    return concatMap { Observable.just(it).delay(millis, TimeUnit.MILLISECONDS) }
}