# Deployment Guide for Clinical Trials MCP Server

## Overview

This guide covers deploying the Clinical Trials MCP Server to various platforms including Smithery, PyPI, and manual installations.

## Files for Deployment

The following files are created for deployment:

- `clinicaltrials.dxt` - DXT extension file for Smithery
- `package.json` - NPM/Node.js metadata
- `setup.py` - Python package setup
- `MANIFEST.in` - Package manifest
- `install.sh` - Unix/Linux installation script
- `install.bat` - Windows installation script
- `bin/clintrials-mcp` - Executable script

## Smithery Deployment

### 1. DXT File

The `clinicaltrials.dxt` file contains all metadata needed for Smithery deployment:

```json
{
  "name": "clinicaltrials",
  "version": "1.0.0", 
  "description": "Access and analyze clinical trials data from ClinicalTrials.gov",
  "mcp": {
    "server": {
      "command": "python",
      "args": ["-m", "clintrials_mcp.server"]
    }
  }
}
```

### 2. Submit to Smithery

1. **Create GitHub Repository**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/clintrials-mcp.git
   git push -u origin main
   ```

2. **Submit to Smithery**:
   - Go to [Smithery](https://smithery.ai)
   - Submit your repository URL
   - Smithery will automatically detect the `clinicaltrials.dxt` file

### 3. Installation via Smithery

Users can install via:
```bash
smithery install clinicaltrials
```

## PyPI Deployment

### 1. Prepare for PyPI

Build the package:
```bash
python setup.py sdist bdist_wheel
```

### 2. Upload to PyPI

```bash
pip install twine
twine upload dist/*
```

### 3. Installation via PyPI

Users can install via:
```bash
pip install clintrials-mcp
```

## Manual Installation

### Unix/Linux/macOS

```bash
chmod +x install.sh
./install.sh
```

### Windows

```batch
install.bat
```

## Configuration

### Claude Desktop Configuration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "clinicaltrials": {
      "command": "python",  
      "args": ["path/to/mcp_server.py"],
      "env": {}
    }
  }
}
```

### Continue IDE Configuration

Add to Continue configuration:

```json
{
  "mcpServers": {
    "clinicaltrials": {
      "command": "python",
      "args": ["path/to/mcp_server.py"]
    }
  }
}
```

## Server URL for Installation

For direct installation via URL, users can use:

```bash
# Via curl
curl -sSL https://raw.githubusercontent.com/yourusername/clintrials-mcp/main/install.sh | bash

# Via wget  
wget -qO- https://raw.githubusercontent.com/yourusername/clintrials-mcp/main/install.sh | bash
```

## Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "mcp_server.py"]
```

Build and run:
```bash
docker build -t clintrials-mcp .
docker run -p 8000:8000 clintrials-mcp
```

## Vercel/Serverless Deployment

For serverless deployment, create `vercel.json`:

```json
{
  "functions": {
    "api/server.py": {
      "runtime": "python3.9"
    }
  }
}
```

## Environment Variables

The server supports these optional environment variables:

- `CLINTRIALS_MCP_PORT` - Port to run on (default: auto-detect)
- `CLINTRIALS_MCP_DEBUG` - Enable debug logging
- `CLINTRIALS_API_TIMEOUT` - API request timeout in seconds

## Monitoring and Logging

### Health Check Endpoint

The server provides a health check endpoint:

```bash
curl http://localhost:8000/health
```

### Logging

Logs are written to stdout/stderr and can be configured via environment variables.

## Security Considerations

- The server only makes requests to the public ClinicalTrials.gov API
- No API keys or authentication required
- No personal data is stored or transmitted
- All queries are read-only

## Performance Optimization

- Implements request session reuse
- Respects API rate limits
- Supports pagination for large result sets
- Caches API responses where appropriate

## Troubleshooting

### Common Issues

1. **Python Version**: Requires Python 3.8+
2. **Dependencies**: Install via `pip install -r requirements.txt`
3. **Permissions**: Ensure execute permissions on scripts
4. **Network**: Requires internet access to ClinicalTrials.gov API

### Debug Mode

Run with debug logging:
```bash
CLINTRIALS_MCP_DEBUG=1 python mcp_server.py
```

## Support

- GitHub Issues: https://github.com/yourusername/clintrials-mcp/issues
- Documentation: README.md
- API Reference: ClinicalTrials.gov API documentation