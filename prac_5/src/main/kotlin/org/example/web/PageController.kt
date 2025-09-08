package org.example.web

import org.example.service.FileStorageService
import org.springframework.stereotype.Controller
import org.springframework.ui.Model
import org.springframework.web.bind.annotation.GetMapping

@Controller
class PageController(
    private val storageService: FileStorageService
) {
    @GetMapping("/")
    fun index(model: Model): String {
        val files = storageService.listAll()
        model.addAttribute("files", files)
        return "index"
    }
}


