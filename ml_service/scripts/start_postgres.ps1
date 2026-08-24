param(
    [string]$ContainerName = "antifraud-postgres",
    [string]$Image = "postgres:16-alpine",
    [int]$Port = 5432,
    [string]$Database = "antifraud",
    [string]$Username = "postgres",
    [string]$Password = "antifraud2026",
    [string]$DataDir = "D:/Desktop/postgres_data"
)

$running = docker ps --filter "name=$ContainerName" --format "{{.Names}}" 2>&1
if ($running -eq $ContainerName) {
    Write-Host "PostgreSQL 已在运行: postgresql://$Username@localhost:$Port/$Database"
    exit 0
}

$exists = docker ps -a --filter "name=$ContainerName" --format "{{.Names}}" 2>&1
if ($exists -eq $ContainerName) {
    Write-Host "重启已有 PostgreSQL 容器..."
    docker start $ContainerName | Out-Null
} else {
    if (-not (Test-Path $DataDir)) {
        New-Item -ItemType Directory -Path $DataDir | Out-Null
    }
    Write-Host "创建并启动 PostgreSQL 容器..."
    docker run -d `
        --name $ContainerName `
        -e POSTGRES_DB=$Database `
        -e POSTGRES_USER=$Username `
        -e POSTGRES_PASSWORD=$Password `
        -p ${Port}:5432 `
        -v "${DataDir}:/var/lib/postgresql/data" `
        $Image | Out-Null
}

Write-Host "等待 PostgreSQL 启动..."
$maxWait = 30
$waited = 0
while ($waited -lt $maxWait) {
    Start-Sleep -Seconds 2
    $waited += 2
    $probe = docker exec $ContainerName pg_isready -U $Username -d $Database 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "PostgreSQL 已就绪"
        Write-Host "  DSN: postgresql://$Username`:$Password@localhost:$Port/$Database"
        break
    }
    Write-Host "  等待中... ${waited}s"
}
