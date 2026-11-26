param([int]$Port = 8086)

$Root = $PSScriptRoot
$Listener = New-Object System.Net.HttpListener
$Listener.Prefixes.Add("http://127.0.0.1:$Port/")
$Listener.Start()
Write-Output "MEDUSA-X serving at http://127.0.0.1:$Port/"

$MimeTypes = @{
  ".html" = "text/html; charset=utf-8"
  ".css"  = "text/css; charset=utf-8"
  ".js"   = "application/javascript; charset=utf-8"
  ".json" = "application/json; charset=utf-8"
  ".svg"  = "image/svg+xml"
  ".png"  = "image/png"
}

try {
  while ($Listener.IsListening) {
    $Context = $Listener.GetContext()
    $ReqPath = $Context.Request.Url.AbsolutePath.TrimStart("/")
    if ([string]::IsNullOrEmpty($ReqPath)) { $ReqPath = "index.html" }
    $FilePath = Join-Path $Root $ReqPath

    if ((Test-Path $FilePath) -and -not (Get-Item $FilePath).PSIsContainer) {
      $Ext = [System.IO.Path]::GetExtension($FilePath).ToLower()
      $Context.Response.ContentType = if ($MimeTypes.ContainsKey($Ext)) { $MimeTypes[$Ext] } else { "application/octet-stream" }
      $Bytes = [System.IO.File]::ReadAllBytes($FilePath)
      $Context.Response.ContentLength64 = $Bytes.Length
      $Context.Response.OutputStream.Write($Bytes, 0, $Bytes.Length)
    } else {
      $Context.Response.StatusCode = 404
    }
    $Context.Response.Close()
  }
} finally {
  $Listener.Stop()
}
