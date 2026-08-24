# 启动 Neo4j 容器（挂载本地数据目录）
# 用法：在项目根目录执行 .\scripts\start_neo4j.ps1
# Neo4j Browser: http://localhost:7474  用户名: neo4j  密码: antifraud2026
# Bolt 连接:     bolt://localhost:7687

$DATA_DIR = "D:/Desktop/neo4j_data"
$CYPHER_DIR = "$PSScriptRoot/../knowledge_graph/cypher_scripts"
$CONTAINER_NAME = "antifraud-neo4j"
$IMAGE = "neo4j:5.26.0-community"

# 检查容器是否已在运行
$running = docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}" 2>&1
if ($running -eq $CONTAINER_NAME) {
    Write-Host "Neo4j 已在运行: http://localhost:7474"
    exit 0
}

# 检查容器是否存在但已停止
$exists = docker ps -a --filter "name=$CONTAINER_NAME" --format "{{.Names}}" 2>&1
if ($exists -eq $CONTAINER_NAME) {
    Write-Host "重启已有容器..."
    docker start $CONTAINER_NAME
} else {
    Write-Host "创建并启动 Neo4j 容器..."
    docker run -d `
        --name $CONTAINER_NAME `
        -p 7474:7474 -p 7687:7687 `
        -v "${DATA_DIR}:/data" `
        -v "${CYPHER_DIR}:/cypher" `
        -e NEO4J_AUTH=neo4j/antifraud2026 `
        $IMAGE
}

# 等待启动
Write-Host "等待 Neo4j 启动..."
$maxWait = 30
$waited = 0
while ($waited -lt $maxWait) {
    Start-Sleep -Seconds 3
    $waited += 3
    $log = docker logs $CONTAINER_NAME 2>&1 | Select-String "Started"
    if ($log) {
        Write-Host "Neo4j 已就绪"
        Write-Host "  Browser: http://localhost:7474"
        Write-Host "  Bolt:    bolt://localhost:7687"
        Write-Host "  用户名:  neo4j"
        Write-Host "  密码:    antifraud2026"
        break
    }
    Write-Host "  等待中... ${waited}s"
}
