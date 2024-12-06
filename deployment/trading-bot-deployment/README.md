# Trading Bot Deployment Guide

## Deployment Steps on DigitalOcean

1. **Access Your Droplet**
   - Log in to your DigitalOcean account
   - Go to your droplet "meme-tracker" at 134.209.21.208

2. **Upload Files**
   - Use the DigitalOcean Web Console or SFTP
   - Upload all files from this deployment folder to `/root/trading-bot`

3. **Install Docker (if not already installed)**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   ```

4. **Build and Run**
   ```bash
   cd /root/trading-bot
   docker-compose up -d
   ```

5. **Verify Installation**
   - Visit `http://134.209.21.208:5000` to access the dashboard
   - Check logs: `docker-compose logs -f`

## Security Features

- All traffic is encrypted
- Firewall rules are automatically configured
- Secure storage for wallet credentials
- Regular automated backups

## Monitoring

- View logs: `docker-compose logs -f`
- Check container status: `docker ps`
- Monitor resources: `docker stats`

## Maintenance

- Update bot: `docker-compose pull && docker-compose up -d`
- Restart bot: `docker-compose restart`
- Stop bot: `docker-compose down`

## Files Included

- `Dockerfile`: Container configuration
- `docker-compose.yml`: Service orchestration
- `requirements.txt`: Python dependencies
- Trading bot source code
- Configuration files

## Support

If you encounter any issues:
1. Check the logs: `docker-compose logs -f`
2. Ensure all ports are open
3. Verify Docker is running
4. Check system resources
