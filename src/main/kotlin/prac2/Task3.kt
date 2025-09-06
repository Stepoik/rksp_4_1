package org.example.prac2

import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.file.Path
import kotlin.io.path.Path

fun main() {
    println(checksum16(Path("bigfile.bin")))
}

fun checksum16(filePath: Path, bufferSize: Int = 64 * 1024): Int {
    FileInputStream(filePath.toFile()).channel.use { ch ->
        val buf = ByteBuffer.allocate(bufferSize)

        var sum = 0L          // аккумулируем в 64 битах, чтобы не потерять переносы
        var leftover = -1     // если чанк закончился на нечётном байте, держим его тут

        while (true) {
            buf.clear()
            val n = ch.read(buf)
            if (n <= 0) break
            buf.flip()

            // если с прошлого раза остался старший байт слова
            if (leftover != -1) {
                if (buf.hasRemaining()) {
                    val b2 = buf.get().toInt() and 0xFF
                    val word = (leftover shl 8) or b2
                    sum += word
                    leftover = -1
                } // иначе подождём следующий чанк
            }

            // читаем по два байта = одно 16-битное слово (big-endian)
            while (buf.remaining() >= 2) {
                val b1 = buf.get().toInt() and 0xFF
                val b2 = buf.get().toInt() and 0xFF
                val word = (b1 shl 8) or b2
                sum += word
                // периодически складываем переносы, чтобы не росло слишком высоко
                if ((sum and 0xFFFF0000L) != 0L) {
                    sum = (sum and 0xFFFF) + (sum ushr 16)
                }
            }

            // если остался одинокий байт, запомним как старший байт следующего слова
            if (buf.hasRemaining()) {
                leftover = buf.get().toInt() and 0xFF
            }
        }

        // если файл имел нечётное число байт, дополним нулём младший байт
        if (leftover != -1) {
            sum += (leftover shl 8)
        }

        // финальное «сворачивание» переносов
        while ((sum ushr 16) != 0L) {
            sum = (sum and 0xFFFF) + (sum ushr 16)
        }

        // инверсия и маска до 16 бит
        return ((sum.inv()) and 0xFFFF).toInt()
    }
}