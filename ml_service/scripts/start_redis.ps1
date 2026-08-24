param(
    [string]$ContainerName = "antifraud-redis",
    [string]$Image = "redis:7-alpine",
    [int]$Port = 6379
)

$exists = docker ps -a --format "{{.Names}}" | Select-String -Pattern "^$ContainerName$"
if (-not $exists) {
    docker run -d --name $ContainerName -p ${Port}:6379 $Image | Out-Null
    Write-Host "已创建并启动 Redis 容器: $ContainerName"
} else {
    docker start $ContainerName | Out-Null
    Write-Host "已启动现有 Redis 容器: $ContainerName"
}
