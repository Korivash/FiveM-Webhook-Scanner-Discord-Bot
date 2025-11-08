# Contributing to FiveM Webhook Manager

Thanks for your interest in contributing! Here's how you can help improve this project.

## Code Style

### Python Standards
- Follow PEP 8 style guidelines
- Use type hints where possible
- Keep functions focused and single-purpose
- Write self-documenting code with clear variable names

### Comments
- **Don't** add inline comments explaining what code does
- **Do** add comments explaining why non-obvious decisions were made
- **Do** maintain docstrings for classes and functions
- Keep section dividers for code organization

### Example
```python
# ❌ Bad - Over-commented
async def scan(self):
    # Get all files to scan
    files = list(self._get_files())
    
    # Loop through each file
    for file in files:
        # Scan the file
        self._scan_file(file)

# ✅ Good - Self-documenting
async def scan(self):
    files = list(self._get_files())
    for file in files:
        self._scan_file(file)
```

## Making Changes

### 1. Fork & Clone
```bash
git clone https://github.com/yourusername/fivem-webhook-manager.git
cd fivem-webhook-manager
```

### 2. Create Branch
```bash
git checkout -b feature/your-feature-name
```

### 3. Make Changes
- Write clean, commented code
- Test thoroughly
- Update documentation if needed

### 4. Test
```bash
# Set up test environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Test your changes
python fivem_webhook_manager.py
```

### 5. Commit
```bash
git add .
git commit -m "feat: add your feature description"
```

Use conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `style:` - Code style changes
- `refactor:` - Code refactoring
- `test:` - Tests
- `chore:` - Maintenance

### 6. Push & PR
```bash
git push origin feature/your-feature-name
```
Then create a Pull Request on GitHub.

## What to Contribute

### High Priority
- Bug fixes
- Performance improvements
- Better error handling
- Additional file type support

### Medium Priority
- UI/UX improvements
- Additional commands
- Better logging

### Low Priority
- Documentation improvements
- Code style consistency
- Additional examples

## Testing Checklist

Before submitting:
- [ ] Code runs without errors
- [ ] New features work as expected
- [ ] Existing features still work
- [ ] Documentation updated
- [ ] No excessive comments added
- [ ] Follows project style

## Need Help?

- Check existing issues
- Review documentation
- Test on a development server first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
