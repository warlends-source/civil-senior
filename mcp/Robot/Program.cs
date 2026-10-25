using CivilSenior.Mcp.Robot;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

// MCP server for Autodesk Robot Structural Analysis 2027 (stdio). stdout carries the protocol: log to stderr only.
var builder = Host.CreateApplicationBuilder(args);
builder.Logging.AddConsole(o => o.LogToStandardErrorThreshold = LogLevel.Trace);
builder.Services.AddSingleton<RobotSession>();
builder.Services
    .AddMcpServer(o => o.ServerInfo = new() { Name = "civilsenior-robot", Version = "1.0.0" })
    .WithStdioServerTransport()
    .WithToolsFromAssembly();
await builder.Build().RunAsync();
