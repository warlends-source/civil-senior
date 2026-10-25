# Renderiza paginas de um PDF para PNG usando o renderizador nativo do Windows (sem instalar nada).
# Uso (Windows PowerShell 5.1):  powershell -File pdf_para_png.ps1 -Pdf arquivo.pdf -Saida pasta -Paginas '1,2,3' [-Largura 1100]
param([Parameter(Mandatory=$true)][string]$Pdf, [Parameter(Mandatory=$true)][string]$Saida,
      [string]$Paginas = '1', [int]$Largura = 1100)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime]
$null = [Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType=WindowsRuntime]
$null = [Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Storage.Streams, ContentType=WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$t) { $m = $asTask.MakeGenericMethod($t); $task = $m.Invoke($null, @($op)); $task.Wait(-1) | Out-Null; $task.Result }
$awaitAction = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction' })[0]
function AwaitAction($op) { $task = $awaitAction.Invoke($null, @($op)); $task.Wait(-1) | Out-Null }
New-Item -ItemType Directory -Force -Path $Saida | Out-Null
$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync((Resolve-Path $Pdf).Path)) ([Windows.Storage.StorageFile])
$doc = Await ([Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($file)) ([Windows.Data.Pdf.PdfDocument])
"paginas no PDF: " + $doc.PageCount
foreach ($n in ($Paginas -split '[,; ]+' | Where-Object { $_ } | ForEach-Object { [int]$_ })) {
    if ($n -lt 1 -or $n -gt $doc.PageCount) { continue }
    $page = $doc.GetPage($n - 1)
    $ms = New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
    $opt = New-Object Windows.Data.Pdf.PdfPageRenderOptions
    $opt.DestinationWidth = $Largura
    AwaitAction ($page.RenderToStreamAsync($ms, $opt))
    $out = Join-Path (Resolve-Path $Saida).Path ("pagina_{0:D2}.png" -f $n)
    $stream = [System.IO.WindowsRuntimeStreamExtensions]::AsStreamForRead($ms.GetInputStreamAt(0))
    $fs = [System.IO.File]::Create($out); $stream.CopyTo($fs); $fs.Close(); $stream.Close(); $page.Dispose()
    $out
}
