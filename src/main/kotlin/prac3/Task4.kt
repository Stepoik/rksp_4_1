package org.example.prac3

import io.reactivex.rxjava3.core.Flowable
import io.reactivex.rxjava3.functions.BiFunction
import io.reactivex.rxjava3.schedulers.Schedulers
import kotlin.random.Random

enum class FileType {
    XML,
    JSON,
    XLS
}

data class File(val size: Int, val type: FileType)

fun main() {
    val files = Flowable.generate<File, Int>({ 0 }, BiFunction { state, emitter ->
        val size = Random.nextInt(10, 100)
        val type = FileType.entries.random()
        val file = File(size = size, type = type)
        emitter.onNext(file)

        state + 1
    })
        .subscribeOn(Schedulers.single())
        .publish()
        .autoConnect(3)
        .rebatchRequests(5)


    files.subscribe {
        println("ALL $it")
    }
    val xmlConsumer = startConsumer(files, type = FileType.XML)
    val jsonConsumer = startConsumer(files, type = FileType.JSON)
    val xlsConsumer = startConsumer(files, type = FileType.XLS)
    Flowable.merge(xmlConsumer, jsonConsumer, xlsConsumer)
        .blockingSubscribe {
            println(it)
        }

}

fun startConsumer(files: Flowable<File>, type: FileType): Flowable<File> {
    return files
        .observeOn(Schedulers.computation())
        .filter { it.type == type }
        .flatMap {
            Flowable.fromCallable {
                println(Thread.currentThread())
                processFile(it)
            }.subscribeOn(Schedulers.computation())
        }
}

fun processFile(file: File): File {
    println("$file in processing")
    Thread.sleep(file.size * 700L)
    return file
}