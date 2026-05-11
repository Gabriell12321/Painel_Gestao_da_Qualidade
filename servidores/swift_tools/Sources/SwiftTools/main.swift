import NIO
import NIOHTTP1
import Foundation
import CryptoSwift

final class HTTPHandler: ChannelInboundHandler {
    typealias InboundIn = HTTPServerRequestPart
    typealias OutboundOut = HTTPServerResponsePart

    var buffer: ByteBuffer!
    var bodyData = Data()

    func channelRead(context: ChannelHandlerContext, data: NIOAny) {
        let part = self.unwrapInboundIn(data)
        switch part {
        case .head(_):
            bodyData.removeAll(keepingCapacity: true)
        case .body(let chunk):
            var c = chunk
            if let bytes = c.readBytes(length: c.readableBytes) {
                bodyData.append(contentsOf: bytes)
            }
        case .end:
            handleRequest(context: context)
        }
    }

    func handleRequest(context: ChannelHandlerContext) {
    let requestString = String(data: bodyData, encoding: .utf8) ?? ""
    // Expected body: plain text to hash
    let hashed = requestString.bytes.sha256().toHexString()
        var headers = HTTPHeaders()
        headers.add(name: "Content-Type", value: "application/json")
        let json = "{\"ok\":true,\"sha256\":\"\(hashed)\"}"
        var buffer = context.channel.allocator.buffer(capacity: json.utf8.count)
        buffer.writeString(json)
        let head = HTTPResponseHead(version: .http1_1, status: .ok, headers: headers)
        context.write(self.wrapOutboundOut(.head(head)), promise: nil)
        context.write(self.wrapOutboundOut(.body(.byteBuffer(buffer))), promise: nil)
        context.writeAndFlush(self.wrapOutboundOut(.end(nil)), promise: nil)
    }
}

let group = MultiThreadedEventLoopGroup(numberOfThreads: System.coreCount)
let bootstrap = ServerBootstrap(group: group)
    .serverChannelOption(ChannelOptions.backlog, value: 256)
    .serverChannelOption(ChannelOptions.socketOption(.so_reuseaddr), value: 1)
    .childChannelInitializer { channel in
        channel.pipeline.configureHTTPServerPipeline().flatMap {
            channel.pipeline.addHandler(HTTPHandler())
        }
    }
    .childChannelOption(ChannelOptions.socketOption(.so_reuseaddr), value: 1)

let host = ProcessInfo.processInfo.environment["SWIFT_TOOLS_HOST"] ?? "0.0.0.0"
let portString = ProcessInfo.processInfo.environment["SWIFT_TOOLS_PORT"] ?? "8085"
let port = Int(portString) ?? 8085

do {
    let channel = try bootstrap.bind(host: host, port: port).wait()
    print("SwiftTools running on \(host):\(port)")
    try channel.closeFuture.wait()
} catch {
    fputs("Failed to start SwiftTools: \(error)\n", stderr)
}
