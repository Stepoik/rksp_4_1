package org.example.service

import org.example.config.StorageProperties
import org.springframework.core.io.FileSystemResource
import org.springframework.core.io.Resource
import org.springframework.stereotype.Service
import org.springframework.util.FileSystemUtils
import org.springframework.web.multipart.MultipartFile
import java.io.IOException
import java.nio.file.Files
import java.nio.file.Path
import java.nio.file.StandardCopyOption
import java.util.*
import java.util.stream.Collectors

@Service
class FileStorageService(
    storageProperties: StorageProperties
) {
    private val rootLocation: Path = Path.of(storageProperties.location)

    init {
        initStorage()
    }

    fun initStorage() {
        try {
            if (!Files.exists(rootLocation)) {
                Files.createDirectories(rootLocation)
            }
        } catch (e: IOException) {
            throw RuntimeException("Не удалось инициализировать хранилище", e)
        }
    }

    fun store(file: MultipartFile, subfolder: String? = null, filename: String? = null): String {
        if (file.isEmpty) throw IllegalArgumentException("Пустой файл")
        val targetDir = if (subfolder.isNullOrBlank()) rootLocation else rootLocation.resolve(subfolder)
        try {
            if (!Files.exists(targetDir)) Files.createDirectories(targetDir)
            val original = (if (filename.isNullOrBlank()) file.originalFilename else filename) ?: "file-${UUID.randomUUID()}"
            val cleanName = Path.of(original).fileName.toString()
            val destination = targetDir.resolve(cleanName)
            file.inputStream.use { input ->
                Files.copy(input, destination, StandardCopyOption.REPLACE_EXISTING)
            }
            return rootLocation.relativize(destination).toString()
        } catch (e: IOException) {
            throw RuntimeException("Не удалось сохранить файл", e)
        }
    }

    fun load(relativePath: String): Resource {
        val filePath = rootLocation.resolve(relativePath).normalize()
        val resource = FileSystemResource(filePath)
        if (!resource.exists() || !resource.isReadable) {
            throw IllegalArgumentException("Файл не найден: $relativePath")
        }
        return resource
    }

    fun deleteAll() {
        FileSystemUtils.deleteRecursively(rootLocation)
        initStorage()
    }

    fun listAll(): List<String> {
        if (!Files.exists(rootLocation)) return emptyList()
        Files.createDirectories(rootLocation)
        Files.newDirectoryStream(rootLocation).use { topLevel ->
            // Соберём рекурсивно все файлы
        }
        return Files.walk(rootLocation)
            .filter { Files.isRegularFile(it) }
            .map { rootLocation.relativize(it).toString().replace('\\', '/') }
            .collect(Collectors.toList())
    }
}


