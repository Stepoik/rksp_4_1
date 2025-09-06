import org.example.prac2.checksum16
import java.nio.charset.StandardCharsets
import java.nio.file.*
import java.nio.file.StandardWatchEventKinds.*
import java.time.LocalTime
import java.util.concurrent.TimeUnit
import kotlin.io.path.isRegularFile

// Снимок файла для быстрых сравнений и печати при удалении
data class FileSnapshot(
    val size: Long,
    val checksum16: Int,
    val lineCounts: Map<String, Int> // мультисет строк
)

fun main() {
    val dir = Paths.get(".").toAbsolutePath().normalize()
    require(Files.isDirectory(dir)) { "Не папка: $dir" }
    println("Слежу за: $dir")

    val watcher = FileSystems.getDefault().newWatchService()
    dir.register(watcher, ENTRY_CREATE, ENTRY_MODIFY, ENTRY_DELETE)

    // Кеш последних снимков по абсолютному пути
    val cache = mutableMapOf<Path, FileSnapshot>()

    while (true) {
        val key = watcher.take() // блокируемся до событий
        for (event in key.pollEvents()) {
            val kind = event.kind()
            if (kind == OVERFLOW) continue

            @Suppress("UNCHECKED_CAST")
            val ev = event as WatchEvent<Path>
            val child = dir.resolve(ev.context()).toAbsolutePath().normalize()

            when (kind) {
                ENTRY_CREATE -> {
                    if (!Files.exists(child) || !child.isRegularFile()) {
                        println(ts() + "CREATE: ${child.fileName} (не файл, пропускаю)")
                        continue
                    }
                    println(ts() + "CREATE: ${child.fileName}")
                    // Дадим файловой системе дописать файл (на случай больших копий)
                    val snap = safeSnapshot(child)
                    if (snap != null) cache[child] = snap
                }

                ENTRY_MODIFY -> {
                    if (!Files.exists(child) || !child.isRegularFile()) continue
                    // Небольшая задержка чтобы поймать «стабильное» состояние
                    val prev = cache[child]
                    val nowSnap = safeSnapshot(child)
                    if (nowSnap == null) continue
                    cache[child] = nowSnap

                    if (prev != null) {
                        val (added, removed) = diffLines(prev.lineCounts, nowSnap.lineCounts)
                        if (added.isEmpty() && removed.isEmpty()) {
                            println(ts() + "MODIFY: ${child.fileName} без изменений по строкам")
                        } else {
                            println(ts() + "MODIFY: ${child.fileName}")
                            if (added.isNotEmpty()) {
                                println("  Добавлены строки:")
                                added.forEach { (line, cnt) ->
                                    val suffix = if (cnt > 1) " x$cnt" else ""
                                    println("    + $line$suffix")
                                }
                            }
                            if (removed.isNotEmpty()) {
                                println("  Удалены строки:")
                                removed.forEach { (line, cnt) ->
                                    val suffix = if (cnt > 1) " x$cnt" else ""
                                    println("    - $line$suffix")
                                }
                            }
                        }
                    } else {
                        println(ts() + "MODIFY: ${child.fileName} (нет предыдущего снимка, сравнить нельзя)")
                    }
                }

                ENTRY_DELETE -> {
                    // Файла уже нет. Берем последний снимок, если он был.
                    val snap = cache.remove(child)
                    if (snap != null) {
                        println(ts() + "DELETE: ${child.fileName} size=${snap.size} bytes, checksum=${"%04X".format(snap.checksum16)}")
                    } else {
                        println(ts() + "DELETE: ${child.fileName}")
                        println("  Не могу вывести размер и контрольную сумму. Файл уже удален, а снимка не было.")
                        println("  Обоснование: после удаления по пути к файлу не добраться, а Java не хранит его данные. " +
                                "Единственный способ — считать и сохранить размер/чексумму заранее (на событиях CREATE/MODIFY) " +
                                "или держать открытый дескриптор, что кроссплатформенно не гарантируется.")
                    }
                }
            }
        }
        val valid = key.reset()
        if (!valid) break
    }
}

private fun safeSnapshot(path: Path, attempts: Int = 3, waitMs: Long = 120): FileSnapshot? {
    if (!Files.exists(path)) return null
    if (!path.isRegularFile()) return null

    var lastSize = -1L
    repeat(attempts) {
        val s1 = runCatching { Files.size(path) }.getOrElse { return null }
        sleep(waitMs)
        val s2 = runCatching { Files.size(path) }.getOrElse { return null }
        if (s1 == s2) {
            val lines = runCatching { readAllLinesUtf8(path) }.getOrElse { return null }
            val checksum = runCatching { checksum16(path) }.getOrElse { return null }
            return FileSnapshot(size = s2, checksum16 = checksum, lineCounts = toCounts(lines))
        }
        lastSize = s2
    }
    // Если за попытки размер дергался, всё равно попробуем один раз
    val size = runCatching { Files.size(path) }.getOrElse { return null }
    val lines = runCatching { readAllLinesUtf8(path) }.getOrElse { return null }
    val checksum = runCatching { checksum16(path) }.getOrElse { return null }
    return FileSnapshot(size = size, checksum16 = checksum, lineCounts = toCounts(lines))
}

private fun readAllLinesUtf8(path: Path): List<String> =
    Files.readAllLines(path, StandardCharsets.UTF_8)

// Мультисет строк
private fun toCounts(lines: List<String>): Map<String, Int> {
    val m = HashMap<String, Int>(lines.size * 2)
    for (ln in lines) m[ln] = (m[ln] ?: 0) + 1
    return m
}

private fun diffLines(oldC: Map<String, Int>, newC: Map<String, Int>):
        Pair<Map<String, Int>, Map<String, Int>> {
    val added = mutableMapOf<String, Int>()
    val removed = mutableMapOf<String, Int>()
    val keys = HashSet<String>().apply {
        addAll(oldC.keys); addAll(newC.keys)
    }
    for (k in keys) {
        val o = oldC[k] ?: 0
        val n = newC[k] ?: 0
        if (n > o) added[k] = n - o
        if (o > n) removed[k] = o - n
    }
    return added to removed
}

private fun ts(): String = "[${LocalTime.now()}] "

private fun sleep(ms: Long) {
    try { TimeUnit.MILLISECONDS.sleep(ms) } catch (_: InterruptedException) {}
}