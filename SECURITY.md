# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          | Status |
| ------- | ------------------ | ------ |
| 0.15.x  | :white_check_mark: | Latest stable |
| 0.14.x  | :x:                | End of life |
| < 0.14  | :x:                | End of life |

## Reporting a Vulnerability

If you discover a security vulnerability in JsonAI, please report it to us as follows:

### Contact
- **Email**: security@jsonai.dev
- **Response Time**: We will acknowledge receipt within 48 hours
- **Updates**: We'll provide regular updates on our progress

### What to Include
- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Any suggested fixes (optional)

### Our Process
1. **Acknowledgment**: We'll confirm receipt within 48 hours
2. **Investigation**: We'll investigate and validate the report
3. **Fix Development**: We'll develop and test a fix
4. **Disclosure**: We'll coordinate disclosure with you
5. **Release**: We'll release the fix and security advisory

## Security Considerations

### API Keys and Credentials
- Never commit API keys to version control
- Use environment variables for sensitive configuration
- Rotate keys regularly

### Data Privacy
- JsonAI processes user-provided schemas and prompts
- Generated data may contain sensitive information
- Implement proper access controls in production deployments

### Network Security
- Use HTTPS for API communications
- Implement rate limiting
- Validate all inputs to prevent injection attacks

### Model Security
- Be aware of potential biases in LLM outputs
- Validate generated data against your schemas
- Monitor for unexpected or malicious outputs

## Responsible AI

JsonAI is committed to responsible AI development:
- Transparency in model usage and limitations
- Bias detection and mitigation
- Privacy-preserving data handling
- Ethical use guidelines
