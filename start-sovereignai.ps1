$backendOut = "e:\soverign_ai\backend\backend.log"
$backendErr = "e:\soverign_ai\backend\backend.err"
$frontendOut = "e:\soverign_ai\frontend\frontend.log"
$frontendErr = "e:\soverign_ai\frontend\frontend.err"

$backendProcess = Start-Process `
  -FilePath "powershell" `
  -ArgumentList "-NoExit","-Command","Set-Location 'e:\soverign_ai\backend'; python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload" `
  -RedirectStandardOutput $backendOut `
  -RedirectStandardError $backendErr `
  -PassThru

$frontendProcess = Start-Process `
  -FilePath "powershell" `
  -ArgumentList "-NoExit","-Command","Set-Location 'e:\soverign_ai\frontend'; npm run dev -- --host 127.0.0.1 --port 4173" `
  -RedirectStandardOutput $frontendOut `
  -RedirectStandardError $frontendErr `
  -PassThru

Write-Output "Backend PID: $($backendProcess.Id)"
Write-Output "Frontend PID: $($frontendProcess.Id)"
Write-Output "Backend stdout: $backendOut"
Write-Output "Backend stderr: $backendErr"
Write-Output "Frontend stdout: $frontendOut"
Write-Output "Frontend stderr: $frontendErr"
Write-Output "Open: http://127.0.0.1:4173"
Write-Output "API: http://127.0.0.1:8000/api/status"
