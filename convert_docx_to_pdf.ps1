param(
    [string]$docxPath,
    [string]$pdfPath
)

$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open($docxPath)
    # 17 = wdFormatPDF
    $doc.SaveAs([ref]$pdfPath, [ref]17)
    Write-Host "Successfully converted $docxPath to $pdfPath"
    $doc.Close([ref]0)
}
catch {
    Write-Host "Conversion error: $_"
}
finally {
    $word.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
