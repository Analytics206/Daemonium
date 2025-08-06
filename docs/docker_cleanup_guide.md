# Docker Cleanup Commands Guide

This guide provides essential Docker cleanup commands with detailed explanations of what they delete and when to use them.

## Container Cleanup

### Remove stopped containers
```bash
docker container prune
```
- **Deletes:** All stopped containers
- **Use case:** Regular maintenance to free up disk space from containers that have exited
- **Safe:** Yes, only affects stopped containers

### Remove all containers (including running)
```bash
docker rm -f $(docker ps -aq)
```
- **Deletes:** All containers (stops running ones first)
- **Use case:** Complete reset of container environment
- **Caution:** Will terminate running applications

## Image Cleanup

### Remove unused images
```bash
docker image prune
```
- **Deletes:** Dangling images (untagged images not referenced by containers)
- **Use case:** Clean up intermediate build layers and orphaned images
- **Safe:** Yes, keeps images used by existing containers

### Remove all unused images
```bash
docker image prune -a
```
- **Deletes:** All images not currently used by running containers
- **Use case:** Aggressive cleanup when you want to reclaim maximum space
- **Caution:** Will require re-downloading images for stopped containers

### Remove specific images
```bash
docker rmi image_name:tag
# or
docker rmi $(docker images -q "pattern")
```

## Volume Cleanup

### Remove unused volumes
```bash
docker volume prune
```
- **Deletes:** Volumes not attached to any container
- **Use case:** Clean up orphaned data volumes
- **Caution:** Permanent data loss - backup important data first

### Remove all volumes
```bash
docker volume rm $(docker volume ls -q)
```
- **Deletes:** All volumes (stops containers using them first)
- **Use case:** Complete data reset
- **High Risk:** All persistent data will be lost

## Network Cleanup

### Remove unused networks
```bash
docker network prune
```
- **Deletes:** Custom networks not used by containers
- **Use case:** Clean up unused custom networks
- **Safe:** Keeps default networks (bridge, host, none)

## Comprehensive Cleanup

### Remove everything unused
```bash
docker system prune
```
- **Deletes:** Stopped containers, dangling images, unused networks
- **Use case:** General maintenance cleanup
- **Safe:** Preserves running containers and their images

### Aggressive system cleanup
```bash
docker system prune -a --volumes
```
- **Deletes:** All stopped containers, all unused images, all unused networks, all unused volumes
- **Use case:** Maximum space reclamation
- **High Risk:** Removes all unused Docker objects

## Build Cache Cleanup

### Remove build cache
```bash
docker builder prune
```
- **Deletes:** Build cache from Docker BuildKit
- **Use case:** Free up space from Docker builds
- **Safe:** Only affects build performance, not running containers

## Selective Cleanup Examples

### Remove containers older than 24 hours
```bash
docker container prune --filter "until=24h"
```

### Remove images from specific repository
```bash
docker images | grep "repo_name" | awk '{print $3}' | xargs docker rmi
```

### Check space usage before cleanup
```bash
docker system df
```

### Optimize-VHD

1. Open PowerShell as an administrator.
2. Run the following command:
```bash
wsl --shutdown
```
3. Navigate to the directory containing the ext4.vhdx file.
```bash
cd "C:\Users\%USERNAME%\AppData\Local\Docker\wsl"
```
4. Run the following Powershell command:
```bash
Optimize-VHD -Path .\ext4.vhdx -Mode full
```

## Best Practices

### 1. Always check what will be deleted
```bash
docker system prune --dry-run
```

### 2. Backup important volumes before cleanup
```bash
docker run --rm -v volume_name:/data -v $(pwd):/backup alpine tar czf /backup/backup.tar.gz /data
```

### 3. Use filters for selective cleanup
```bash
docker container prune --filter "label!=keep"
```

### 4. Regular maintenance schedule
- **Weekly:** `docker system prune`
- **Monthly:** `docker system prune -a`
- **As needed:** `docker volume prune` (with caution)

## Windows Docker Desktop Space Reclaim

### The Problem
Docker Desktop on Windows uses a virtual disk file (`ext4.vhdx`) that doesn't automatically shrink when you delete Docker objects. You need to manually reclaim the space.

### Solution 1: Docker Desktop GUI (Easiest)
1. Open Docker Desktop
2. Go to **Settings** → **Resources** → **Advanced**
3. Click **"Disk image size"** section
4. Click **"Reset to factory defaults"** or use the **"Clean / Purge data"** option
5. This will recreate the virtual disk at a smaller size

### Solution 2: WSL2 Compact Command
If using WSL2 backend:
```bash
# Stop Docker Desktop first
wsl --shutdown

# Compact the virtual disk
diskpart
select vdisk file="C:\Users\%USERNAME%\AppData\Local\Docker\wsl\data\ext4.vhdx"
compact vdisk
exit
```
**Note:** Adjust the path if Docker is installed elsewhere.

### Solution 3: PowerShell Script
```powershell
# Stop Docker Desktop
Stop-Process -Name "Docker Desktop" -Force -ErrorAction SilentlyContinue

# Shutdown WSL
wsl --shutdown

# Compact the disk
$vhdxPath = "$env:LOCALAPPDATA\Docker\wsl\data\ext4.vhdx"
if (Test-Path $vhdxPath) {
    Optimize-VHD -Path $vhdxPath -Mode Full
}

# Restart Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

### Prevention: Enable Automatic Cleanup
In Docker Desktop Settings:
1. Go to **General**
2. Enable **"Use the WSL 2 based engine"** (if not already)
3. Go to **Resources** → **Advanced**
4. Consider enabling periodic cleanup scripts

## ⚠️ Important Warning

The key is understanding that Docker cleanup is permanent - always verify what you're deleting matches your intentions, especially with volumes containing application data.

## Quick Reference

| Command | Risk Level | What it removes |
|---------|------------|-----------------|
| `docker container prune` | Low | Stopped containers only |
| `docker image prune` | Low | Dangling images only |
| `docker image prune -a` | Medium | All unused images |
| `docker volume prune` | High | Unused volumes (data loss) |
| `docker system prune` | Low-Medium | Containers, dangling images, networks |
| `docker system prune -a --volumes` | High | Everything unused (max cleanup) |