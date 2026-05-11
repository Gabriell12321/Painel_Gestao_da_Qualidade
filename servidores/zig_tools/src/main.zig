const std = @import("std");

pub fn main() !void {
    var gpa = std.heap.GeneralPurposeAllocator(.{}){};
    defer _ = gpa.deinit();
    const allocator = gpa.allocator();

    var listener = std.net.StreamServer.init(.{});
    defer listener.deinit();

    const host_env = std.process.getEnvVarOwned(allocator, "ZIG_TOOLS_HOST") catch allocator.dupe(u8, "0.0.0.0") catch return;
    defer allocator.free(host_env);
    const port_env = std.process.getEnvVarOwned(allocator, "ZIG_TOOLS_PORT") catch allocator.dupe(u8, "8090") catch return;
    defer allocator.free(port_env);

    const port = std.fmt.parseInt(u16, port_env, 10) catch 8090;
    const address = try std.net.Address.parseIp(host_env, port);
    try listener.listen(address);

    const xxh3 = std.hash.XxHash3(64, .{});

    while (true) {
        var conn = try listener.accept();
        handleConn(allocator, &conn, xxh3) catch |e| {
            std.debug.print("conn error: {s}\n", .{@errorName(e)});
        };
    }
}

fn handleConn(allocator: std.mem.Allocator, conn: *std.net.StreamServer.Connection, comptime Hasher: type) !void {
    defer conn.stream.close();
    var reader = conn.stream.reader();
    var writer = conn.stream.writer();

    var req_buf: [8192]u8 = undefined;
    const n = try reader.read(&req_buf);
    const req = req_buf[0..n];

    var method: []const u8 = "GET";
    var path: []const u8 = "/";
    if (std.mem.indexOf(u8, req, " ")) |i| {
        const rest = req[i+1..];
        if (std.mem.indexOf(u8, rest, " ")) |j| {
            method = req[0..i];
            path = rest[0..j];
        }
    }

    if (std.mem.startsWith(u8, path, "/health")) {
        try writer.print("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 12\r\n\r\n{{\"ok\":true}}", .{});
        return;
    }

    if (std.mem.startsWith(u8, path, "/xxh3")) {
        // Expect raw body (POST) and return hex digest
        var body: []const u8 = "";
        if (std.mem.eql(u8, method, "POST")) {
            // crude split: find empty line \r\n\r\n
            if (std.mem.indexOf(u8, req, "\r\n\r\n")) |k| {
                body = req[k+4..];
            }
        }
        var hasher = Hasher.init(0);
        hasher.update(body);
        const digest = hasher.final();
        var hex: [16]u8 = undefined; // 64-bit -> 8 bytes -> 16 hex chars
        _ = std.fmt.bytesToHex(std.mem.asBytes(&digest), &hex, .lower);
        const payload = try std.fmt.allocPrint(allocator, "{{\"ok\":true,\"xxh3\":\"{s}\"}}", .{hex});
        defer allocator.free(payload);
        try writer.print("HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {d}\r\n\r\n{s}", .{payload.len, payload});
        return;
    }

    try writer.print("HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n", .{});
}
