package com.ippel.kotlinutils

import io.ktor.client.request.*
import io.ktor.http.*
import io.ktor.server.application.*
import io.ktor.server.testing.*
import kotlin.test.Test
import kotlin.test.assertEquals

class ServerTest {
    @Test
    fun health_endpoint_should_return_ok_true() = testApplication {
        application(Application::kotlinUtilsModule)
        val response = client.get("/health")
        assertEquals(HttpStatusCode.OK, response.status)
    }
}
