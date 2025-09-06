package org.example.prac2

import org.apache.commons.io.FileUtils
import java.io.*
import java.nio.file.Files
import java.nio.file.StandardCopyOption
import kotlin.system.measureTimeMillis

fun main() {
    val fileSrc = File("bigfile.bin")
    val fileDst = File("bigfile2.bin")

    measureTime(src = fileSrc, dst = fileDst, tag = "IOStreams") { src, dst ->
        copyFileIOStreams(src, dst)
    }
    measureTime(src = fileSrc, dst = fileDst, tag = "Channels") { src, dst ->
        copyFileChannel(src, dst)
    }
    measureTime(src = fileSrc, dst = fileDst, tag = "Apache") { src, dst ->
        copyFileApache(src, dst)
    }
    measureTime(src = fileSrc, dst = fileDst, tag = "NIO2") { src, dst ->
        copyFileNIO2(src, dst)
    }
}

fun copyFileIOStreams(src: File, dst: File) {
    FileInputStream(src).use { input ->
        FileOutputStream(dst).use { output ->
            val buf = ByteArray(64 * 1024)
            while (true) {
                val n = input.read(buf)
                if (n < 0) break
                output.write(buf, 0, n)
            }
        }
    }
}

fun copyFileChannel(src: File, dst: File) {
    FileInputStream(src).channel.use { inCh ->
        FileOutputStream(dst).channel.use { outCh ->
            var pos = 0L
            val size = inCh.size()
            while (pos < size) {
                val sent = inCh.transferTo(pos, size - pos, outCh)
                if (sent <= 0) break
                pos += sent
            }
        }
    }
}

fun copyFileApache(src: File, dst: File) {
    FileUtils.copyFile(src, dst)
}

fun copyFileNIO2(src: File, dst: File) {
    Files.copy(src.toPath(), dst.toPath(), StandardCopyOption.REPLACE_EXISTING)
}

fun measureTime(src: File, dst: File, tag: String = "", block: (src: File, dst: File) -> Unit) {
    if (dst.exists()) dst.delete()
    val result = measureTimeMillis {
        block(src, dst)
    }
    println("$tag millis $result")
}
