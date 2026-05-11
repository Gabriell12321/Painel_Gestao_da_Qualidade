package com.ippel.scalatools

import akka.actor.ActorSystem
import akka.http.scaladsl.Http
import akka.http.scaladsl.model._
import akka.http.scaladsl.model.headers.`Content-Type`
import akka.http.scaladsl.server.Directives._
import akka.stream.Materializer
import akka.util.ByteString
import scala.concurrent.duration._
import scala.concurrent.{ExecutionContextExecutor, Future}
import java.util.Base64

object Server extends App {
  implicit val system: ActorSystem = ActorSystem("scala-tools")
  implicit val materializer: Materializer = Materializer(system)
  implicit val executionContext: ExecutionContextExecutor = system.dispatcher

  val host = sys.env.getOrElse("SCALA_TOOLS_HOST", "0.0.0.0")
  val port = sys.env.getOrElse("SCALA_TOOLS_PORT", "8086").toInt

  val route =
    path("health") {
      get {
        complete(HttpEntity(ContentTypes.`application/json`, "{""ok"":true}"))
      }
    } ~
    pathPrefix("b64") {
      path("encode") {
        post {
          entity(as[String]) { body =>
            val encoded = Base64.getEncoder.encodeToString(body.getBytes("UTF-8"))
            complete(HttpEntity(ContentTypes.`application/json`, s"{""ok"":true,""data"":$"""$encoded"""}"))
          }
        }
      } ~
      path("decode") {
        post {
          entity(as[String]) { body =>
            try {
              val decoded = new String(Base64.getDecoder.decode(body.trim), "UTF-8")
              complete(HttpEntity(ContentTypes.`application/json`, s"{""ok"":true,""data"":$"""$decoded"""}"))
            } catch {
              case _: IllegalArgumentException =>
                complete(StatusCodes.BadRequest, HttpEntity(ContentTypes.`application/json`, "{""ok"":false,""error"":""invalid base64""}"))
            }
          }
        }
      }
    }

  val bindingFuture = Http().newServerAt(host, port).bind(route)
  println(s"ScalaTools running on $host:$port")
}
