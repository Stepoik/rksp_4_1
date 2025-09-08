package org.example.web

import org.example.service.FileStorageService
import org.springframework.core.io.Resource
import org.springframework.http.HttpHeaders
import org.springframework.http.MediaType
import org.springframework.http.ResponseEntity
import org.springframework.web.bind.annotation.*
import org.springframework.web.multipart.MultipartFile

@RestController
@RequestMapping("/files")
class FileUploadController(
    private val storageService: FileStorageService
) {
    @PostMapping("/upload")
    fun upload(
        @RequestParam("file") file: MultipartFile,
        @RequestParam(name = "subfolder", required = false) subfolder: String?,
        @RequestParam(name = "filename", required = false) filename: String?
    ): Map<String, String> {
        val path = storageService.store(file, subfolder, filename)
        return mapOf("path" to path)
    }

    @GetMapping("/download")
    fun download(@RequestParam("path") relativePath: String): ResponseEntity<Resource> {
        val resource = storageService.load(relativePath)
        return ResponseEntity.ok()
            .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"${resource.filename}\"")
            .contentType(MediaType.APPLICATION_OCTET_STREAM)
            .body(resource)
    }
}


