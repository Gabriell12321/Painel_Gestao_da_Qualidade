package com.ippel.kotlinutils

import io.ktor.server.application.*
import io.ktor.server.engine.*
import io.ktor.server.netty.*
import io.ktor.server.response.*
import io.ktor.server.request.*
import io.ktor.server.routing.*
import io.ktor.http.*
import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.plugins.contentnegotiation.*

import com.google.zxing.BarcodeFormat
import com.google.zxing.MultiFormatWriter
import com.google.zxing.client.j2se.MatrixToImageWriter
import com.google.zxing.common.BitMatrix

import java.io.ByteArrayOutputStream

fun Application.kotlinUtilsModule() {
    install(ContentNegotiation) { json() }
    routing {
        get("/health") {
            call.respond(mapOf("ok" to true))
        }
        get("/qr.png") {
            val text = call.request.queryParameters["text"] ?: return@get call.respond(HttpStatusCode.BadRequest, "missing text")
            val size = (call.request.queryParameters["size"] ?: "256").toIntOrNull() ?: 256
            val matrix: BitMatrix = MultiFormatWriter().encode(text, BarcodeFormat.QR_CODE, size, size)
            val baos = ByteArrayOutputStream()
            MatrixToImageWriter.writeToStream(matrix, "PNG", baos)
            call.respondBytes(baos.toByteArray(), ContentType.Image.PNG)
        }
    }
}

fun main() {
    val host = System.getenv("KOTLIN_UTILS_HOST") ?: "0.0.0.0"
    val port = (System.getenv("KOTLIN_UTILS_PORT") ?: "8084").toInt()
    embeddedServer(Netty, port = port, host = host, module = Application::kotlinUtilsModule).start(wait = true)
}
