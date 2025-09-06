package org.example.prac2

import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.charset.Charset


fun main() {
    val filePath = "file.txt"
    runCatching {
        val charset = Charset.forName("UTF-8")
        val decoder = charset.newDecoder()
        FileInputStream(filePath).use { fis ->
            fis.channel.use { channel ->
                val buffer: ByteBuffer = ByteBuffer.allocate(1024)
                while (channel.read(buffer) > 0) {
                    buffer.flip()
                    print(decoder.decode(buffer))
                    buffer.clear()
                }
            }
        }
    }
}